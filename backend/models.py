from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class DiagnosticRequest(BaseModel):
    """
    Payload received by Agent 1 from the technician or customer interface.
    Supports Dual-Mode:
    1. Smart NLP Mode: 'raw_text' provided for automatic spaCy extraction.
    2. Manual Spec Entry Mode: 'make', 'model', 'year' provided directly.
    """
    session_id: str = Field(..., description="Unique session identifier for triage tracking")
    raw_text: Optional[str] = Field(None, description="Unstructured mechanic notes or customer complaint")
    
    # Optional direct fields for Manual Spec Entry Mode
    make: Optional[str] = Field(None, description="Direct vehicle make (e.g., Honda, Toyota)")
    model: Optional[str] = Field(None, description="Direct vehicle model (e.g., Civic, Camry)")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Direct vehicle manufacturing year")
    dtc_codes: Optional[List[str]] = Field(default_factory=list, description="Direct list of OBD-II DTC codes")
    damaged_parts: Optional[List[str]] = Field(default_factory=list, description="Direct list of damaged parts")

    @model_validator(mode="after")
    def validate_input_mode(self):
        has_text = bool(self.raw_text and self.raw_text.strip())
        has_specs = bool(self.make and self.model and self.year)

        if not has_text and not has_specs:
            raise ValueError("Either 'raw_text' (for Smart NLP Mode) or ('make', 'model', 'year') (for Manual Spec Entry Mode) must be provided.")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "sess_abc123",
                "raw_text": "2019 Honda Civic with crashed bumper and code P0171",
                "make": "Honda",
                "model": "Civic",
                "year": 2019,
                "dtc_codes": ["P0171"],
                "damaged_parts": ["bumper"]
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
                "damaged_parts": ["bumper"]
            }
        }
    }
