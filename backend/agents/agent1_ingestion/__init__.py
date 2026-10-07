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
    validate_chassis_or_vin
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
    "validate_chassis_or_vin"
]
