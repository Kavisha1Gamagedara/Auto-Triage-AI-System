"""
Agent 1: Ingestion, Multi-Vehicle spaCy NLP, Typo Correction, and Vehicle Specification Validation.
"""

from .nlp_extractor import (
    extract_entities,
    sanitize_input,
    extract_dtc_codes,
    extract_damaged_parts,
    extract_vin,
    extract_year,
    normalize_mechanic_notes,
    resolve_dtc_hierarchy,
    classify_dtc_cascades,
    fuzzy_correct_make,
    fuzzy_correct_model,
    parse_freeze_frame_scanner_text,
    analyze_freeze_frame,
    nlp
)

from .nhtsa_validator import (
    verify_vehicle,
    decode_vin_nhtsa,
    validate_vin_checksum
)

from .extended_automotive_data import (
    GLOBAL_VEHICLE_CATALOG,
    EV_HYBRID_ADAS_COMPONENTS,
    EXTENDED_DTC_TAXONOMY,
    EXTENDED_DTC_DESCRIPTIONS,
    EXTENDED_DTC_CASCADE_RULES,
    is_jdm_chassis_number,
    is_recognized_global_vehicle,
    validate_chassis_or_vin,
    lookup_jdm_chassis_specs,
    JDM_CHASSIS_REGISTRY
)

from .sri_lanka_plate_validator import (
    extract_sri_lankan_plate,
    validate_plate_components,
    verify_plate_vehicle_compatibility,
    SL_PROVINCES,
    VEHICLE_CLASS_MAP
)

from .fleet_history_store import (
    get_vehicle_history,
    record_vehicle_visit,
    get_fleet_store_status
)

from .complaint_summarizer import (
    summarize_complaint
)

from .privacy_guardrail import (
    mask_pii
)

from .bm25_retrieval_engine import (
    search_dtc_bm25,
    expand_automotive_query,
    BM25DiagnosticEngine,
    get_bm25_engine
)

from .security_guardrail import (
    audit_security_perimeter,
    sanitize_with_security_perimeter
)

from .ensemble_resolver import (
    resolve_ambiguous_entities,
    detect_extraction_ambiguity
)

__all__ = [
    "extract_entities",
    "sanitize_input",
    "extract_dtc_codes",
    "extract_damaged_parts",
    "extract_vin",
    "extract_year",
    "normalize_mechanic_notes",
    "resolve_dtc_hierarchy",
    "classify_dtc_cascades",
    "fuzzy_correct_make",
    "fuzzy_correct_model",
    "parse_freeze_frame_scanner_text",
    "analyze_freeze_frame",
    "nlp",
    "verify_vehicle",
    "decode_vin_nhtsa",
    "validate_vin_checksum",
    "GLOBAL_VEHICLE_CATALOG",
    "EV_HYBRID_ADAS_COMPONENTS",
    "EXTENDED_DTC_TAXONOMY",
    "EXTENDED_DTC_DESCRIPTIONS",
    "EXTENDED_DTC_CASCADE_RULES",
    "is_jdm_chassis_number",
    "is_recognized_global_vehicle",
    "validate_chassis_or_vin",
    "lookup_jdm_chassis_specs",
    "JDM_CHASSIS_REGISTRY",
    "extract_sri_lankan_plate",
    "validate_plate_components",
    "verify_plate_vehicle_compatibility",
    "SL_PROVINCES",
    "VEHICLE_CLASS_MAP",
    "get_vehicle_history",
    "record_vehicle_visit",
    "get_fleet_store_status",
    "summarize_complaint",
    "mask_pii",
    "search_dtc_bm25",
    "expand_automotive_query",
    "BM25DiagnosticEngine",
    "get_bm25_engine",
    "audit_security_perimeter",
    "sanitize_with_security_perimeter",
    "resolve_ambiguous_entities",
    "detect_extraction_ambiguity"
]

