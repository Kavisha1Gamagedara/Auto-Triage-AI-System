import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status, Header, Depends
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
    FreezeFrameData,
    FreezeFrameAnalysis,
    RepairRequest,
    ProcurementRequest, 
    ProcurementResponse
)

# Role-Based Access Control & Subscriptions
from subscriptions import subscriptions_router, store, get_current_user_optional

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
    parse_freeze_frame_scanner_text,
    analyze_freeze_frame,
    nlp,
    verify_vehicle,
    decode_vin_nhtsa,
    validate_vin_checksum,
    extract_sri_lankan_plate,
    verify_plate_vehicle_compatibility,
    get_vehicle_history,
    record_vehicle_visit,
    get_fleet_store_status,
    lookup_jdm_chassis_specs
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

# Mount Subscription & Authentication Router
app.include_router(subscriptions_router, prefix="/api/v1")


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
            "subscriptions": "/api/v1/subscriptions/tiers",
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
async def ingest_diagnostic(
    request: DiagnosticRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Primary gateway endpoint for Agent 1 with Role-Based Access Control and Quota Enforcement.
    - Guest users: Rejected with HTTP 401 (must authenticate to diagnose).
    - Logged-in mechanics: Evaluated against daily/monthly subscription quotas.
    """
    # 1. Enforce Authentication Requirement (Guests can only view the app)
    user = await get_current_user_optional(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_REQUIRED",
                "message": "Guest users can view the platform but must log in to execute autonomous diagnosis."
            }
        )

    # 2. Enforce Subscription Quota Limits (Basic: 2/day, Plus: 300/mo, Pro: 600/mo, Ultra: Unlimited)
    quota = store.get_quota(user["id"])
    if not quota.can_diagnose:
        period_label = "today" if quota.period == "daily" else "this month"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "QUOTA_EXCEEDED",
                "tier": user["tier"],
                "limit": quota.limit,
                "used": quota.used,
                "period": quota.period,
                "message": f"Subscription limit reached ({quota.used}/{quota.limit} tries {period_label} for {user['tier'].capitalize()} tier). Please upgrade your subscription to continue diagnosing vehicles."
            }
        )

    # 3. Increment usage count for this diagnosis execution
    store.record_usage(user["id"])

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

    # OBD-II Mode $02 Freeze Frame Sensor Telemetry ingestion & empirical analysis
    freeze_frame = request.freeze_frame
    if not freeze_frame and request.raw_text:
        freeze_frame = parse_freeze_frame_scanner_text(request.raw_text)
    elif freeze_frame and freeze_frame.raw_scanner_text and freeze_frame.stft_pct is None:
        parsed_ff = parse_freeze_frame_scanner_text(freeze_frame.raw_scanner_text)
        if parsed_ff:
            freeze_frame = parsed_ff

    freeze_frame_analysis = None
    if freeze_frame:
        freeze_frame_analysis = analyze_freeze_frame(
            freeze_frame,
            dtc_codes=dtc_codes,
            vehicle={"make": make, "model": model, "year": year}
        )

    # 4. Sri Lankan Number Plate & JDM Chassis Code Ingestion
    sl_plate = None
    if request.plate_number:
        sl_plate = extract_sri_lankan_plate(request.plate_number)
    elif extracted.get("sl_plate"):
        sl_plate = extracted["sl_plate"]
    elif request.raw_text:
        sl_plate = extract_sri_lankan_plate(request.raw_text)

    jdm_specs = None
    if request.chassis_code:
        jdm_specs = lookup_jdm_chassis_specs(request.chassis_code)
    elif extracted.get("jdm_specs"):
        jdm_specs = extracted["jdm_specs"]
    elif request.raw_text:
        jdm_specs = lookup_jdm_chassis_specs(request.raw_text)

    # Check vehicle compatibility with statutory plate class
    plate_compatibility = None
    if sl_plate and sl_plate.get("is_valid"):
        plate_compatibility = verify_plate_vehicle_compatibility(sl_plate, make, model)

    # 5. Local Workshop Fleet Return-Visit History Lookup
    history_lookup_key = (sl_plate.get("plate_number") if sl_plate else None) or vin or (jdm_specs.get("model_code") if jdm_specs else None)
    fleet_history = None
    if history_lookup_key:
        fleet_history = get_vehicle_history(history_lookup_key)
        # Record this diagnostic visit into the local shop fleet store
        record_vehicle_visit(
            identifier=history_lookup_key,
            make=make,
            model=model,
            year=year,
            dtc_codes=dtc_codes,
            chassis_number=jdm_specs.get("model_code") if jdm_specs else None,
            technician_notes=raw_user_note
        )

    # Build detailed vehicle specifications
    vehicle_details = VehicleDetails(
        make=make,
        model=model,
        year=year,
        is_verified=True,
        vin=vin,
        engine=vin_data.get("engine_displacement_l") if vin_data else (jdm_specs.get("engine_displacement") if jdm_specs else None),
        fuel_type=vin_data.get("fuel_type") if vin_data else (jdm_specs.get("drivetrain") if jdm_specs else None),
        drive_type=vin_data.get("drive_type") if vin_data else (jdm_specs.get("transmission") if jdm_specs else None),
        body_class=vin_data.get("body_class") if vin_data else None,
        vin_checksum_valid=vin_data.get("checksum", {}).get("is_valid") if vin_data else (validate_vin_checksum(vin)["is_valid"] if vin else None),
        fuzzy_corrections=fuzzy_corrections if fuzzy_corrections else None,
        sl_plate=sl_plate,
        jdm_specs=jdm_specs,
        plate_compatibility=plate_compatibility,
        fleet_history=fleet_history
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
        fuzzy_corrections=fuzzy_corrections,
        freeze_frame=freeze_frame,
        freeze_frame_analysis=freeze_frame_analysis,
        sl_plate=sl_plate,
        jdm_specs=jdm_specs,
        plate_compatibility=plate_compatibility,
        fleet_history=fleet_history
    )


@app.post(
    "/api/v1/validate-plate",
    tags=["Agent 1 - Ingestion & Validation"]
)
async def api_validate_plate(data: Dict[str, str]):
    """
    Validates a Sri Lankan vehicle registration plate against statutory Motor Traffic Act rules.
    """
    plate_text = data.get("plate", "")
    res = extract_sri_lankan_plate(plate_text)
    if not res:
        return {"is_valid": False, "status_message": "Invalid or unrecognized Sri Lankan number plate format."}
    return res


@app.get(
    "/api/v1/fleet-history/{identifier}",
    tags=["Agent 1 - Ingestion & Validation"]
)
async def api_get_fleet_history(identifier: str):
    """
    Retrieves previous workshop return-visit diagnostic history for a plate or chassis number.
    """
    hist = get_vehicle_history(identifier)
    return hist or {"has_prior_history": False, "total_prior_visits": 0, "message": f"No previous workshop visits found for '{identifier}'"}


@app.get(
    "/api/v1/fleet-history-status",
    tags=["Agent 1 - Ingestion & Validation"]
)
async def api_get_fleet_history_status():
    """
    Returns the active operational mode (MongoDB Atlas vs Local JSON Fallback) of the Fleet History store.
    """
    return get_fleet_store_status()



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


class ParseFreezeFrameRequest(BaseModel):
    raw_text: str
    dtc_codes: Optional[List[str]] = None


@app.post(
    "/api/v1/parse-freeze-frame",
    tags=["Agent 1 - Ingestion & Validation"]
)
async def parse_freeze_frame_endpoint(data: ParseFreezeFrameRequest):
    """
    Dedicated endpoint to parse unformatted scan tool text dumps (Autel, Snap-on, Launch, BlueDriver, generic Mode $02)
    and compute empirical physical telemetry analysis.
    """
    parsed = parse_freeze_frame_scanner_text(data.raw_text)
    if not parsed:
        return {
            "success": False,
            "message": "No recognized freeze frame telemetry parameters found in the provided text.",
            "freeze_frame": None,
            "analysis": None
        }
    analysis = analyze_freeze_frame(parsed, dtc_codes=data.dtc_codes or [])
    return {
        "success": True,
        "freeze_frame": parsed,
        "analysis": analysis
    }


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
        if payload.freeze_frame_analysis and not getattr(result, "freeze_frame_analysis", None):
            result.freeze_frame_analysis = payload.freeze_frame_analysis
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
            vehicle_model=full_vehicle_name,
            dtc_codes=request.dtc_codes
        )
        
        return {"status": "success", "repair_plan": repair_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}