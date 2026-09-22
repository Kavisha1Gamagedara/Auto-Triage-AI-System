import logging
from typing import Optional
import httpx

logger = logging.getLogger("nhtsa_validator")
NHTSA_BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear"


async def verify_vehicle(make: str, model: str, year: int, timeout_seconds: float = 10.0) -> bool:
    """
    Queries the U.S. DOT NHTSA vPIC API to verify if a make/model/year combination exists.
    Applies RapidFuzz approximate string matching to tolerate typos in user input.

    Args:
        make: Vehicle manufacturer (e.g., 'Honda', 'Toyota', 'Ford', 'Toyta').
        model: Vehicle model name (e.g., 'Civic', 'Camry', 'F-150', 'Commry').
        year: Vehicle model year (e.g., 2019).
        timeout_seconds: Request timeout duration in seconds.

    Returns:
        bool: True if vehicle model exists in the official NHTSA database for that year, False otherwise.
    """
    from nlp_extractor import fuzzy_correct_make, fuzzy_correct_model

    # Automatically normalize potential typos to canonical names
    canonical_make, _ = fuzzy_correct_make(make)
    canonical_model, _ = fuzzy_correct_model(model)

    cleaned_make = canonical_make.strip().lower()
    cleaned_model = canonical_model.strip().lower()

    url = f"{NHTSA_BASE_URL}/make/{cleaned_make}/modelyear/{year}?format=json"

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(url)

        if response.status_code != 200:
            logger.warning(
                f"NHTSA API returned status {response.status_code} for {year} {make} {model}"
            )
            return False

        data = response.json()
        results = data.get("Results", [])

        if not results:
            logger.info(f"No models found in NHTSA database for make '{make}' and year '{year}'")
            return False

        # Extract all official model names for this make/year
        official_models = [
            item.get("Model_Name", "").strip().lower()
            for item in results
            if item.get("Model_Name")
        ]

        # 1. Match exact model name or model contained as primary token
        is_match = any(
            cleaned_model == official or cleaned_model in official.split()
            for official in official_models
        )

        # 2. RapidFuzz approximate match against NHTSA official model list
        if not is_match and official_models and len(cleaned_model) >= 3:
            try:
                from rapidfuzz import fuzz, process, distance
                best_match, best_score, _ = process.extractOne(cleaned_model, official_models, scorer=fuzz.ratio)
                lev = distance.Levenshtein.distance(cleaned_model, best_match)
                if (lev <= 2 or best_score >= 85.0) and best_score >= 70.0:
                    logger.info(f"NHTSA fuzzy matched model '{model}' to official '{best_match}' (score: {best_score:.1f}%, lev: {lev})")
                    is_match = True
            except Exception as err:
                logger.debug(f"RapidFuzz model matching skipped: {err}")

        if is_match:
            logger.info(f"NHTSA verified vehicle: {year} {canonical_make} {canonical_model}")
        else:
            logger.warning(f"Vehicle model '{model}' not found among official models: {official_models[:5]}...")

        return is_match

    except httpx.RequestError as exc:
        logger.error(f"Network error querying NHTSA API: {exc}")
        # Fallback resilience: if external government API times out or is unreachable, allow known makes
        known_makes = {"honda", "toyota", "ford", "chevrolet", "nissan", "bmw", "mercedes-benz", "audi", "volkswagen", "hyundai", "kia", "subaru", "mazda", "dodge", "jeep", "ram", "chrysler", "lexus", "acura", "infiniti", "volvo", "porsche", "mitsubishi", "cadillac", "buick", "lincoln", "gmc", "tesla"}
        if cleaned_make in known_makes:
            logger.warning(f"NHTSA API unreachable, but '{make}' is a recognized manufacturer. Permitting vehicle.")
            return True
        return False
    except Exception as exc:
        logger.error(f"Unexpected error validating vehicle with NHTSA: {exc}")
        return False


# Standard ISO 3779 VIN Transliteration & Weight Constants
VIN_TRANSLITERATION = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9,
    'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9
}

VIN_POSITION_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


def validate_vin_checksum(raw_vin: str) -> dict:
    """
    Offline ISO 3779 standard 17-character VIN format and MOD-11 checksum validation.
    The 9th character is a calculated check digit.
    
    Returns:
        dict with:
            is_valid (bool),
            clean_vin (str),
            expected_check_digit (str),
            actual_check_digit (str),
            error (Optional[str])
    """
    if not raw_vin or not isinstance(raw_vin, str):
        return {"is_valid": False, "clean_vin": "", "error": "VIN is empty or invalid"}

    clean_vin = raw_vin.strip().upper()

    # Rule 1: Length must be exactly 17 characters
    if len(clean_vin) != 17:
        return {
            "is_valid": False,
            "clean_vin": clean_vin,
            "error": f"Invalid VIN length: {len(clean_vin)} characters (must be exactly 17)"
        }

    # Rule 2: Letters I, O, Q are strictly illegal in standard VINs to prevent confusion with numbers 1 and 0
    illegal_chars = [c for c in clean_vin if c in ('I', 'O', 'Q')]
    if illegal_chars:
        return {
            "is_valid": False,
            "clean_vin": clean_vin,
            "error": f"VIN contains illegal characters ({', '.join(set(illegal_chars))}). Standard VINs never use I, O, or Q."
        }

    # Rule 3: Must be alphanumeric
    if not clean_vin.isalnum():
        return {
            "is_valid": False,
            "clean_vin": clean_vin,
            "error": "VIN contains non-alphanumeric characters."
        }

    # Rule 4: MOD-11 Check Digit Algorithm
    try:
        total = 0
        for i in range(17):
            char = clean_vin[i]
            val = VIN_TRANSLITERATION[char] if char in VIN_TRANSLITERATION else int(char)
            total += val * VIN_POSITION_WEIGHTS[i]

        remainder = total % 11
        expected_check_digit = "X" if remainder == 10 else str(remainder)
        actual_check_digit = clean_vin[8]

        is_checksum_valid = (actual_check_digit == expected_check_digit)

        return {
            "is_valid": is_checksum_valid,
            "clean_vin": clean_vin,
            "expected_check_digit": expected_check_digit,
            "actual_check_digit": actual_check_digit,
            "error": None if is_checksum_valid else f"MOD-11 Checksum mismatch: expected '{expected_check_digit}', got '{actual_check_digit}'"
        }
    except Exception as e:
        return {
            "is_valid": False,
            "clean_vin": clean_vin,
            "error": f"Error calculating checksum: {e}"
        }


async def decode_vin_nhtsa(vin: str, timeout_seconds: float = 12.0) -> dict:
    """
    Decodes a 17-character VIN using the official U.S. DOT NHTSA vPIC API:
    https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json

    Returns:
        dict containing verified make, model, year, engine, fuel type, body class, and check status.
    """
    checksum_result = validate_vin_checksum(vin)
    clean_vin = checksum_result["clean_vin"]

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{clean_vin}?format=json"

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return {
                "success": False,
                "vin": clean_vin,
                "error": f"NHTSA server returned status code {response.status_code}",
                "checksum": checksum_result
            }

        data = response.json()
        results = data.get("Results", [])

        if not results:
            return {
                "success": False,
                "vin": clean_vin,
                "error": "No decoding data returned from NHTSA database",
                "checksum": checksum_result
            }

        rec = results[0]
        make = (rec.get("Make") or "").strip().title()
        model = (rec.get("Model") or "").strip()
        year_str = (rec.get("ModelYear") or "").strip()
        error_code = (rec.get("ErrorCode") or "").strip()
        error_text = (rec.get("ErrorText") or "").strip()

        # Check if year is valid integer
        year = int(year_str) if year_str.isdigit() else None

        if not make or not model or not year:
            return {
                "success": False,
                "vin": clean_vin,
                "error": f"VIN decoded with missing core attributes (Make: '{make}', Model: '{model}', Year: '{year_str}'). NHTSA note: {error_text}",
                "checksum": checksum_result
            }

        return {
            "success": True,
            "vin": clean_vin,
            "make": make,
            "model": model,
            "year": year,
            "engine_displacement_l": rec.get("DisplacementL") or None,
            "fuel_type": rec.get("FuelTypePrimary") or None,
            "drive_type": rec.get("DriveType") or None,
            "body_class": rec.get("BodyClass") or None,
            "plant_country": rec.get("PlantCountry") or None,
            "checksum": checksum_result,
            "nhtsa_error_code": error_code,
            "nhtsa_note": error_text
        }
    except Exception as exc:
        logger.error(f"Error decoding VIN '{clean_vin}' via NHTSA: {exc}")
        return {
            "success": False,
            "vin": clean_vin,
            "error": f"Network or decoding error: {exc}",
            "checksum": checksum_result
        }
