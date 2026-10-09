"""
Sri Lankan Vehicle Registration (Number Plate) Validator & Parser.
Implements deterministic statutory rules governed by the Sri Lanka Motor Traffic Act:

1. Provincial Council Prefixes (9 Official Codes):
   - WP: Western Province (බස්නාහිර / மேல்)
   - CP: Central Province (මධ්‍යම / மத்திய)
   - SP: Southern Province (දකුණ / தென்)
   - NP: Northern Province (උතුරු / வட)
   - EP: Eastern Province (නැගෙනහිර / கிழக்கு)
   - NW: North Western Province (වයඹ / வடமேல்)
   - NC: North Central Province (උතුරු මැද / வடமத்திய)
   - SG: Sabaragamuwa Province (සබරගමුව / சப்ரகமுவ)
   - UP: Uva Province (ඌව / ஊவா)

2. Forbidden Letters Rule (DMT / RMV Standard):
   - The Department of Motor Traffic strictly bans 'I', 'O', and 'Q'
     from series letters to prevent optical confusion with '1' and '0'.

3. Statutory Vehicle Class (First Letter Rule of 3-letter series):
   - C: Motor Cars / Station Wagons / SUVs (e.g. CAA - CBZ)
   - D: Dual-Purpose Vehicles / Light Commercial Vans (e.g. DAA - DBZ)
   - B: Motorcycles / Motor Tricycles (e.g. BAA - BCZ)
   - A: Three-Wheelers (Tuk-Tuks) (e.g. AAA - ACZ)
   - L: Lorries / Heavy Commercial Trucks (e.g. LAA - LBZ)
   - N: Omnibuses / Passenger Buses (e.g. NAA - NBZ)
   - P: Prime Movers / Heavy Machinery (e.g. PAA - PBZ)
   - R: Land Vehicles / Agricultural Tractors (e.g. RAA - RBZ)
   - V: Trailers / Semi-Trailers
   - E: Electric / Alternative Fuel Series

4. Historical & Special Formats:
   - Modern 3-letter: [Province] [AAA]-[####] (e.g. WP CAB-1234)
   - Modern 2-letter: [Province] [AA]-[####]  (e.g. WP GA-1234, CP KA-5678)
   - Vintage "Sri" series: ## SRI #### / ## ශ්‍රී #### (e.g. 14 SRI 1234)
   - Vintage Numeric: ##-#### / ###-#### (e.g. 65-1234, 301-5678)
"""

import re
from typing import Dict, Any, Optional, Tuple, List

# Official 9 Sri Lankan Provincial Council codes
SL_PROVINCES: Dict[str, Dict[str, str]] = {
    "WP": {"name_en": "Western Province", "name_si": "බස්නාහිර", "capital": "Colombo"},
    "CP": {"name_en": "Central Province", "name_si": "මධ්‍යම", "capital": "Kandy"},
    "SP": {"name_en": "Southern Province", "name_si": "දකුණ", "capital": "Galle"},
    "NP": {"name_en": "Northern Province", "name_si": "උතුරු", "capital": "Jaffna"},
    "EP": {"name_en": "Eastern Province", "name_si": "නැගෙනහිර", "capital": "Trincomalee"},
    "NW": {"name_en": "North Western Province", "name_si": "වයඹ", "capital": "Kurunegala"},
    "NC": {"name_en": "North Central Province", "name_si": "උතුරු මැද", "capital": "Anuradhapura"},
    "SG": {"name_en": "Sabaragamuwa Province", "name_si": "සබරගමුව", "capital": "Ratnapura"},
    "UP": {"name_en": "Uva Province", "name_si": "ඌව", "capital": "Badulla"},
}

# Forbidden characters by DMT regulations
FORBIDDEN_LETTERS: set = {"I", "O", "Q"}

# DMT Statutory Vehicle Class assignments by first letter of 3-letter series
VEHICLE_CLASS_MAP: Dict[str, Dict[str, Any]] = {
    "C": {
        "class_name": "Motor Car / Station Wagon / SUV",
        "description": "Private Passenger Motor Car, Station Wagon, or SUV",
        "typical_models": ["Toyota Aqua", "Honda Vezel", "Toyota Prius", "Toyota Premio", "Toyota Axio", "Suzuki Swift", "Toyota Vitz"],
        "is_car": True,
        "is_motorcycle": False,
        "is_three_wheeler": False,
        "is_van": False,
        "is_heavy": False
    },
    "D": {
        "class_name": "Dual-Purpose Vehicle / Light Commercial Van",
        "description": "Light Commercial Passenger/Cargo Van or Double Cab",
        "typical_models": ["Toyota HiAce", "Nissan Caravan", "Toyota TownAce", "Mazda Bongo", "Toyota Hilux Double Cab"],
        "is_car": False,
        "is_motorcycle": False,
        "is_three_wheeler": False,
        "is_van": True,
        "is_heavy": False
    },
    "B": {
        "class_name": "Motorcycle / Motor Tricycle",
        "description": "Two-Wheel Motor Bicycle / Motorcycle",
        "typical_models": ["Honda Dio", "Yamaha FZ", "Bajaj Pulsar", "TVS Apache", "Hero Dash", "Honda CB Hornet"],
        "is_car": False,
        "is_motorcycle": True,
        "is_three_wheeler": False,
        "is_van": False,
        "is_heavy": False
    },
    "A": {
        "class_name": "Three-Wheeler (Tuk-Tuk)",
        "description": "Three-Wheeled Passenger Light Vehicle",
        "typical_models": ["Bajaj RE", "TVS King", "Piaggio Ape", "Mahindra Alfa"],
        "is_car": False,
        "is_motorcycle": False,
        "is_three_wheeler": True,
        "is_van": False,
        "is_heavy": False
    },
    "L": {
        "class_name": "Lorry / Heavy Goods Commercial",
        "description": "Medium to Heavy Goods Vehicle / Truck",
        "typical_models": ["Isuzu Elf", "Mitsubishi Canter", "Tata 407", "Hino Dutro", "Ashok Leyland Ecomet"],
        "is_car": False,
        "is_motorcycle": False,
        "is_three_wheeler": False,
        "is_van": False,
        "is_heavy": True
    },
    "N": {
        "class_name": "Omnibus / Passenger Bus",
        "description": "Heavy Passenger Transport Bus",
        "typical_models": ["Ashok Leyland Viking", "Mitsubishi Rosa", "Toyota Coaster", "Tata Marcopolo"],
        "is_car": False,
        "is_motorcycle": False,
        "is_three_wheeler": False,
        "is_van": False,
        "is_heavy": True
    },
    "P": {
        "class_name": "Prime Mover / Heavy Machinery",
        "description": "Articulated Vehicle or Heavy Industrial Equipment",
        "typical_models": ["CAT Excavator", "Komatsu", "Volvo Prime Mover", "JCB Backhoe"],
        "is_car": False,
        "is_motorcycle": False,
        "is_three_wheeler": False,
        "is_van": False,
        "is_heavy": True
    },
    "R": {
        "class_name": "Agricultural Tractor / Land Vehicle",
        "description": "Two-wheel or Four-wheel Agricultural Tractor",
        "typical_models": ["Massey Ferguson", "Tafe", "Land Master", "Kubota"],
        "is_car": False,
        "is_motorcycle": False,
        "is_three_wheeler": False,
        "is_van": False,
        "is_heavy": False
    },
    "V": {
        "class_name": "Trailer / Semi-Trailer",
        "description": "Towed Non-Powered Transport Unit",
        "typical_models": ["Commercial Container Trailer", "Agricultural Trailer"],
        "is_car": False,
        "is_motorcycle": False,
        "is_three_wheeler": False,
        "is_van": False,
        "is_heavy": True
    },
    "E": {
        "class_name": "Electric / Alternative Fuel",
        "description": "Dedicated Zero-Emission / Special Electric Allocation",
        "typical_models": ["Nissan Leaf", "Tesla Model 3", "BYD Atto 3", "MG ZS EV"],
        "is_car": True,
        "is_motorcycle": False,
        "is_three_wheeler": False,
        "is_van": False,
        "is_heavy": False
    }
}

# 1. Candidate Provincial 3-letter: e.g. "WP CAB-1234", "XP CAB-1234"
PATTERN_ANY_PROVINCIAL_3L = re.compile(
    r"\b([A-Z]{2})\s*[-/ ]?\s*([A-Z]{3})\s*[- ]?\s*([0-9]{4})\b",
    re.IGNORECASE
)

# 2. Candidate Provincial 2-letter: e.g. "WP GA-1234", "ZZ GA-1234"
PATTERN_ANY_PROVINCIAL_2L = re.compile(
    r"\b([A-Z]{2})\s*[-/ ]?\s*([A-Z]{2})\s*[- ]?\s*([0-9]{4})\b",
    re.IGNORECASE
)

# 3. Standalone 3-letter series without province: e.g. "CAB-1234"
PATTERN_SERIES_3L_STANDALONE = re.compile(
    r"\b([A-Z]{3})\s*[- ]\s*([0-9]{4})\b",
    re.IGNORECASE
)

# 4. Standalone 2-letter English series without province: e.g. "GA-1234", "HA-5678"
PATTERN_SERIES_2L_STANDALONE = re.compile(
    r"\b([A-Z]{2})\s*[- ]\s*([0-9]{4})\b",
    re.IGNORECASE
)

# 5. Vintage Sri series: e.g. "14 SRI 1234" or "32-SRI-5678"
PATTERN_SRI_SERIES = re.compile(
    r"\b([0-9]{1,3})\s*[-/ ]?\s*(?:SRI|ශ්‍රී)\s*[-/ ]?\s*([0-9]{4})\b",
    re.IGNORECASE
)

# 6. Vintage Numeric: e.g. "65-1234", "301-5678", "19-1234"
PATTERN_VINTAGE_NUMERIC = re.compile(
    r"\b([0-9]{2,3})\s*[-]\s*([0-9]{4})\b"
)


def extract_sri_lankan_plate(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts a Sri Lankan vehicle registration plate from raw technician/customer text.
    Returns normalized parsed tokens or None if not found.
    """
    if not text or not isinstance(text, str):
        return None

    clean_text = text.strip()

    # 1. Match Candidate 3-letter with Province prefix (e.g. WP CAB-1234 or XP CAB-1234)
    m = PATTERN_ANY_PROVINCIAL_3L.search(clean_text)
    if m:
        prov = m.group(1).upper()
        series = m.group(2).upper()
        num = m.group(3)
        return validate_plate_components(province=prov, series=series, number=num, format_era="modern_3letter")

    # 2. Match Candidate 2-letter with Province prefix (e.g. WP GA-1234 or ZZ GA-1234)
    m = PATTERN_ANY_PROVINCIAL_2L.search(clean_text)
    if m:
        prov = m.group(1).upper()
        series = m.group(2).upper()
        num = m.group(3)
        return validate_plate_components(province=prov, series=series, number=num, format_era="modern_2letter")


    # 3. Match Standalone 3-letter series (e.g. CAB-1234)
    m = PATTERN_SERIES_3L_STANDALONE.search(clean_text)
    if m:
        series = m.group(1).upper()
        num = m.group(2)
        # Avoid false positives with common acronyms or DTC codes (e.g. DTC-1234 is not a plate)
        if series not in {"DTC", "RPM", "MAF", "OBD", "VIN", "ECU", "PCM", "ABS"}:
            return validate_plate_components(province=None, series=series, number=num, format_era="modern_3letter")

    # 4. Match Sri Series (e.g. 14 SRI 1234)
    m = PATTERN_SRI_SERIES.search(clean_text)
    if m:
        prefix = m.group(1)
        num = m.group(2)
        clean_plate = f"{prefix} SRI {num}"
        return {
            "is_valid": True,
            "plate_number": clean_plate,
            "raw_match": m.group(0),
            "format_era": "vintage_sri_series",
            "province_code": None,
            "province_name": None,
            "series": f"{prefix} SRI",
            "number": num,
            "class_letter": None,
            "statutory_class": "Classic / Vintage Sri Series",
            "is_motor_car": True,
            "forbidden_letters": [],
            "validation_status": "VALID_SRI_SERIES",
            "status_message": f"Historical Sri Lanka 'Sri' Era Registration ({clean_plate})"
        }

    # 5. Match Vintage Numeric (e.g. 65-1234, 19-5678)
    m = PATTERN_VINTAGE_NUMERIC.search(clean_text)
    if m:
        prefix = m.group(1)
        num = m.group(2)
        clean_plate = f"{prefix}-{num}"
        return {
            "is_valid": True,
            "plate_number": clean_plate,
            "raw_match": m.group(0),
            "format_era": "vintage_numeric",
            "province_code": None,
            "province_name": None,
            "series": prefix,
            "number": num,
            "class_letter": None,
            "statutory_class": "Vintage / Pre-Sri Series",
            "is_motor_car": True,
            "forbidden_letters": [],
            "validation_status": "VALID_VINTAGE_NUMERIC",
            "status_message": f"Vintage Sri Lanka Numeric Registration ({clean_plate})"
        }

    return None


def validate_plate_components(
    province: Optional[str],
    series: str,
    number: str,
    format_era: str
) -> Dict[str, Any]:
    """
    Performs deterministic statutory validation against Motor Traffic Act rules.
    """
    series_clean = series.strip().upper()
    prov_clean = province.strip().upper() if province else None
    num_clean = number.strip()

    plate_str = f"{prov_clean + ' ' if prov_clean else ''}{series_clean}-{num_clean}"
    
    # Check 1: Province Code Validation
    prov_data = SL_PROVINCES.get(prov_clean) if prov_clean else None
    if prov_clean and not prov_data:
        return {
            "is_valid": False,
            "plate_number": plate_str,
            "format_era": format_era,
            "province_code": prov_clean,
            "province_name": "Unknown / Invalid Province",
            "series": series_clean,
            "number": num_clean,
            "class_letter": None,
            "statutory_class": "Invalid",
            "is_motor_car": False,
            "forbidden_letters": [],
            "validation_status": "INVALID_PROVINCE",
            "status_message": f"❌ Invalid Province Code '{prov_clean}'. Must be one of the 9 official Provincial Councils: {', '.join(SL_PROVINCES.keys())}"
        }

    # Check 2: Forbidden Letters Rule (DMT standard: no 'I', 'O', 'Q')
    found_forbidden = [ch for ch in series_clean if ch in FORBIDDEN_LETTERS]
    if found_forbidden:
        return {
            "is_valid": False,
            "plate_number": plate_str,
            "format_era": format_era,
            "province_code": prov_clean,
            "province_name": prov_data["name_en"] if prov_data else None,
            "series": series_clean,
            "number": num_clean,
            "class_letter": series_clean[0],
            "statutory_class": "Rejected by DMT Rules",
            "is_motor_car": False,
            "forbidden_letters": found_forbidden,
            "validation_status": "FORBIDDEN_LETTERS_DETECTED",
            "status_message": f"❌ Invalid Plate: Letters {', '.join(found_forbidden)} are prohibited by Sri Lanka DMT (to avoid optical confusion with numbers '1' and '0')."
        }

    # Check 3: Vehicle Class Category (First Letter of 3-letter series)
    class_letter = series_clean[0] if len(series_clean) == 3 else None
    class_meta = VEHICLE_CLASS_MAP.get(class_letter) if class_letter else None

    statutory_class = class_meta["class_name"] if class_meta else "General Passenger Vehicle (2-letter Series)"
    is_motor_car = class_meta["is_car"] if class_meta else True

    prov_label = f"{prov_data['name_en']} ({prov_clean})" if prov_data else "National Series"

    return {
        "is_valid": True,
        "plate_number": plate_str,
        "format_era": format_era,
        "province_code": prov_clean,
        "province_name": prov_data["name_en"] if prov_data else None,
        "province_capital": prov_data["capital"] if prov_data else None,
        "series": series_clean,
        "number": num_clean,
        "class_letter": class_letter,
        "statutory_class": statutory_class,
        "is_motor_car": is_motor_car,
        "forbidden_letters": [],
        "validation_status": "VALID_SRI_LANKAN_PLATE",
        "status_message": f"✓ Valid {prov_label} {statutory_class} Registration ({plate_str})"
    }


def verify_plate_vehicle_compatibility(plate_info: Dict[str, Any], make: str, model: str) -> Dict[str, Any]:
    """
    Checks if the entered vehicle body type aligns with the statutory plate class category.
    E.g. If series is 'BAF' (Motorcycle) but vehicle is 'Toyota Aqua' (Motor Car), issues a warning.
    """
    if not plate_info or not plate_info.get("is_valid"):
        return {"is_compatible": True, "warning": None}

    class_letter = plate_info.get("class_letter")
    if not class_letter:
        return {"is_compatible": True, "warning": None}

    clean_make = (make or "").strip().lower()
    clean_model = (model or "").strip().lower()

    # Known Motorcycles
    is_bike = any(b in clean_model for b in ["dio", "pulsar", "fz", "apache", "dash", "hornet", "ct100", "gn125", "cbf"])
    # Known Three-Wheelers
    is_tuk = any(t in clean_model for t in ["tuk", "three wheeler", "three-wheeler", "re", "king", "ape", "alfa"])
    # Known Vans
    is_van = any(v in clean_model for v in ["hiace", "caravan", "townace", "bongo", "vanette", "every"])
    # Known Lorries / Trucks
    is_truck = any(l in clean_model for l in ["elf", "canter", "dutro", "407", "ecomet", "lorry", "truck"])

    # 1. Motorcycle Series (B) assigned to a Car
    if class_letter == "B" and not is_bike:
        return {
            "is_compatible": False,
            "warning": f"⚠️ Vehicle Class Mismatch: Series '{plate_info['series']}' is strictly assigned to Motorcycles/Two-Wheelers in Sri Lanka, but vehicle specified is '{make} {model}'."
        }

    # 2. Three-Wheeler Series (A) assigned to a Car
    if class_letter == "A" and not is_tuk:
        return {
            "is_compatible": False,
            "warning": f"⚠️ Vehicle Class Mismatch: Series '{plate_info['series']}' is strictly assigned to Three-Wheelers (Tuk-Tuks) in Sri Lanka, but vehicle specified is '{make} {model}'."
        }

    # 3. Car Series (C) assigned to a Motorcycle or Tuk-Tuk
    if class_letter == "C" and (is_bike or is_tuk):
        return {
            "is_compatible": False,
            "warning": f"⚠️ Vehicle Class Mismatch: Series '{plate_info['series']}' is strictly assigned to Motor Cars / SUVs, but vehicle specified is a two/three-wheeler '{make} {model}'."
        }

    return {"is_compatible": True, "warning": None}
