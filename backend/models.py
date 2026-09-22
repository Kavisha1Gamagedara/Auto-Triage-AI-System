from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class DiagnosticRequest(BaseModel):
    """
    Payload received by Agent 1 from the technician or customer interface.
    Supports Multi-Mode Intake:
    1. Smart NLP Mode: 'raw_text' provided for automatic spaCy & VIN extraction.
    2. Manual Spec Entry Mode: 'make', 'model', 'year' provided directly.
    3. Direct VIN Intake Mode: 17-character VIN provided directly.
    """
    session_id: str = Field(..., description="Unique session identifier for triage tracking")
    raw_text: Optional[str] = Field(None, description="Unstructured mechanic notes or customer complaint")
    
    # Optional direct VIN Mode
    vin: Optional[str] = Field(None, min_length=17, max_length=17, description="17-character vehicle identification number (ISO 3779)")

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
        has_vin = bool(self.vin and self.vin.strip())

        if not has_text and not has_specs and not has_vin:
            raise ValueError("Provide 'vin' (for Direct VIN Mode), 'raw_text' (for Smart NLP Mode), or ('make', 'model', 'year') (for Manual Spec Entry Mode).")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "sess_abc123",
                "vin": "1HGCR2F85HA000000",
                "raw_text": "2017 Honda Accord with code P0171 and check engine light",
                "make": "Honda",
                "model": "Accord",
                "year": 2017,
                "dtc_codes": ["P0171"],
                "damaged_parts": ["bumper"]
            }
        }
    }


class SpellcheckRequest(BaseModel):
    """Payload for vehicle make and model approximate string matching / spell-checking."""
    make: Optional[str] = Field(default="", description="Raw make string, e.g. 'Toyta'")
    model: Optional[str] = Field(default="", description="Raw model string, e.g. 'Commry'")


class VehicleDetails(BaseModel):
    """Normalized vehicle specifications verified against NHTSA vPIC or VIN decoder."""
    make: str = Field(..., description="Vehicle manufacturer make (e.g., Honda)")
    model: str = Field(..., description="Vehicle model name (e.g., Civic)")
    year: int = Field(..., ge=1900, le=2100, description="Vehicle manufacturing year")
    is_verified: bool = Field(default=False, description="Whether vehicle was validated via NHTSA vPIC")
    
    # Extended VIN Decoded Telemetry (Additive)
    vin: Optional[str] = Field(default=None, description="17-character ISO 3779 VIN if provided/extracted")
    engine: Optional[str] = Field(default=None, description="Engine displacement (e.g., '2.4L')")
    fuel_type: Optional[str] = Field(default=None, description="Primary fuel type (e.g., 'Gasoline')")
    drive_type: Optional[str] = Field(default=None, description="Drive type (e.g., 'FWD', 'AWD', '4x2')")
    body_class: Optional[str] = Field(default=None, description="Body class (e.g., 'Sedan/Saloon')")
    vin_checksum_valid: Optional[bool] = Field(default=None, description="Whether the 9th check digit passed MOD-11 validation")
    fuzzy_corrections: Optional[List[Dict[str, Any]]] = Field(default=None, description="Fuzzy string corrections applied")

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class DTCCodeHierarchy(BaseModel):
    """Taxonomic representation of an OBD-II trouble code for faceted search."""
    exact_code: str = Field(..., description="Granular trouble code, e.g. P0301")
    family_code: str = Field(..., description="Parent code family fallback, e.g. P0300")
    family_name: str = Field(..., description="Functional subsystem, e.g. Ignition / Misfire")
    system: str = Field(..., description="High-level vehicle system, e.g. Powertrain")
    description: str = Field(..., description="Human-readable standard fault description")


class FuzzyCorrection(BaseModel):
    """Details of approximate string matching / spell-checking correction applied to vehicle name."""
    field: str = Field(..., description="Field corrected ('make' or 'model')")
    raw: str = Field(..., description="Original raw token from user or complaint text")
    corrected: str = Field(..., description="Canonical corrected string sent to NHTSA")
    similarity: float = Field(..., description="RapidFuzz ratio similarity score (0-100)")
    levenshtein_distance: int = Field(..., description="Levenshtein edit distance")


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
    
    # Normalized IR Query & Hierarchical Codes (Additive, 100% backward-compatible)
    canonical_query: Optional[str] = Field(default="", description="Normalized, stopword-stripped canonical symptom query")
    dtc_hierarchy: List[DTCCodeHierarchy] = Field(default_factory=list, description="Resolved hierarchical code families for faceted fallback")
    
    # Fuzzy Typo Correction Telemetry (Additive)
    fuzzy_corrections: List[FuzzyCorrection] = Field(default_factory=list, description="Fuzzy string matching corrections applied to typos in make/model")

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


class RepairRequest(BaseModel):
    """Payload sent to Agent 3 to generate repair steps."""
    session_id: str = Field(..., description="Session identifier for tracking")
    vehicle_make: str = Field(..., description="Vehicle manufacturer make")
    vehicle_model: str = Field(..., description="Vehicle model name")
    vehicle_year: int = Field(..., description="Vehicle manufacturing year")
    issue_summary: str = Field(..., description="The root cause or failure mode identified by Agent 2")


class ProcurementRequest(BaseModel):
    """
    Payload sent to Agent 4 to price a repair.

    Vehicle identity is carried as three separate fields, not a concatenated
    string: parts are priced per generation, and the generation lookup needs
    year as an integer to compare against year_from / year_to.
    """
    session_id: str = Field(..., description="Session identifier for tracking")
    root_cause_component: str = Field(..., min_length=1, description="The failed component named by Agent 2 (e.g., 'Mass Air Flow Sensor')")
    make: str = Field(..., min_length=1, description="Vehicle manufacturer make")
    model: str = Field(..., min_length=1, description="Vehicle model name")
    year: int = Field(..., ge=1900, le=2100, description="Vehicle manufacturing year")
    severity: str = Field(default="Medium", description="Risk level passed through from Agent 2")
    safety_warning: str = Field(default="", description="Safety hazards passed through from Agent 2")

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "sess_abc123",
                "root_cause_component": "Brake Pads",
                "make": "Toyota",
                "model": "Corolla",
                "year": 2020,
                "severity": "High",
                "safety_warning": "Support the vehicle on axle stands before removing road wheels."
            }
        }
    }


class QuotedPart(BaseModel):
    """A single priced line item. Every field here is read from MongoDB."""
    part_name: str = Field(..., description="Canonical catalog part name")
    brand: str = Field(..., description="Supplying brand")
    part_number: str = Field(..., description="Catalog part number")
    price_lkr: int = Field(..., description="Price in LKR, from the catalog")
    role: str = Field(..., description="primary, required, or recommended")


class TierQuote(BaseModel):
    """The basket for one quality tier."""
    tier_total_lkr: int = Field(..., description="Sum of the cheapest row per BOM item at this tier")
    complete: bool = Field(..., description="False if any BOM item has no part at this tier")
    parts: List[QuotedPart] = Field(default_factory=list, description="Priced line items")


class ProcurementResponse(BaseModel):
    """Agent 4 output: a tiered, fully database-sourced quote."""
    resolved_part: Optional[str] = Field(None, description="Canonical part name, or null if unresolved")
    match_method: str = Field(..., description="exact, alias_exact, bm25, fuzzy, or none")
    match_confidence: float = Field(..., description="Resolver confidence, 0.0-1.0")
    bill_of_materials: List[str] = Field(default_factory=list, description="Primary part plus companion parts")
    unpriced_items: List[str] = Field(default_factory=list, description="Proposed items the catalog could not confirm")
    tiers: Dict[str, TierQuote] = Field(default_factory=dict, description="Quote per surviving quality tier")
    suppressed_tiers: List[str] = Field(default_factory=list, description="Tiers withheld by a safety rule")
    severity: str = Field(..., description="Passed through from the request")
    safety_warning: str = Field(..., description="Passed through from the request")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal conditions affecting this quote")
    candidates: List[str] = Field(default_factory=list, description="Near-miss part names when resolution failed")