from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from models import DiagnosticRequest, Agent1Payload, VehicleDetails
from nhtsa_validator import verify_vehicle
from nlp_extractor import extract_entities, sanitize_input, extract_dtc_codes, extract_damaged_parts, nlp

app = FastAPI(
    title="Auto-Triage AI - Agent 1",
    description="Gateway Ingestion, Normalization, and Vehicle Validation Agent for Auto-Triage AI",
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
        "service": "Auto-Triage AI - Agent 1",
        "role": "Ingestion & Vehicle Validation Gateway",
        "modes": ["Smart NLP Intake", "Manual Spec Entry"],
        "docs": "/docs",
        "status": "online"
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "agent": "Agent 1 (Ingestion & Validation)"
    }


@app.post(
    "/api/v1/ingest",
    response_model=Agent1Payload,
    status_code=status.HTTP_200_OK,
    tags=["Triage Pipeline"]
)
async def ingest_diagnostic(request: DiagnosticRequest):
    """
    Primary gateway endpoint for Agent 1.
    Supports Dual Mode:
    - Mode A (Manual Spec Entry): Technician supplies explicit Make, Model, Year, DTCs.
    - Mode B (Smart NLP Intake): AI parses natural language complaint for all entities.
    
    Both modes validate against the official US DOT NHTSA vPIC database.
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
        damaged_parts=damaged_parts
    )
