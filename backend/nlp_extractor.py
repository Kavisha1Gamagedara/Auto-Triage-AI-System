import re
from typing import Dict, List, Any


def sanitize_input(raw_text: str) -> str:
    """
    Sanitizes raw mechanic / user input to prevent prompt injection and remove malformed characters.
    """
    # Remove control characters and normalize spaces
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", raw_text)
    return cleaned.strip()


def extract_entities(raw_text: str) -> Dict[str, Any]:
    """
    Extracts vehicle specifications (Make, Model, Year), OBD-II DTC codes,
    and physical damaged parts from unstructured mechanic or customer text.

    Note: Currently returns mock extracted entities for initial pipeline validation.
    Full spaCy NER and regex/LLM hybrid extraction will be plugged in next.

    Args:
        raw_text: Raw unstructured diagnostic notes or mechanic description.

    Returns:
        dict containing:
            - make (str)
            - model (str)
            - year (int)
            - dtc_codes (List[str])
            - damaged_parts (List[str])
    """
    clean_text = sanitize_input(raw_text)

    # Simple regex fallback to detect standard OBD-II trouble codes (e.g., P0171, B0001, C0123, U0100)
    detected_dtcs = re.findall(r"\b[PCBU][0-9A-Fa-f]{4}\b", clean_text, re.IGNORECASE)
    dtc_codes = [code.upper() for code in detected_dtcs] if detected_dtcs else ["P0171"]

    # Mock entity extraction (to be substituted with spaCy/LLM NER)
    return {
        "make": "Honda",
        "model": "Civic",
        "year": 2019,
        "dtc_codes": dtc_codes,
        "damaged_parts": []
    }
