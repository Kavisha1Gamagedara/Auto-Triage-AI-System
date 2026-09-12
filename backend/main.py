import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from models import DiagnosticRequest, Agent1Payload, VehicleDetails, DiagnosticResult
from nhtsa_validator import verify_vehicle
from nlp_extractor import extract_entities, sanitize_input, extract_dtc_codes, extract_damaged_parts, nlp

# Safely import Agent 2 diagnostic reasoning engine
try:
    import groq
    from agent2_logic import deduce_root_cause
except Exception as e:
    groq = None
    deduce_root_cause = None

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
    # Check if direct vehicle specs were provided (Manual Spec Entry Mode)
    if request.make and request.model and request.year:
        make = request.make.strip()
        model = request.model.strip()
        year = int(request.year)
        
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
        # Smart NLP Intake Mode
        sanitized_text = sanitize_input(request.raw_text or "")
        extracted = extract_entities(sanitized_text)
        make = extracted["make"]
        model = extracted["model"]
        year = extracted["year"]
        dtc_codes = extracted["dtc_codes"]
        damaged_parts = extracted["damaged_parts"]

    # Validate against external official NHTSA vPIC database
    is_valid = await verify_vehicle(make=make, model=model, year=year)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle configuration '{year} {make} {model}' was not found in the official US DOT NHTSA vPIC database."
        )

    # Assemble and return verified A2A payload for Agent 2
    return Agent1Payload(
        session_id=request.session_id,
        vehicle_details=VehicleDetails(
            make=make,
            model=model,
            year=year,
            is_verified=True
        ),
        dtc_codes=dtc_codes,
        damaged_parts=damaged_parts,
        user_note=request.raw_text or ""
    )


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
