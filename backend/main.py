import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
# Core shared schemas and database
from core.models import (
    DiagnosticRequest, 
    Agent1Payload, 
    VehicleDetails, 
    DiagnosticResult,
    SpellcheckRequest,
    DTCCascadeRequest,
    DTCCascadeAnalysis,
    RepairRequest,
    ProcurementRequest, 
    ProcurementResponse
)

# Agent 1 - Ingestion, Validation, IR & Cascade
from agents.agent1_ingestion import (
    extract_entities, 
    sanitize_input, 
    extract_dtc_codes, 
    extract_damaged_parts, 
    extract_vin,
    normalize_mechanic_notes, 
    resolve_dtc_hierarchy,
    classify_dtc_cascades,
    fuzzy_correct_make,
    fuzzy_correct_model,
    nlp,
    verify_vehicle,
    decode_vin_nhtsa,
    validate_vin_checksum
)

# Agent 2 - Cognitive Diagnostic Reasoning
try:
    import groq
    from agents.agent2_reasoning import deduce_root_cause
except Exception as e:
    groq = None
    deduce_root_cause = None

# Agent 3 - Retrieval-Augmented Generation (OEM Manuals)
try:
    from agents.agent3_rag import get_repair_procedure
except Exception as e:
    get_repair_procedure = None

# Agent 4 - Procurement & Pricing
try:
    from agents.agent4_procurement import get_procurement_quote
except Exception as e:
    get_procurement_quote = None

app = FastAPI(
    title="Auto-Triage AI System",
    description="Multi-Agent Diagnostic Platform: Agent 1 (Ingestion & Vehicle Validation) and Agent 2 (Diagnostic Reasoning)",
    version="1.0.0",
)

# Configure CORS for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev / React frontend integration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    return {
        "service": "Auto-Triage AI System",
        "agents": {
            "agent_1": "Ingestion & Vehicle Validation Gateway",
            "agent_2": "Diagnostic Reasoning Service"
        },
        "endpoints": {
            "ingest": "/api/v1/ingest",
            "diagnose": "/api/v1/diagnose",
            "docs": "/docs"
        },
        "status": "online"
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "agent_1": "online",
        "agent_2": "online" if deduce_root_cause is not None else "degraded (dependencies missing)"
    }


@app.post(
    "/api/v1/ingest",
    response_model=Agent1Payload,
    status_code=status.HTTP_200_OK,
    tags=["Agent 1 - Ingestion & Validation"]
)
async def ingest_diagnostic(request: DiagnosticRequest):
    """
    Primary gateway endpoint for Agent 1.
    Supports Dual Mode:
    - Mode A (Manual Spec Entry): Technician supplies explicit Make, Model, Year, DTCs.
    - Mode B (Smart NLP Intake): AI parses natural language complaint for all entities.
    
    Both modes validate against the official US DOT NHTSA vPIC database and format
    an Agent-to-Agent (A2A) payload ready for Agent 2.
    """
    # Initialize extended VIN metadata and fuzzy typo corrections
    vin = (request.vin or "").strip().upper() if request.vin else None
    vin_data = None
    fuzzy_corrections: List[Dict[str, Any]] = []

    # Check Mode 1: Direct VIN Intake Mode
    if vin:
        vin_res = await decode_vin_nhtsa(vin)
        if not vin_res.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"VIN decoding failed for '{vin}': {vin_res.get('error')}"
            )
        make = vin_res["make"]
        model = vin_res["model"]
        year = vin_res["year"]
        vin_data = vin_res

        dtc_codes = list(request.dtc_codes or [])
        damaged_parts = list(request.damaged_parts or [])

        if request.raw_text and request.raw_text.strip():
            clean_text = sanitize_input(request.raw_text)
            for code in extract_dtc_codes(clean_text):
                if code not in dtc_codes:
                    dtc_codes.append(code)
            doc = nlp(clean_text) if nlp is not None else clean_text
            for part in extract_damaged_parts(doc):
                if part not in damaged_parts:
                    damaged_parts.append(part)

    # Check Mode 2: Manual Spec Entry Mode (explicit make, model, year)
    elif request.make and request.model and request.year:
        raw_make = request.make.strip()
        raw_model = request.model.strip()
        year = int(request.year)

        # Apply RapidFuzz approximate string matching to tolerate typos in user input
        make, make_corr = fuzzy_correct_make(raw_make)
        model, model_corr = fuzzy_correct_model(raw_model)

        if make_corr:
            fuzzy_corrections.append(make_corr)
        if model_corr:
            fuzzy_corrections.append(model_corr)
        
        # Combine provided DTC codes and any found in raw_text
        dtc_codes = list(request.dtc_codes or [])
        damaged_parts = list(request.damaged_parts or [])
        
        if request.raw_text and request.raw_text.strip():
            clean_text = sanitize_input(request.raw_text)
            extra_dtcs = extract_dtc_codes(clean_text)
            for code in extra_dtcs:
                if code not in dtc_codes:
                    dtc_codes.append(code)
                    
            doc = nlp(clean_text) if nlp is not None else clean_text
            extra_parts = extract_damaged_parts(doc)
            for part in extra_parts:
                if part not in damaged_parts:
                    damaged_parts.append(part)
    else:
        # Mode 3: Smart NLP Intake Mode (extracts VIN, specs, DTCs from text)
        sanitized_text = sanitize_input(request.raw_text or "")
        extracted = extract_entities(sanitized_text)
        
        # If a 17-character VIN was discovered in the complaint notes, decode via NHTSA
        if extracted.get("vin"):
            vin = extracted["vin"]
            vin_res = await decode_vin_nhtsa(vin)
            if vin_res.get("success"):
                make = vin_res["make"]
                model = vin_res["model"]
                year = vin_res["year"]
                vin_data = vin_res
            else:
                make = extracted["make"]
                model = extracted["model"]
                year = extracted["year"]
        else:
            make = extracted["make"]
            model = extracted["model"]
            year = extracted["year"]

        dtc_codes = extracted["dtc_codes"]
        damaged_parts = extracted["damaged_parts"]
        fuzzy_corrections = extracted.get("fuzzy_corrections", [])

    # Validate against external official NHTSA vPIC database (unless already validated via VIN)
    if vin_data:
        is_valid = True
    else:
        is_valid = await verify_vehicle(make=make, model=model, year=year)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle configuration '{year} {make} {model}' was not found in the official US DOT NHTSA vPIC database."
        )

    # Compute Information Retrieval normalized query & DTC taxonomic hierarchy
    raw_user_note = request.raw_text or ""
    canonical_query = normalize_mechanic_notes(raw_user_note)
    dtc_hierarchy = resolve_dtc_hierarchy(dtc_codes)
    dtc_cascade = classify_dtc_cascades(dtc_codes)

    # Build detailed vehicle specifications
    vehicle_details = VehicleDetails(
        make=make,
        model=model,
        year=year,
        is_verified=True,
        vin=vin,
        engine=vin_data.get("engine_displacement_l") if vin_data else None,
        fuel_type=vin_data.get("fuel_type") if vin_data else None,
        drive_type=vin_data.get("drive_type") if vin_data else None,
        body_class=vin_data.get("body_class") if vin_data else None,
        vin_checksum_valid=vin_data.get("checksum", {}).get("is_valid") if vin_data else (validate_vin_checksum(vin)["is_valid"] if vin else None),
        fuzzy_corrections=fuzzy_corrections if fuzzy_corrections else None
    )

    # Assemble and return verified A2A payload for Agent 2
    return Agent1Payload(
        session_id=request.session_id,
        vehicle_details=vehicle_details,
        dtc_codes=dtc_codes,
        damaged_parts=damaged_parts,
        user_note=raw_user_note,
        canonical_query=canonical_query,
        dtc_hierarchy=dtc_hierarchy,
        dtc_cascade=dtc_cascade,
        fuzzy_corrections=fuzzy_corrections
    )


@app.post(
    "/api/v1/spellcheck-vehicle",
    tags=["Agent 1 - Ingestion & Validation"]
)
async def spellcheck_vehicle(data: SpellcheckRequest):
    """
    Dedicated Information Retrieval endpoint for approximate string matching & spell-checking of vehicle names.
    Calculates Levenshtein edit distance and RapidFuzz ratio similarity.
    """
    raw_make = (data.make or "").strip()
    raw_model = (data.model or "").strip()
    make, make_corr = fuzzy_correct_make(raw_make)
    model, model_corr = fuzzy_correct_model(raw_model)
    return {
        "original_make": raw_make,
        "corrected_make": make,
        "make_correction": make_corr,
        "original_model": raw_model,
        "corrected_model": model,
        "model_correction": model_corr
    }


@app.get(
    "/api/v1/vin/{vin}",
    tags=["Agent 1 - Ingestion & Validation"]
)
async def decode_vin_endpoint(vin: str):
    """
    Dedicated endpoint to decode and validate a 17-character ISO 3779 VIN:
    - Runs offline MOD-11 checksum validation
    - Queries official US DOT NHTSA vPIC API for full specifications
    """
    clean_vin = vin.strip().upper()
    checksum = validate_vin_checksum(clean_vin)
    decode_result = await decode_vin_nhtsa(clean_vin)
    return {
        "vin": clean_vin,
        "checksum": checksum,
        "decode": decode_result
    }


@app.post(
    "/api/v1/dtc-cascade",
    response_model=DTCCascadeAnalysis,
    tags=["Agent 1 - Ingestion & Validation"]
)
async def analyze_dtc_cascade(data: DTCCascadeRequest):
    """
    Dedicated endpoint for multi-DTC cascade and causal correlation analysis:
    - Isolates primary upstream root-cause trigger code
    - Detects downstream consequential symptoms (e.g. misfires from vacuum leak or bad MAF)
    - Maps causal propagation chains and provides master mechanic explanation
    """
    return classify_dtc_cascades(data.dtc_codes)


@app.post(
    "/api/v1/diagnose",
    response_model=DiagnosticResult,
    status_code=status.HTTP_200_OK,
    tags=["Agent 2 - Diagnostic Reasoning"]
)
async def run_diagnostics(payload: Agent1Payload):
    """
    Agent 2 Cognitive Diagnostic Reasoning endpoint.
    Processes verified vehicle specs, DTC codes, and mechanic notes through
    the LLM reasoning engine to deduce the root-cause failed component.
    """
    if deduce_root_cause is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent 2 reasoning engine is unavailable or missing required dependencies."
        )
    try:
        result = deduce_root_cause(payload)
        return result
    except Exception as e:
        if groq and hasattr(groq, "APIStatusError") and isinstance(e, groq.APIStatusError):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Groq API error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Diagnostic reasoning error: {e}")


@app.post(
    "/api/v1/procure",
    response_model=ProcurementResponse,
    status_code=status.HTTP_200_OK,
    tags=["Agent 4 - Procurement & Pricing"]
)
async def run_procurement(request: ProcurementRequest):
    """
    Agent 4 Procurement & Pricing endpoint.
    Resolves the root-cause component to a canonical catalog part, assembles the
    bill of materials, and prices it across quality tiers from the MongoDB parts
    catalog. All prices and part numbers originate from the database.

    An unknown part or an unlisted vehicle is a normal result, returned as a 200
    with a populated 'warnings' list - not an error.
    """
    if get_procurement_quote is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent 4 procurement engine is unavailable or missing required dependencies."
        )
    try:
        return get_procurement_quote(
            root_cause_component=request.root_cause_component,
            make=request.make,
            model=request.model,
            year=request.year,
            severity=request.severity,
            safety_warning=request.safety_warning,
        )
    except HTTPException:
        raise
    except Exception as e:
        if groq and hasattr(groq, "APIStatusError") and isinstance(e, groq.APIStatusError):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Groq API error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Procurement error: {e}")


@app.post("/api/v1/repair")
async def generate_repair_plan(request: RepairRequest):
    try:
        # Combine the vehicle info into a clean string
        full_vehicle_name = f"{request.vehicle_year} {request.vehicle_make} {request.vehicle_model}"
        
        # Call Agent 3 by explicitly passing BOTH required arguments
        repair_data = await get_repair_procedure(
            target_component=request.issue_summary, 
            vehicle_model=full_vehicle_name
        )
        
        return {"status": "success", "repair_plan": repair_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}