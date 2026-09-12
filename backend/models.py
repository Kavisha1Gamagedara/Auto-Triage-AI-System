from typing import List, Optional, Dict, Any
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

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class Agent1Payload(BaseModel):
    """
    Agent-to-Agent (A2A) payload sent from Agent 1 to downstream cognitive agents (Agent 2, 3, 4).
    Seamlessly interoperates with both structured VehicleDetails and dictionary vehicle formats.
    """
    session_id: str = Field(..., description="Session identifier")
    vehicle_details: Optional[VehicleDetails] = Field(default=None, description="Extracted and verified vehicle specifications")
    vehicle: Optional[Dict[str, Any]] = Field(default=None, description="Vehicle specifications (Agent 2 compatible)")
    dtc_codes: List[str] = Field(default_factory=list, description="Extracted Diagnostic Trouble Codes (OBD-II)")
    damaged_parts: List[str] = Field(default_factory=list, description="Identified damaged physical parts")
    user_note: Optional[str] = Field(default="", description="Customer complaint or mechanic notes")

    @model_validator(mode="before")
    @classmethod
    def sync_vehicle_fields(cls, data: Any):
        if isinstance(data, dict):
            # If vehicle is provided as dict but vehicle_details isn't
            if "vehicle" in data and data["vehicle"] and ("vehicle_details" not in data or not data["vehicle_details"]):
                v = data["vehicle"]
                if isinstance(v, dict):
                    data["vehicle_details"] = {
                        "make": str(v.get("make", "")),
                        "model": str(v.get("model", "")),
                        "year": int(v.get("year", 2000)),
                        "is_verified": bool(v.get("is_verified", False))
                    }
            # If vehicle_details is provided but vehicle isn't
            elif "vehicle_details" in data and data["vehicle_details"] and ("vehicle" not in data or not data["vehicle"]):
                vd = data["vehicle_details"]
                if hasattr(vd, "model_dump"):
                    vd = vd.model_dump()
                if isinstance(vd, dict):
                    data["vehicle"] = {
                        "make": vd.get("make"),
                        "model": vd.get("model"),
                        "year": vd.get("year")
                    }
        return data

    @model_validator(mode="after")
    def ensure_vehicle_consistency(self):
        if self.vehicle_details and not self.vehicle:
            self.vehicle = {
                "make": self.vehicle_details.make,
                "model": self.vehicle_details.model,
                "year": self.vehicle_details.year
            }
        elif self.vehicle and not self.vehicle_details:
            self.vehicle_details = VehicleDetails(
                make=str(self.vehicle.get("make", "")),
                model=str(self.vehicle.get("model", "")),
                year=int(self.vehicle.get("year", 2000)),
                is_verified=bool(self.vehicle.get("is_verified", False))
            )
        return self

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
                "vehicle": {
                    "make": "Honda",
                    "model": "Civic",
                    "year": 2019
                },
                "dtc_codes": ["P0171"],
                "damaged_parts": ["bumper"],
                "user_note": "Engine lacks power and hesitates during acceleration"
            }
        }
    }


class DiagnosticResult(BaseModel):
    """The strictly formatted payload output from Agent 2 to Agents 3 & 4."""
    root_cause_component: str = Field(description="Exact physical part needing replacement (e.g., 'Mass Air Flow Sensor')")
    failure_mode: str = Field(description="Mechanical reasoning for why the part failed")
    severity: str = Field(description="Risk level: Low, Medium, or Critical")
    safety_warning: str = Field(description="Specific safety hazards for the mechanic")
