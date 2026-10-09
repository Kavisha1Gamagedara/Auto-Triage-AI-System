from typing import List, Optional, Dict, Any,Literal
from pydantic import BaseModel, Field, model_validator, computed_field

class FreezeFrameData(BaseModel):
    """
    OBD-II Mode $02 Freeze Frame Sensor Telemetry captured at the exact moment
    a Diagnostic Trouble Code (DTC) was registered by the ECU.
    Standardized per SAE J1979 / ISO 15031-5.
    """
    stft_pct: Optional[float] = Field(None, ge=-100.0, le=100.0, description="Short Term Fuel Trim Bank 1 in % (-100 to +100)")
    ltft_pct: Optional[float] = Field(None, ge=-100.0, le=100.0, description="Long Term Fuel Trim Bank 1 in % (-100 to +100)")
    engine_rpm: Optional[int] = Field(None, ge=0, le=15000, description="Engine speed in RPM when code triggered")
    coolant_temp_c: Optional[float] = Field(None, ge=-40.0, le=160.0, description="Engine Coolant Temperature (ECT) in °C")
    maf_gps: Optional[float] = Field(None, ge=0.0, le=600.0, description="Mass Air Flow rate in grams/second (g/s)")
    engine_load_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Calculated engine load value in %")
    vehicle_speed_kmh: Optional[int] = Field(None, ge=0, le=400, description="Vehicle speed in km/h")
    fuel_rail_pressure_kpa: Optional[float] = Field(None, ge=0.0, description="Fuel rail pressure in kPa (GDI & Diesel)")
    battery_soc_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="High-Voltage Battery State of Charge % (EV/Hybrid)")
    battery_cell_delta_mv: Optional[float] = Field(None, ge=0.0, description="Max battery cell voltage deviation in mV (EV/Hybrid)")
    raw_scanner_text: Optional[str] = Field(None, description="Raw unparsed scanner freeze frame text report")


class FreezeFrameAnalysis(BaseModel):
    """
    Master Diagnostic Reasoning evaluation derived from Freeze Frame parameters.
    Mathematically isolates vacuum leaks, fuel pump failures, EV cell imbalances, or sensor faults.
    """
    total_fuel_trim_pct: Optional[float] = Field(None, description="Sum of STFT + LTFT in %")
    trim_condition: str = Field("NORMAL", description="Status: CRITICAL_LEAN, MODERATE_LEAN, NORMAL, MODERATE_RICH, CRITICAL_RICH")
    operating_state: str = Field("UNKNOWN", description="Vehicle operating regime: IDLE_WARM, HIGH_LOAD_CRUISE, COLD_START, HIGHWAY, STOPPED")
    root_cause_verdict: str = Field("", description="Authoritative master mechanic deduction derived from telemetry")
    ruled_out_components: List[str] = Field(default_factory=list, description="Components proven functional by operating telemetry (prevents guessing)")
    high_probability_targets: List[str] = Field(default_factory=list, description="Specific components isolated as primary suspect causes")
    confidence_score: int = Field(80, ge=0, le=100, description="Confidence percentage derived from sensor correlation")


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

    # Optional Sri Lanka Registration Plate & JDM Chassis Code
    plate_number: Optional[str] = Field(None, description="Optional Sri Lankan registration plate, e.g. 'WP CAB-1234'")
    chassis_code: Optional[str] = Field(None, description="Optional JDM Chassis / Model Code, e.g. 'NHP10', 'RU3'")

    # Optional direct fields for Manual Spec Entry Mode
    make: Optional[str] = Field(None, description="Direct vehicle make (e.g., Honda, Toyota)")
    model: Optional[str] = Field(None, description="Direct vehicle model (e.g., Civic, Camry)")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Direct vehicle manufacturing year")
    dtc_codes: Optional[List[str]] = Field(default_factory=list, description="Direct list of OBD-II DTC codes")
    damaged_parts: Optional[List[str]] = Field(default_factory=list, description="Direct list of damaged parts")

    # Optional OBD-II Mode $02 Freeze Frame Sensor Telemetry
    freeze_frame: Optional[FreezeFrameData] = Field(None, description="Optional OBD-II Mode $02 Freeze Frame Sensor Telemetry")

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


class DTCCascadeRequest(BaseModel):
    """Payload for multi-DTC cascade and causal correlation analysis."""
    dtc_codes: List[str] = Field(..., description="List of OBD-II Diagnostic Trouble Codes to analyze")



class SriLankanPlateDetails(BaseModel):
    """
    Statutory Sri Lankan Vehicle Registration (Number Plate) evaluation.
    Governed deterministically by Motor Traffic Act rules.
    """
    plate_number: str = Field(..., description="Normalized plate number, e.g. 'WP CAB-1234'")
    is_valid: bool = Field(..., description="Whether plate satisfies DMT syntax, province, and non-forbidden letter rules")
    format_era: str = Field("modern_3letter", description="Format: modern_3letter, modern_2letter, vintage_sri_series, vintage_numeric")
    province_code: Optional[str] = Field(None, description="2-letter Provincial Council code (WP, CP, SP, NP, EP, NW, NC, SG, UP)")
    province_name: Optional[str] = Field(None, description="Full English province name, e.g. Western Province")
    series: str = Field(..., description="Registration series letters, e.g. 'CAB'")
    number: str = Field(..., description="4-digit serial registration number")
    class_letter: Optional[str] = Field(None, description="First letter indicating statutory vehicle class (C, D, B, A, L, N, etc.)")
    statutory_class: str = Field(..., description="Official vehicle class, e.g. 'Motor Car / Station Wagon / SUV'")
    is_motor_car: bool = Field(True, description="True if class is designated for passenger cars")
    forbidden_letters: List[str] = Field(default_factory=list, description="Prohibited characters detected (I, O, Q)")
    validation_status: str = Field("VALID_SRI_LANKAN_PLATE", description="Deterministic status code")
    status_message: str = Field("", description="Human-readable statutory verification message")


class JDMChassisSpecs(BaseModel):
    """
    Japanese Domestic Market (JDM) vehicle frame and powertrain specifications.
    Derived from factory EPC (Electronic Parts Catalog) databases.
    """
    model_code: str = Field(..., description="Frame model code, e.g. 'NHP10', 'RU3', 'ZVW30'")
    make: str = Field(..., description="Manufacturer (Toyota, Honda, Suzuki, Nissan)")
    model: str = Field(..., description="Model name (Aqua, Vezel Hybrid, Prius, Wagon R)")
    years: Optional[str] = Field(None, description="Production generation years")
    engine_code: Optional[str] = Field(None, description="Factory engine code, e.g. '1NZ-FXE', 'LEB-H1', 'R06A'")
    engine_displacement: Optional[str] = Field(None, description="Displacement, e.g. '1.5L Atkinson Cycle'")
    drivetrain: Optional[str] = Field(None, description="Drive type (Hybrid FWD, BEV, Petrol)")
    transmission: Optional[str] = Field(None, description="Transmission type, e.g. 'e-CVT (P510)', '7-Speed i-DCD'")
    hv_battery: Optional[str] = Field(None, description="High-voltage battery specs, e.g. '144V Ni-MH'")
    inverter: Optional[str] = Field(None, description="Power control unit / inverter model")
    dealer_campaigns: List[str] = Field(default_factory=list, description="Known Toyota Lanka / Stafford Motors / AMW service campaigns")


class FleetVisitRecord(BaseModel):
    """Single diagnostic service event recorded at the repair shop."""
    visit_index: int = Field(..., description="Sequential visit number")
    timestamp: str = Field(..., description="ISO 8601 visit date and time")
    dtc_codes: List[str] = Field(default_factory=list, description="DTC trouble codes diagnosed")
    root_cause_component: str = Field("Pending Diagnosis", description="Isolated failure component")
    technician_notes: Optional[str] = Field("", description="Mechanic observations or repair actions")


class FleetHistorySummary(BaseModel):
    """Local workshop fleet return-visit history keyed by registration plate or chassis number."""
    has_prior_history: bool = Field(False, description="True if vehicle has visited this repair facility before")
    plate_number: Optional[str] = Field(None, description="Primary license plate identifier")
    chassis_number: Optional[str] = Field(None, description="JDM chassis or VIN identifier")
    total_prior_visits: int = Field(0, description="Total number of recorded previous visits")
    first_visit_date: Optional[str] = Field(None, description="First recorded registration timestamp")
    last_visit_date: Optional[str] = Field(None, description="Most recent service timestamp")
    historical_dtcs: List[str] = Field(default_factory=list, description="All trouble codes historically logged for this vehicle")
    previously_repaired_components: List[str] = Field(default_factory=list, description="List of components previously serviced/replaced")
    recent_visit_notes: Optional[str] = Field("", description="Notes from the last repair session")
    visits: List[FleetVisitRecord] = Field(default_factory=list, description="Complete chronological visit log")


class ComplaintSummary(BaseModel):
    """
    NLP Customer & Technician Complaint Abstractive & Extractive Summarization.
    Directly satisfies SLIIT requirements for NLP techniques (NER & Summarization) and LLM deployment.
    """
    executive_summary: str = Field(..., description="Concise 1-2 sentence technical diagnostic abstract")
    chief_complaints: List[str] = Field(default_factory=list, description="Structured primary physical symptom bullet points")
    operational_conditions: List[str] = Field(default_factory=list, description="Driving conditions when fault occurs (e.g., At idle, Cold start)")
    severity_level: str = Field(default="Moderate", description="Assessed severity: Minor, Moderate, or Critical")
    urgency_score: int = Field(default=5, ge=1, le=10, description="Severity/urgency score (1-10)")
    method: str = Field(default="spacy_extractive_linguistic", description="Summarization method: 'hybrid_llm_abstractive' or 'spacy_extractive_linguistic'")


class ComplaintSummarizeRequest(BaseModel):
    """Payload for standalone complaint summarization endpoint."""
    complaint: str = Field(..., description="Raw customer or technician complaint text")
    dtc_codes: Optional[List[str]] = Field(default_factory=list, description="Optional diagnostic trouble codes")


class RedactedEntityInfo(BaseModel):
    """Details of a single redacted Personally Identifiable Information (PII) item."""
    entity_type: str = Field(..., description="Type of PII (SRI_LANKAN_NIC, PHONE_NUMBER, CUSTOMER_NAME, etc.)")
    preview_masked: str = Field(..., description="Privacy-preserving partially masked preview for audit")
    token: str = Field(..., description="Redaction token, e.g. [REDACTED_NIC]")


class PrivacyGuardrailReport(BaseModel):
    """
    Responsible AI User Data Protection & Privacy Guardrail Report.
    Complies with Sri Lanka Personal Data Protection Act (PDPA No. 9 of 2022) & GDPR Art. 5(1)(c).
    """
    pii_detected: bool = Field(False, description="Whether sensitive personal data was detected and redacted")
    total_redactions: int = Field(0, description="Total count of redacted PII tokens")
    redacted_entities: List[RedactedEntityInfo] = Field(default_factory=list, description="Audit log of redacted PII items")
    compliance_standard: str = Field("Sri Lanka PDPA No. 9 of 2022 & GDPR Art. 5(1)(c)", description="Governing data privacy standard")
    sanitized_text: str = Field(..., description="Sanitized complaint text with all PII replaced by safe redaction tokens")


class PIIMaskRequest(BaseModel):
    """Payload for standalone privacy guardrail PII masking endpoint."""
    text: str = Field(..., description="Raw text containing potential user personal data to redact")


class VehicleDetails(BaseModel):
    """Normalized vehicle specifications verified against NHTSA vPIC, JDM Catalog, or VIN decoder."""
    make: str = Field(..., description="Vehicle manufacturer make (e.g., Honda)")
    model: str = Field(..., description="Vehicle model name (e.g., Civic)")
    year: int = Field(..., ge=1900, le=2100, description="Vehicle manufacturing year")
    is_verified: bool = Field(default=False, description="Whether vehicle was validated via NHTSA vPIC or JDM Registry")
    
    # Extended VIN Decoded Telemetry (Additive)
    vin: Optional[str] = Field(default=None, description="17-character ISO 3779 VIN if provided/extracted")
    engine: Optional[str] = Field(default=None, description="Engine displacement (e.g., '2.4L')")
    fuel_type: Optional[str] = Field(default=None, description="Primary fuel type (e.g., 'Gasoline')")
    drive_type: Optional[str] = Field(default=None, description="Drive type (e.g., 'FWD', 'AWD', '4x2')")
    body_class: Optional[str] = Field(default=None, description="Body class (e.g., 'Sedan/Saloon')")
    vin_checksum_valid: Optional[bool] = Field(default=None, description="Whether the 9th check digit passed MOD-11 validation")
    fuzzy_corrections: Optional[List[Dict[str, Any]]] = Field(default=None, description="Fuzzy string corrections applied")

    # Sri Lanka & JDM Automotive Domain Telemetry (Additive)
    sl_plate: Optional[SriLankanPlateDetails] = Field(default=None, description="Sri Lankan registration plate statutory verification")
    jdm_specs: Optional[JDMChassisSpecs] = Field(default=None, description="JDM frame and powertrain specifications")
    plate_compatibility: Optional[Dict[str, Any]] = Field(default=None, description="Plate statutory class vs vehicle compatibility")
    fleet_history: Optional[FleetHistorySummary] = Field(default=None, description="Local workshop return-visit service history")
    complaint_summary: Optional[ComplaintSummary] = Field(default=None, description="NLP Executive Complaint Summary, symptoms, and urgency classification")
    privacy_guardrail: Optional[PrivacyGuardrailReport] = Field(default=None, description="Responsible AI data protection report & PII redaction audit log")

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


class DTCCascadeChain(BaseModel):
    """Causal relationship link between two co-occurring DTC trouble codes."""
    root_code: str = Field(..., description="The upstream causal trigger DTC code")
    consequential_code: str = Field(..., description="The downstream consequential symptom DTC code")
    mechanism: str = Field(..., description="Physical/electrical mechanism explaining the causality")


class DTCCascadeAnalysis(BaseModel):
    """Multi-DTC causal hierarchy and cascade classification."""
    has_cascade: bool = Field(default=False, description="Whether a causal cascade relationship was detected among codes")
    primary_code: Optional[str] = Field(default=None, description="The identified root-cause trigger DTC code")
    primary_description: Optional[str] = Field(default=None, description="Description of the primary root code")
    primary_subsystem: Optional[str] = Field(default=None, description="Vehicle subsystem where fault originated")
    cascade_codes: List[str] = Field(default_factory=list, description="Consequential secondary DTC codes")
    isolated_codes: List[str] = Field(default_factory=list, description="Unrelated secondary DTC codes")
    cascade_chains: List[DTCCascadeChain] = Field(default_factory=list, description="List of causal propagation links")
    diagnostic_summary: Optional[str] = Field(default="", description="Master mechanic plain-language explanation of cascade")


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

    # Multi-DTC Cascade & Correlation Analysis (Additive)
    dtc_cascade: Optional[DTCCascadeAnalysis] = Field(default=None, description="Multi-DTC causal hierarchy and cascade classification")

    # OBD-II Mode $02 Freeze Frame Sensor Telemetry (Additive)
    freeze_frame: Optional[FreezeFrameData] = Field(default=None, description="Ingested OBD-II Freeze Frame Sensor Telemetry")
    freeze_frame_analysis: Optional[FreezeFrameAnalysis] = Field(default=None, description="Master Diagnostic Analysis derived from Freeze Frame metrics")

    # Sri Lanka & JDM Automotive Domain Telemetry (Additive)
    sl_plate: Optional[SriLankanPlateDetails] = Field(default=None, description="Sri Lankan registration plate statutory verification")
    jdm_specs: Optional[JDMChassisSpecs] = Field(default=None, description="JDM frame and powertrain specifications")
    plate_compatibility: Optional[Dict[str, Any]] = Field(default=None, description="Plate statutory class vs vehicle compatibility")
    fleet_history: Optional[FleetHistorySummary] = Field(default=None, description="Local workshop return-visit service history")
    complaint_summary: Optional[ComplaintSummary] = Field(default=None, description="NLP Executive Complaint Summary, symptoms, and urgency classification")
    privacy_guardrail: Optional[PrivacyGuardrailReport] = Field(default=None, description="Responsible AI data protection report & PII redaction audit log")

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


class Hypothesis(BaseModel):
    root_cause_component: str = Field(
        ..., description="The specific failing component, e.g. 'Mass Airflow (MAF) Sensor'"
    )
    failure_mode: str = Field(
        ..., description="How it fails, e.g. 'Contaminated hot-wire element under-reporting airflow'"
    )
    confidence: int = Field(
        ..., ge=0, le=100,
        description="Independent confidence 0-100 for THIS hypothesis. Values across hypotheses do NOT sum to 100."
    )
    supporting_evidence: List[str] = Field(
        ..., description="The specific DTC codes and phrases from the user note that support this"
    )
    confirming_test: str = Field(
        ..., description="The cheapest workshop test that confirms or eliminates this hypothesis"

    )

    #Verification of alternative hypotheses is a separate stage from the initial diagnostic reasoning.
    verified: bool =Field(
        default =True,
        description ="Set by the verifcation stage. Not produced by the diagnostic stage."

    )
    verification_note: str =Field(
        default ="",
        description ="Why this hypothesis was rejected, it it was."
    )

    #Adding catalog_part_name to support Agent 4 procurement request
    catalog_part_name: Optional[str] = Field(
        default=None,
        description="Exact part name from the supplied catalog list, if one matches this component. Null if no catalog entry fits."
    )

    reason: str = Field(
       default="",
       description="Why this hypothesis was rejected. Required when plausible is false; omit otherwise."
   )

class DiagnosticResult(BaseModel):

   #To verify everything got rejected - Agent 2
    status: Literal["diagnosed","unverified"] = "diagnosed"

    reasoning_steps: List[str] = Field(
        ..., description="Ordered diagnostic reasoning from symptoms to candidates, BEFORE ranking"
    )
    primary_hypothesis: Hypothesis
    differential_hypotheses: List[Hypothesis] = Field(
        default_factory=list, max_length=3,
        description="Alternatives ranked by descending confidence. Distinct components, not restatements."
    )
    severity: Literal["low", "moderate", "high", "critical"]
    safety_warning: str
    freeze_frame_analysis: Optional[FreezeFrameAnalysis] = Field(default=None, description="Ground-truth freeze frame analysis")

    @model_validator(mode="after")
    def primary_must_rank_highest(self):
        candidates = [h for h in self.differential_hypotheses if h.verified]

       #Ranking the verified candidates
        if candidates:
            best = max(candidates, key=lambda h: h.confidence)
            if best.confidence > self.primary_hypothesis.confidence and self.primary_hypothesis.verified:
                others = [h for h in self.differential_hypotheses if h is not best]
                others.append(self.primary_hypothesis)
                self.primary_hypothesis = best
                self.differential_hypotheses = sorted(others, key=lambda h: h.confidence, reverse=True)
            else:
                self.differential_hypotheses = sorted(
                    self.differential_hypotheses, key=lambda h: h.confidence, reverse=True
                )
        return self

    @computed_field
    @property
    def root_cause_component(self) -> str:
        return self.primary_hypothesis.root_cause_component

    @computed_field
    @property
    def failure_mode(self) -> str:
        return self.primary_hypothesis.failure_mode
    


class RepairRequest(BaseModel):
    """Payload sent to Agent 3 to generate repair steps."""
    session_id: str = Field(..., description="Session identifier for tracking")
    vehicle_make: str = Field(..., description="Vehicle manufacturer make")
    vehicle_model: str = Field(..., description="Vehicle model name")
    vehicle_year: int = Field(..., description="Vehicle manufacturing year")
    issue_summary: str = Field(..., description="The root cause or failure mode identified by Agent 2")
    dtc_codes: List[str] = Field(default_factory=list, description="OBD-II codes from Agent 1, used to find the matching diagnostic manual")


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
    price_updated: str = Field(..., description="Date the price was last updated (YYYY-MM-DD)")
    currency: str = Field(..., description="Currency of the price")
    supplier: str = Field(..., description="Supplier of the part")
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

#Verification of alternative hypotheses is a separate stage from the initial diagnostic reasoning - Agent 2
class VerificationVerdict(BaseModel):
    index: int = Field(..., ge=0, description="Position of the hypothesis in the list under review")
    plausible: bool = Field(..., description="Whether this component exists on the vehicle and explains the codes")
    reason: Optional[str] = Field(
        default="",
        description="Why this hypothesis was rejected. Required when plausible is false; omit otherwise."
    )

class VerificationResponse(BaseModel):
    drivetrain: str = Field(
        default="",
        description="The vehicle's drivetrain type, determined before evaluating any component."
    )
    verdicts: List[VerificationVerdict]