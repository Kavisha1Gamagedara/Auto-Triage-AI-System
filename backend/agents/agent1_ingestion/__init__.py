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
    "validate_vin_checksum"
]
