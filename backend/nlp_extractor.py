import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("nlp_extractor")

try:
    from rapidfuzz import fuzz, process, distance
    HAS_RAPIDFUZZ = True
except ImportError as e:
    logger.warning(f"RapidFuzz is not installed ({e}). Approximate string matching disabled.")
    HAS_RAPIDFUZZ = False

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        logger.warning(f"Could not load en_core_web_sm model: {e}. Using blank English.")
        nlp = spacy.blank("en")
except ImportError as e:
    logger.warning(f"spaCy is not installed in the current environment ({e}). Using pure regex/rule-based fallback.")
    spacy = None
    nlp = None

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
    "forester": "Forester",
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
    "mazda6": "Mazda6",
    "prius": "Prius",
    "4runner": "4Runner",
    "townace": "Townace",
    "town ace": "Townace"
}

# Recognized automotive physical components (Mechanical, Body, Collision, Electrical, Suspension)
AUTOMOTIVE_COMPONENTS = [
    # Body & Collision
    "bumper",
    "front bumper",
    "rear bumper",
    "fender",
    "hood",
    "headlight",
    "headlights",
    "taillight",
    "taillights",
    "grille",
    "door",
    "side mirror",
    "mirror",
    "windshield",
    "window",
    "trunk",
    "tailgate",
    "quarter panel",
    "rocker panel",
    "spoiler",
    # Powertrain & Engine
    "spark plug",
    "spark plugs",
    "oxygen sensor",
    "o2 sensor",
    "catalytic converter",
    "alternator",
    "battery",
    "radiator",
    "radiator hose",
    "timing belt",
    "timing chain",
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
    "clutch",
    "turbo",
    "turbocharger",
    "intercooler",
    "exhaust manifold",
    "intake manifold",
    "muffler",
    "exhaust pipe",
    # Brakes, Suspension & Steering
    "brake pad",
    "brake pads",
    "brake rotor",
    "brake rotors",
    "brake caliper",
    "strut",
    "struts",
    "shock absorber",
    "shock absorbers",
    "control arm",
    "ball joint",
    "tie rod",
    "sway bar",
    "wheel bearing",
    "wheel",
    "tire",
    "tires",
    "axle",
    "cv axle",
    "drive shaft",
    "power steering pump"
]

DAMAGE_ADJECTIVES = {
    "crashed", "damaged", "broken", "cracked", "smashed", "dented", "bent",
    "shattered", "scratched", "punctured", "torn", "failing", "leaking",
    "blown", "bad", "worn", "faulty", "loose", "burned", "defective", "missing"
}

# Automotive mechanic slang and symptom synonym expansion dictionary
AUTOMOTIVE_SYNONYMS = {
    # Misfire, rough engine & combustion hesitation
    "shudder": "engine misfire",
    "shuddering": "engine misfire",
    "hesitation": "engine misfire hesitation",
    "hesitating": "engine misfire hesitation",
    "hesitates": "engine misfire hesitation",
    "bucking": "engine misfire surge",
    "jerking": "engine hesitation misfire",
    "rough idle": "rough idle misfire",
    "chugging": "engine misfire rough running",
    "stumble": "acceleration hesitation misfire",
    "stumbling": "acceleration hesitation misfire",
    "misfiring": "engine misfire",
    
    # Fuel, vapor & air leaks
    "smells like gas": "fuel vapor leak rich condition",
    "smells like fuel": "fuel vapor leak rich condition",
    "fuel smell": "fuel vapor leak rich condition",
    "gas smell": "fuel vapor leak rich condition",
    "rotten egg smell": "catalytic converter failure sulfur odor",
    "black smoke": "excessive rich fuel mixture",
    "white smoke": "coolant leak head gasket failure",
    "blue smoke": "engine oil burning piston ring failure",
    
    # Airflow & vacuum
    "vacuum leak": "unmetered intake air leak",
    "hissing sound": "intake vacuum leak",
    "whistling": "intake or turbocharger vacuum leak",
    
    # Starting & electrical
    "clicking sound when starting": "starter motor solenoid battery failure",
    "clicking when starting": "starter motor solenoid battery failure",
    "slow crank": "weak battery or starter motor draw",
    "wont crank": "no crank starter battery failure",
    "won't crank": "no crank starter battery failure",
    
    # Braking & suspension
    "squealing brakes": "brake pad wear indicator worn pads",
    "grinding brakes": "brake pad rotor metal on metal wear",
    "spongy brake": "brake fluid air hydraulic leak",
    "pulling to one side": "wheel alignment uneven brake caliper tie rod wear",
    "clunking over bumps": "strut mount sway bar bushing ball joint wear"
}

# Standard English & colloquial filler stopwords to filter when creating canonical IR queries
IR_STOPWORDS = {
    "a", "about", "above", "after", "again", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", 
    "but", "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", 
    "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", 
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", 
    "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", 
    "of", "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", 
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the", 
    "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", 
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", 
    "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would", 
    "you", "your", "yours", "yourself", "yourselves",
    # Automotive conversational fillers
    "customer", "states", "complaint", "noted", "reporting", "driver", "feels", "like", 
    "says", "car", "vehicle", "truck", "suv", "problem", "issue", "got", "getting", "showing"
}

# Standard OBD-II code family taxonomy and hierarchy mapping
DTC_TAXONOMY = {
    # P00xx - Fuel and Air Metering and Auxiliary Emission Controls
    "P00": {"family": "P0000", "family_name": "Fuel and Air Metering Auxiliary Controls", "system": "Powertrain"},
    "P01": {"family": "P0100", "family_name": "Fuel and Air Metering Circuit / Sensor", "system": "Powertrain"},
    "P02": {"family": "P0200", "family_name": "Fuel Injector Circuit / Injection Timing", "system": "Powertrain"},
    "P03": {"family": "P0300", "family_name": "Ignition System or Misfire Detection", "system": "Powertrain"},
    "P04": {"family": "P0400", "family_name": "Auxiliary Emission Controls (Catalyst/EVAP/EGR)", "system": "Powertrain"},
    "P05": {"family": "P0500", "family_name": "Vehicle Speed, Idle Control, Auxiliary Inputs", "system": "Powertrain"},
    "P06": {"family": "P0600", "family_name": "Computer and Output Auxiliary Circuits", "system": "Powertrain"},
    "P07": {"family": "P0700", "family_name": "Transmission Control System", "system": "Powertrain"},
    "P08": {"family": "P0800", "family_name": "Transmission Control System Auxiliary", "system": "Powertrain"},
    # B0xxx - Body System
    "B0": {"family": "B0000", "family_name": "Body Restraints / Airbags / Seatbelts", "system": "Body"},
    # C0xxx - Chassis System
    "C0": {"family": "C0000", "family_name": "Chassis / ABS / Traction Control", "system": "Chassis"},
    # U0xxx - Network & Communication
    "U0": {"family": "U0000", "family_name": "Network & CAN Bus Communication", "system": "Network Communication"}
}

# Known granular DTC descriptions for canonical resolution
KNOWN_DTC_DESCRIPTIONS = {
    "P0171": "System Too Lean (Bank 1)",
    "P0172": "System Too Rich (Bank 1)",
    "P0174": "System Too Lean (Bank 2)",
    "P0300": "Random or Multiple Cylinder Misfire Detected",
    "P0301": "Cylinder 1 Misfire Detected",
    "P0302": "Cylinder 2 Misfire Detected",
    "P0303": "Cylinder 3 Misfire Detected",
    "P0304": "Cylinder 4 Misfire Detected",
    "P0305": "Cylinder 5 Misfire Detected",
    "P0306": "Cylinder 6 Misfire Detected",
    "P0420": "Catalyst System Efficiency Below Threshold (Bank 1)",
    "P0430": "Catalyst System Efficiency Below Threshold (Bank 2)",
    "P0440": "Evaporative Emission (EVAP) System Malfunction",
    "P0442": "EVAP System Small Leak Detected",
    "P0455": "EVAP System Large Leak Detected",
    "P0251": "Injection Pump Fuel Metering Control 'A' Malfunction",
    "P0101": "Mass or Volume Air Flow Circuit Range/Performance",
    "P0102": "Mass or Volume Air Flow Circuit Low Input",
    "P0113": "Intake Air Temperature Circuit High Input",
    "P0128": "Coolant Thermostat (Coolant Temperature Below Regulating Temp)",
    "P0500": "Vehicle Speed Sensor 'A' Malfunction",
    "P0700": "Transmission Control System Malfunction"
}


def normalize_mechanic_notes(raw_text: str) -> str:
    """
    Performs Information Retrieval query processing on customer/mechanic notes:
    1. Lowercasing and punct-normalization
    2. Automotive synonym and jargon expansion (e.g. 'shudder' -> 'misfire')
    3. Stopword removal (filtering out conversational and generic filler words)
    4. Canonical query synthesis for enhanced vector/lexical retrieval recall
    """
    if not raw_text or not raw_text.strip():
        return ""

    text = raw_text.lower()
    
    # 1. Expand domain slang and synonyms (phrase-level first, then word-level)
    expanded_tokens = []
    # Sort phrases by length descending to match multi-word phrases first
    sorted_synonyms = sorted(AUTOMOTIVE_SYNONYMS.keys(), key=lambda s: len(s), reverse=True)
    
    # Replace known phrases with canonical markers
    for phrase in sorted_synonyms:
        if phrase in text:
            replacement = f" {AUTOMOTIVE_SYNONYMS[phrase]} "
            text = text.replace(phrase, replacement)

    # 2. Tokenize into words
    words = re.findall(r"\b[a-z0-9\-_]{2,}\b", text)

    # 3. Filter stopwords and deduplicate preserving order
    seen = set()
    for w in words:
        if w not in IR_STOPWORDS:
            # Expand single-word synonym if not already expanded
            expanded = AUTOMOTIVE_SYNONYMS.get(w, w)
            for sub_word in expanded.split():
                if sub_word not in seen and sub_word not in IR_STOPWORDS:
                    seen.add(sub_word)
                    expanded_tokens.append(sub_word)

    return " ".join(expanded_tokens)


def resolve_dtc_hierarchy(dtc_codes: List[str]) -> List[Dict[str, Any]]:
    """
    Resolves OBD-II Diagnostic Trouble Codes into a hierarchical taxonomy:
    - Exact Code (e.g. P0301)
    - Parent Family Code fallback (e.g. P0300)
    - Subsystem / Functional Domain (e.g. Ignition / Misfire)
    - High-level System (e.g. Powertrain)
    - Official / standard description
    """
    hierarchies = []
    for raw_code in dtc_codes:
        code = raw_code.strip().upper()
        if not code:
            continue

        # Extract prefix (e.g. P03 from P0301, or B0 from B0001)
        prefix_3 = code[:3] if len(code) >= 3 else code
        prefix_2 = code[:2] if len(code) >= 2 else code

        # Match taxonomy
        tax = DTC_TAXONOMY.get(prefix_3) or DTC_TAXONOMY.get(prefix_2)
        if not tax:
            # Fallback for standard P codes
            if code.startswith("P"):
                tax = {"family": "P0000", "family_name": "General Powertrain Fault", "system": "Powertrain"}
            elif code.startswith("B"):
                tax = {"family": "B0000", "family_name": "General Body Electrical Fault", "system": "Body"}
            elif code.startswith("C"):
                tax = {"family": "C0000", "family_name": "General Chassis Fault", "system": "Chassis"}
            elif code.startswith("U"):
                tax = {"family": "U0000", "family_name": "Network Communication Fault", "system": "Network Communication"}
            else:
                tax = {"family": code, "family_name": "Unknown Diagnostic Fault", "system": "Unknown"}

        desc = KNOWN_DTC_DESCRIPTIONS.get(code, f"{tax['family_name']} (Fault Code {code})")

        hierarchies.append({
            "exact_code": code,
            "family_code": tax["family"],
            "family_name": tax["family_name"],
            "system": tax["system"],
            "description": desc
        })

    return hierarchies


def sanitize_input(raw_text: str) -> str:
    """
    Sanitizes raw mechanic / user input to prevent prompt injection and remove malformed characters.
    """
    # Remove control characters and normalize spaces
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", raw_text)
    # Strip potential prompt injection artifacts
    cleaned = re.sub(r"(?i)(ignore previous instructions|system prompt|developer mode)", "", cleaned)
    return " ".join(cleaned.split())


def extract_vin(text: str) -> Optional[str]:
    """
    Extracts a standard 17-character ISO 3779 VIN from unstructured text.
    Standard VINs consist of letters A-Z (excluding I, O, Q) and digits 0-9.
    """
    matches = re.findall(r"\b([A-HJ-NPR-Z0-9]{17})\b", text.upper())
    if matches:
        return matches[0]
    return None


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


FUZZY_EXCLUDED_TOKENS = {
    "the", "car", "truck", "auto", "vehicle", "suv", "van", "with", "has", "had", "have",
    "and", "for", "code", "codes", "light", "engine", "check", "running", "rough",
    "note", "notes", "customer", "brought", "technician", "showing", "misfire",
    "broken", "damaged", "leak", "leaking", "smell", "brake", "sound", "noise",
    "threw", "started", "miles", "speed", "idle", "door", "part", "parts", "in", "at",
    "from", "into", "over", "under", "after", "front", "rear", "left", "right", "side",
    "turn", "headlight", "bumper", "mirror", "fender", "hood", "trunk", "exhaust", "sensor"
}


def fuzzy_correct_make(token: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Normalizes a vehicle manufacturer name using Levenshtein distance and RapidFuzz ratio.
    Tolerates typos (e.g., 'Toyta' -> 'Toyota', 'Mercdes' -> 'Mercedes-Benz', 'Hnda' -> 'Honda').
    
    Returns:
        (canonical_make_or_original, correction_metadata_or_none)
    """
    if not token or not isinstance(token, str):
        return token, None

    clean = token.lower().strip()
    if not clean or len(clean) < 3 or clean in FUZZY_EXCLUDED_TOKENS or clean.isdigit():
        return token, None

    # Exact match check
    if clean in AUTOMOTIVE_MAKES:
        return AUTOMOTIVE_MAKES[clean], None

    if not HAS_RAPIDFUZZ:
        return token, None

    # RapidFuzz approximate match
    best_choice, best_score, _ = process.extractOne(clean, list(AUTOMOTIVE_MAKES.keys()), scorer=fuzz.ratio)
    lev = distance.Levenshtein.distance(clean, best_choice)

    matched = False
    # For short tokens (len <= 3): only allow lev <= 1 and score >= 80.0
    if len(clean) <= 3 and len(best_choice) <= 3:
        if lev <= 1 and best_score >= 80.0:
            matched = True
    # For 4-letter tokens (e.g. 'hnda'): lev <= 1 or score >= 85.0
    elif len(clean) == 4 or len(best_choice) == 4:
        if (lev <= 1 or best_score >= 85.0) and abs(len(clean) - len(best_choice)) <= 1:
            matched = True
    # For tokens len >= 5 (e.g. 'toyta', 'mercdes'): lev <= 2 or score >= 85.0 (with score >= 70.0)
    elif (lev <= 2 or best_score >= 85.0) and abs(len(clean) - len(best_choice)) <= 2 and best_score >= 70.0:
        matched = True

    if matched:
        canonical = AUTOMOTIVE_MAKES[best_choice]
        return canonical, {
            "field": "make",
            "raw": token,
            "corrected": canonical,
            "similarity": round(float(best_score), 1),
            "levenshtein_distance": int(lev)
        }

    return token, None


def fuzzy_correct_model(token: str, make: Optional[str] = None) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Normalizes a vehicle model name using Levenshtein distance and RapidFuzz ratio.
    Tolerates typos (e.g., 'Commry' -> 'Camry', 'Silvrado' -> 'Silverado', 'Civc' -> 'Civic').
    
    Returns:
        (canonical_model_or_original, correction_metadata_or_none)
    """
    if not token or not isinstance(token, str):
        return token, None

    clean = token.lower().strip()
    if not clean or len(clean) < 3 or clean in FUZZY_EXCLUDED_TOKENS or clean.isdigit():
        return token, None

    # Exact match check
    if clean in POPULAR_MODELS:
        return POPULAR_MODELS[clean], None

    if not HAS_RAPIDFUZZ:
        return token, None

    # RapidFuzz approximate match
    best_choice, best_score, _ = process.extractOne(clean, list(POPULAR_MODELS.keys()), scorer=fuzz.ratio)
    lev = distance.Levenshtein.distance(clean, best_choice)

    matched = False
    if len(clean) <= 3 and len(best_choice) <= 3:
        if lev <= 1 and best_score >= 80.0:
            matched = True
    elif len(clean) == 4 or len(best_choice) == 4:
        if (lev <= 1 or best_score >= 85.0) and abs(len(clean) - len(best_choice)) <= 1:
            matched = True
    elif (lev <= 2 or best_score >= 85.0) and abs(len(clean) - len(best_choice)) <= 2 and best_score >= 70.0:
        matched = True

    if matched:
        canonical = POPULAR_MODELS[best_choice]
        return canonical, {
            "field": "model",
            "raw": token,
            "corrected": canonical,
            "similarity": round(float(best_score), 1),
            "levenshtein_distance": int(lev)
        }

    return token, None


def extract_make_and_model(doc: Any) -> Tuple[Optional[str], Optional[str], List[Dict[str, Any]]]:
    """
    Identifies vehicle make and model using lexical dictionary matching,
    RapidFuzz fuzzy string matching (typo tolerance), and linguistic proximity.
    """
    if doc is None:
        return None, None, []

    if hasattr(doc, "text"):
        text_lower = doc.text.lower()
        tokens = [t.text.lower() for t in doc]
        raw_tokens = [t.text for t in doc]
    else:
        text_lower = str(doc).lower()
        tokens = re.findall(r"\b[\w-]+\b", text_lower)
        raw_tokens = re.findall(r"\b[\w-]+\b", str(doc))

    detected_make = None
    make_idx = -1
    corrections: List[Dict[str, Any]] = []

    # 1. Identify Make (Exact match first)
    for i, token in enumerate(tokens):
        if token in AUTOMOTIVE_MAKES:
            detected_make = AUTOMOTIVE_MAKES[token]
            make_idx = i
            break

    # Multi-word exact makes check
    if not detected_make:
        if "mercedes-benz" in text_lower or "mercedes benz" in text_lower:
            detected_make = "Mercedes-Benz"
        elif "land rover" in text_lower:
            detected_make = "Land Rover"
        elif "grand cherokee" not in text_lower and "jeep" in text_lower:
            detected_make = "Jeep"

    # If make not found by exact match, try fuzzy typo match across tokens
    if not detected_make:
        for i, token in enumerate(tokens):
            if token.isdigit() or len(token) < 3 or token in FUZZY_EXCLUDED_TOKENS:
                continue
            canonical_make, corr = fuzzy_correct_make(raw_tokens[i] if i < len(raw_tokens) else token)
            if corr:
                detected_make = canonical_make
                make_idx = i
                corrections.append(corr)
                break

    # 2. Identify Model (Exact match first)
    detected_model = None

    # First check known model lexicon
    for raw_name, canonical_name in POPULAR_MODELS.items():
        if re.search(rf"\b{re.escape(raw_name)}\b", text_lower):
            detected_model = canonical_name
            break

    # If model not in popular lexicon, try fuzzy match on candidate tokens
    if not detected_model:
        # Check token immediately following Make first
        candidate_indices = []
        if make_idx != -1 and make_idx + 1 < len(tokens):
            candidate_indices.append(make_idx + 1)
        # Then all other tokens
        for idx in range(len(tokens)):
            if idx not in candidate_indices and idx != make_idx:
                candidate_indices.append(idx)

        for idx in candidate_indices:
            token = tokens[idx]
            if token.isdigit() or len(token) < 3 or token in FUZZY_EXCLUDED_TOKENS:
                continue
            raw_token = raw_tokens[idx] if idx < len(raw_tokens) else token
            canonical_model, corr = fuzzy_correct_model(raw_token)
            if corr:
                detected_model = canonical_model
                corrections.append(corr)
                break

    # If still not found, check if make was detected and token immediately following looks like a model
    if not detected_model and make_idx != -1 and make_idx + 1 < len(tokens):
        candidate = tokens[make_idx + 1]
        if candidate not in FUZZY_EXCLUDED_TOKENS and not candidate.isdigit() and len(candidate) >= 2:
            if make_idx + 2 < len(tokens) and tokens[make_idx + 2] in {"si", "type-r", "sport"}:
                candidate = f"{candidate} {tokens[make_idx + 2]}"
            detected_model = candidate.capitalize()

    return detected_make, detected_model, corrections


def extract_damaged_parts(doc: Any) -> List[str]:
    """
    Identifies automotive components cited as damaged, faulty, or collided
    using lexicon cross-referencing and spaCy linguistic dependency matching.
    """
    if doc is None:
        return []

    text_lower = doc.text.lower() if hasattr(doc, "text") else str(doc).lower()
    detected = []

    # 1. Direct lexicon scan for recognized automotive parts
    for component in AUTOMOTIVE_COMPONENTS:
        pattern = rf"\b{re.escape(component)}\b"
        if re.search(pattern, text_lower):
            # Normalize plural to singular
            comp_norm = component.rstrip("s") if component.endswith("s") and not component.endswith("ss") else component
            if comp_norm not in detected:
                detected.append(comp_norm)

    # 2. Linguistic dependency & noun-chunk parsing (when spaCy has a parser loaded)
    if hasattr(doc, "noun_chunks") and getattr(doc, "has_annotation", lambda x: False)("DEP"):
        # Check token dependencies for adjectives modifying nouns (e.g., "crashed bumper", "dented door")
        for token in doc:
            if token.pos_ in ("NOUN", "PROPN"):
                token_lower = token.text.lower()
                # Check children/adjectives modifying this noun
                modifiers = [child.text.lower() for child in token.children if child.dep_ in ("amod", "compound", "acomp")]
                if any(mod in DAMAGE_ADJECTIVES for mod in modifiers):
                    comp_norm = token_lower.rstrip("s") if token_lower.endswith("s") and not token_lower.endswith("ss") else token_lower
                    if comp_norm not in detected and len(comp_norm) > 2:
                        detected.append(comp_norm)

        # Check noun chunks containing damage indicators
        NON_PART_WORDS = {"car", "truck", "suv", "vehicle", "problem", "issue", "acceleration", "acceleration code", "note", "code"}
        try:
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.lower()
                if any(indicator in chunk_text for indicator in DAMAGE_ADJECTIVES):
                    for word in chunk:
                        w_lower = word.text.lower()
                        if (w_lower in AUTOMOTIVE_COMPONENTS or word.pos_ in ("NOUN", "PROPN")) and w_lower not in DAMAGE_ADJECTIVES and w_lower not in NON_PART_WORDS and len(w_lower) > 2:
                            norm = w_lower.rstrip("s") if w_lower.endswith("s") and not w_lower.endswith("ss") else w_lower
                            if norm not in detected:
                                detected.append(norm)
        except Exception as e:
            logger.debug(f"Could not parse noun_chunks: {e}")

    # Clean up substrings (e.g., if 'spark plug' is in detected, drop 'plug' or 'spark')
    cleaned_parts = []
    for part in detected:
        if not any(part != other and part in other for other in detected):
            cleaned_parts.append(part)

    return cleaned_parts


def extract_entities(raw_text: str) -> Dict[str, Any]:
    """
    Comprehensive entity extraction pipeline for Agent 1:
    - Input sanitization
    - Year extraction (1980 - 2026)
    - Make & Model extraction (spaCy / lexicon fallback)
    - OBD-II DTC Trouble Codes (regex pattern)
    - Physical Damaged Components (noun chunks / lexicon)
    """
    clean_text = sanitize_input(raw_text)
    doc = nlp(clean_text) if nlp is not None else clean_text

    vin = extract_vin(clean_text)
    year = extract_year(clean_text)
    make, model, fuzzy_corrections = extract_make_and_model(doc)
    dtc_codes = extract_dtc_codes(clean_text)
    damaged_parts = extract_damaged_parts(doc)

    canonical_query = normalize_mechanic_notes(clean_text)
    dtc_hierarchy = resolve_dtc_hierarchy(dtc_codes)

    # Fallback defaults if text did not specify
    return {
        "vin": vin,
        "make": make or "Honda",
        "model": model or "Civic",
        "year": year or 2019,
        "dtc_codes": dtc_codes,
        "damaged_parts": damaged_parts,
        "canonical_query": canonical_query,
        "dtc_hierarchy": dtc_hierarchy,
        "fuzzy_corrections": fuzzy_corrections
    }
