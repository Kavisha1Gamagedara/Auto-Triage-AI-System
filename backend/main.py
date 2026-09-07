from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from models import DiagnosticRequest, Agent1Payload, VehicleDetails
from nhtsa_validator import verify_vehicle
from nlp_extractor import extract_entities, sanitize_input

app = FastAPI(
    title="Auto-Triage AI - Agent 1",
    description="Gateway Ingestion, Normalization, and Vehicle Validation Agent for Auto-Triage AI",
    version="1.0.0",
)

# Configure CORS for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust with specific frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    return {
        "service": "Auto-Triage AI - Agent 1",
        "role": "Ingestion & Vehicle Validation Gateway",
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
    1. Sanitizes incoming raw customer/mechanic complaint text.
    2. Extracts vehicle entities (Make, Model, Year) and OBD-II DTC codes.
    3. Validates the vehicle configuration against NHTSA vPIC database.
    4. Packages and outputs verified A2A payload for Agent 2.
    """
    # 1. Sanitize text input to prevent injection
    sanitized_text = sanitize_input(request.raw_text)

    # 2. Extract entities via NLP / NER
    extracted = extract_entities(sanitized_text)
    make = extracted["make"]
    model = extracted["model"]
    year = extracted["year"]
    dtc_codes = extracted["dtc_codes"]
    damaged_parts = extracted["damaged_parts"]

    # 3. Validate against external NHTSA vPIC database
    is_valid = await verify_vehicle(make=make, model=model, year=year)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle configuration '{year} {make} {model}' was not found in the NHTSA vPIC database."
        )

    # 4. Assemble and return strongly typed A2A payload
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
