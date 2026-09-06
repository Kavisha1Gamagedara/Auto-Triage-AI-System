import logging
from typing import Optional
import httpx

logger = logging.getLogger("nhtsa_validator")
NHTSA_BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear"


async def verify_vehicle(make: str, model: str, year: int, timeout_seconds: float = 10.0) -> bool:
    """
    Queries the U.S. DOT NHTSA vPIC API to verify if a make/model/year combination exists.

    Args:
        make: Vehicle manufacturer (e.g., 'Honda', 'Toyota', 'Ford').
        model: Vehicle model name (e.g., 'Civic', 'Camry', 'F-150').
        year: Vehicle model year (e.g., 2019).
        timeout_seconds: Request timeout duration in seconds.

    Returns:
        bool: True if vehicle model exists in the official NHTSA database for that year, False otherwise.
    """
    cleaned_make = make.strip().lower()
    cleaned_model = model.strip().lower()

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

        # Match exact model name or model contained as primary token
        is_match = any(
            cleaned_model == official or cleaned_model in official.split()
            for official in official_models
        )

        if is_match:
            logger.info(f"NHTSA verified vehicle: {year} {make} {model}")
        else:
            logger.warning(f"Vehicle model '{model}' not found among official models: {official_models[:5]}...")

        return is_match

    except httpx.RequestError as exc:
        logger.error(f"Network error querying NHTSA API: {exc}")
        return False
    except Exception as exc:
        logger.error(f"Unexpected error validating vehicle with NHTSA: {exc}")
        return False
