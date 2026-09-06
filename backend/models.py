from typing import List
from pydantic import BaseModel, Field


class DiagnosticRequest(BaseModel):
    """Payload received by Agent 1 from the frontend or mechanic input."""
    session_id: str = Field(..., description="Unique session identifier for triage tracking")
    raw_text: str = Field(..., min_length=3, description="Unstructured mechanic notes or customer complaint")

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "sess_abc123",
                "raw_text": "2019 Honda Civic running rough with check engine light on, scanner showed code P0171 system too lean bank 1"
            }
        }
    }


class VehicleDetails(BaseModel):
    """Normalized vehicle specifications verified against NHTSA vPIC."""
    make: str = Field(..., description="Vehicle manufacturer make (e.g., Honda)")
    model: str = Field(..., description="Vehicle model name (e.g., Civic)")
    year: int = Field(..., ge=1900, le=2100, description="Vehicle manufacturing year")
    is_verified: bool = Field(default=False, description="Whether vehicle was validated via NHTSA vPIC")


class Agent1Payload(BaseModel):
    """Agent-to-Agent (A2A) payload sent from Agent 1 to downstream cognitive agents."""
    session_id: str = Field(..., description="Session identifier")
    vehicle_details: VehicleDetails = Field(..., description="Extracted and verified vehicle specifications")
    dtc_codes: List[str] = Field(default_factory=list, description="Extracted Diagnostic Trouble Codes (OBD-II)")
    damaged_parts: List[str] = Field(default_factory=list, description="Identified damaged physical parts")

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "sess_abc123",
                "vehicle_details": {
                    "make": "Honda",
                    "model": "Civic",
                    "year": 2019,
                    "is_verified": True
                },
                "dtc_codes": ["P0171"],
                "damaged_parts": []
            }
        }
    }
