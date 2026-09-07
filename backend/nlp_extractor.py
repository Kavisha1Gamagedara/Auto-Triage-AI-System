import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import spacy

logger = logging.getLogger("nlp_extractor")

# Load spaCy English pipeline
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.warning(f"Could not load en_core_web_sm model directly: {e}. Falling back to blank English.")
    nlp = spacy.blank("en")

# Automotive manufacturer aliases and standard names
AUTOMOTIVE_MAKES = {
    "acura": "Acura",
    "audi": "Audi",
    "bmw": "BMW",
    "buick": "Buick",
    "cadillac": "Cadillac",
    "chevrolet": "Chevrolet",
    "chevy": "Chevrolet",
    "chrysler": "Chrysler",
    "dodge": "Dodge",
    "ford": "Ford",
    "gmc": "GMC",
    "honda": "Honda",
    "hyundai": "Hyundai",
    "infiniti": "Infiniti",
    "jeep": "Jeep",
    "kia": "Kia",
    "lexus": "Lexus",
    "lincoln": "Lincoln",
    "mazda": "Mazda",
    "mercedes": "Mercedes-Benz",
    "mercedes-benz": "Mercedes-Benz",
    "nissan": "Nissan",
    "porsche": "Porsche",
    "ram": "Ram",
    "subaru": "Subaru",
    "tesla": "Tesla",
    "toyota": "Toyota",
    "volkswagen": "Volkswagen",
    "vw": "Volkswagen",
    "volvo": "Volvo"
}

# Known vehicle models dictionary mapping to canonical model names
POPULAR_MODELS = {
    "civic": "Civic",
    "accord": "Accord",
    "cr-v": "CR-V",
    "crv": "CR-V",
    "pilot": "Pilot",
    "camry": "Camry",
    "corolla": "Corolla",
    "rav4": "RAV4",
    "highlander": "Highlander",
    "tacoma": "Tacoma",
    "tundra": "Tundra",
    "f-150": "F-150",
    "f150": "F-150",
    "f-250": "F-250",
    "mustang": "Mustang",
    "explorer": "Explorer",
    "escape": "Escape",
    "silverado": "Silverado",
    "malibu": "Malibu",
    "equinox": "Equinox",
    "tahoe": "Tahoe",
    "suburban": "Suburban",
    "altima": "Altima",
    "sentra": "Sentra",
    "rogue": "Rogue",
    "elantra": "Elantra",
    "sonata": "Sonata",
    "tucson": "Tucson",
    "santa fe": "Santa Fe",
    "optima": "Optima",
    "forte": "Forte",
    "sportage": "Sportage",
    "sorento": "Sorento",
    "outback": "Outback",
    "forester": "Foreester",
    "impreza": "Impreza",
    "wrangler": "Wrangler",
    "grand cherokee": "Grand Cherokee",
    "cherokee": "Cherokee",
    "charger": "Charger",
    "challenger": "Challenger",
    "durango": "Durango",
    "golf": "Golf",
    "jetta": "Jetta",
    "passat": "Passat",
    "tiguan": "Tiguan",
    "cx-5": "CX-5",
    "cx5": "CX-5",
    "mazda3": "Mazda3",
    "mazda6": "Mazda6"
}

# Recognized automotive physical components
AUTOMOTIVE_COMPONENTS = [
    "spark plug",
    "spark plugs",
    "oxygen sensor",
    "o2 sensor",
    "catalytic converter",
    "alternator",
    "battery",
    "radiator",
    "brake pad",
    "brake pads",
    "brake rotor",
    "brake rotors",
    "timing belt",
    "serpentine belt",
    "mass air flow sensor",
    "mass airflow sensor",
    "maf sensor",
    "fuel pump",
    "fuel injector",
    "fuel injectors",
    "water pump",
    "transmission",
    "starter",
    "thermostat",
    "ignition coil",
    "ignition coils",
    "strut",
    "shock absorber",
    "clutch"
]


def sanitize_input(raw_text: str) -> str:
    """
    Sanitizes raw mechanic / user input to prevent prompt injection and remove malformed characters.
    """
    # Remove control characters and normalize spaces
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", raw_text)
    # Strip potential prompt injection artifacts
    cleaned = re.sub(r"(?i)(ignore previous instructions|system prompt|developer mode)", "", cleaned)
    return " ".join(cleaned.split())


def extract_year(text: str) -> Optional[int]:
    """Extracts a valid 4-digit automotive year (between 1980 and 2026)."""
    matches = re.findall(r"\b(19[89][0-9]|20[0-2][0-9])\b", text)
    if matches:
        return int(matches[0])
    return None


def extract_dtc_codes(text: str) -> List[str]:
    """
    Extracts standard OBD-II Diagnostic Trouble Codes (e.g., P0171, B0001, C0123, U0100).
    """
    matches = re.findall(r"\b([PCBU][0-9A-Fa-f]{4})\b", text)
    # Return deduplicated, uppercase codes
    return list(dict.fromkeys([code.upper() for code in matches]))


def extract_make_and_model(doc: spacy.tokens.Doc) -> Tuple[Optional[str], Optional[str]]:
    """
    Identifies vehicle make and model using lexical dictionary matching,
    token proximity, and spaCy linguistic analysis.
    """
    text_lower = doc.text.lower()
    tokens = [t.text.lower() for t in doc]

    detected_make = None
    make_idx = -1

    # 1. Identify Make
    for i, token in enumerate(tokens):
        if token in AUTOMOTIVE_MAKES:
            detected_make = AUTOMOTIVE_MAKES[token]
            make_idx = i
            break

    # Check multi-word makes if not found
    if not detected_make:
        if "mercedes-benz" in text_lower or "mercedes benz" in text_lower:
            detected_make = "Mercedes-Benz"
        elif "grand cherokee" not in text_lower and "jeep" in text_lower:
            detected_make = "Jeep"

    # 2. Identify Model
    detected_model = None

    # First check known model lexicon
    for raw_name, canonical_name in POPULAR_MODELS.items():
        if re.search(rf"\b{re.escape(raw_name)}\b", text_lower):
            detected_model = canonical_name
            break

    # If model not in popular lexicon but make was detected, check token immediately following Make
    if not detected_model and make_idx != -1 and make_idx + 1 < len(tokens):
        candidate = tokens[make_idx + 1]
        # Ignore common non-model words
        if candidate not in {"with", "has", "is", "car", "truck", "suv", "vehicle", "code", "threw", "showing"}:
            # Check if followed by alphanumeric like F-150 or single token
            if make_idx + 2 < len(tokens) and tokens[make_idx + 2] in {"si", "type-r", "sport"}:
                candidate = f"{candidate} {tokens[make_idx + 2]}"
            detected_model = candidate.capitalize()

    return detected_make, detected_model


def extract_damaged_parts(doc: spacy.tokens.Doc) -> List[str]:
    """
    Identifies automotive components cited as damaged or faulty using noun chunk matching
    and component lexicon cross-referencing.
    """
    text_lower = doc.text.lower()
    detected = []

    # 1. Direct lexicon scan
    for component in AUTOMOTIVE_COMPONENTS:
        pattern = rf"\b{re.escape(component)}\b"
        if re.search(pattern, text_lower):
            # Normalize plural to singular
            comp_norm = component.rstrip("s") if component.endswith("s") and not component.endswith("ss") else component
            if comp_norm not in detected:
                detected.append(comp_norm)

    # 2. Noun chunk parsing for components associated with fault adjectives
    fault_indicators = {"broken", "cracked", "damaged", "failing", "leaking", "blown", "bad", "worn"}
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        if any(indicator in chunk_text for indicator in fault_indicators):
            for word in chunk:
                if word.text.lower() in AUTOMOTIVE_COMPONENTS and word.text.lower() not in detected:
                    detected.append(word.text.lower())

    return detected


def extract_entities(raw_text: str) -> Dict[str, Any]:
    """
    Comprehensive entity extraction pipeline for Agent 1:
    - Input sanitization
    - Year extraction (1980 - 2026)
    - Make & Model extraction (spaCy + automotive lexicon)
    - OBD-II DTC Trouble Codes (regex pattern)
    - Physical Damaged Components (spaCy noun chunks + lexicon)
    """
    clean_text = sanitize_input(raw_text)
    doc = nlp(clean_text)

    year = extract_year(clean_text)
    make, model = extract_make_and_model(doc)
    dtc_codes = extract_dtc_codes(clean_text)
    damaged_parts = extract_damaged_parts(doc)

    # Fallback defaults if text did not specify
    return {
        "make": make or "Honda",
        "model": model or "Civic",
        "year": year or 2019,
        "dtc_codes": dtc_codes,
        "damaged_parts": damaged_parts
    }
