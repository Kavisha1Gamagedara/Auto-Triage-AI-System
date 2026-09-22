import asyncio
from models import DiagnosticRequest, Agent1Payload, VehicleDetails
from nlp_extractor import (
    extract_entities, 
    sanitize_input, 
    extract_dtc_codes, 
    extract_year, 
    extract_vin,
    resolve_dtc_hierarchy, 
    normalize_mechanic_notes
)
from nhtsa_validator import (
    verify_vehicle, 
    decode_vin_nhtsa, 
    validate_vin_checksum
)


async def test_extraction_cases():
    print("=== [1] Testing Multi-Vehicle spaCy NLP Extraction ===")

    test_cases = [
        {
            "input": "2019 Honda Civic with trouble code P0171 running rough and check engine light",
            "expected_make": "Honda",
            "expected_model": "Civic",
            "expected_year": 2019,
            "expected_dtc": "P0171"
        },
        {
            "input": "Technician note: 2017 Ford F-150 misfiring on acceleration code P0300 with cracked spark plug",
            "expected_make": "Ford",
            "expected_model": "F-150",
            "expected_year": 2017,
            "expected_dtc": "P0300",
            "expected_part": "spark plug"
        },
        {
            "input": "Customer brought in 2021 Toyota Camry showing code P0420 and damaged catalytic converter",
            "expected_make": "Toyota",
            "expected_model": "Camry",
            "expected_year": 2021,
            "expected_dtc": "P0420",
            "expected_part": "catalytic converter"
        },
        {
            "input": "2019 Honda Civic with crashed bumper",
            "expected_make": "Honda",
            "expected_model": "Civic",
            "expected_year": 2019,
            "expected_dtc": None,
            "expected_part": "bumper"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        clean = sanitize_input(case["input"])
        extracted = extract_entities(clean)
        print(f"\nCase {i}: '{case['input']}'")
        print(f"  -> Extracted: Year={extracted['year']}, Make={extracted['make']}, Model={extracted['model']}, DTCs={extracted['dtc_codes']}, Parts={extracted['damaged_parts']}")

        assert extracted["make"] == case["expected_make"], f"Expected {case['expected_make']}, got {extracted['make']}"
        assert extracted["model"] == case["expected_model"], f"Expected {case['expected_model']}, got {extracted['model']}"
        if case.get("expected_dtc"):
            assert case["expected_dtc"] in extracted["dtc_codes"], f"Expected DTC {case['expected_dtc']} in {extracted['dtc_codes']}"

        if "expected_part" in case:
            assert case["expected_part"] in extracted["damaged_parts"], f"Expected part '{case['expected_part']}' in {extracted['damaged_parts']}"

    print("\nExtraction Test Cases: ALL PASSED!")


async def test_nhtsa_and_payloads():
    print("\n=== [2] Testing NHTSA Validation & Pydantic Payloads ===")

    # Test Ford F-150 validation with US DOT
    print("Verifying 2017 Ford F-150 against NHTSA...")
    is_f150_valid = await verify_vehicle("Ford", "F-150", 2017)
    print(f"2017 Ford F-150 valid? {is_f150_valid}")
    assert is_f150_valid is True, "Expected 2017 Ford F-150 to be valid in NHTSA"

    # Test Toyota Camry validation with US DOT
    print("Verifying 2021 Toyota Camry against NHTSA...")
    is_camry_valid = await verify_vehicle("Toyota", "Camry", 2021)
    print(f"2021 Toyota Camry valid? {is_camry_valid}")
    assert is_camry_valid is True, "Expected 2021 Toyota Camry to be valid in NHTSA"

    # Test Fictitious vehicle validation
    print("Verifying non-existent vehicle (2025 Ford GalaxyCruiser9000)...")
    is_bogus_valid = await verify_vehicle("Ford", "GalaxyCruiser9000", 2025)
    print(f"GalaxyCruiser9000 valid? {is_bogus_valid}")
    assert is_bogus_valid is False, "Expected non-existent vehicle to be rejected"

    # Build Agent 1 Payload
    hierarchy = resolve_dtc_hierarchy(["P0301"])
    canonical = normalize_mechanic_notes("rough idle when cold, shuddering and smells like fuel")
    payload = Agent1Payload(
        session_id="sess_live_123",
        vehicle_details=VehicleDetails(
            make="Ford",
            model="F-150",
            year=2017,
            is_verified=True
        ),
        dtc_codes=["P0301"],
        damaged_parts=["spark plug"],
        user_note="rough idle when cold, shuddering and smells like fuel",
        canonical_query=canonical,
        dtc_hierarchy=hierarchy
    )
    print("\nVerified Agent 1 A2A Payload with Hierarchical DTC and Normalized Query:")
    print(payload.model_dump_json(indent=2))

    assert payload.canonical_query is not None
    assert "misfire" in payload.canonical_query
    assert payload.dtc_hierarchy[0].family_code == "P0300"
    assert payload.dtc_hierarchy[0].system == "Powertrain"

    print("\nNHTSA & Payload Verification: ALL PASSED!")


async def test_ir_query_and_dtc_hierarchy():
    print("\n=== [3] Testing IR Query Processing & DTC Code Taxonomy ===")
    
    # Test 1: Mechanic Note Normalization & Synonym Expansion
    test_note = "Customer reports violent shuddering, hesitates on acceleration, car smells like gas"
    canonical = normalize_mechanic_notes(test_note)
    print(f"Raw Note: '{test_note}'")
    print(f"Canonical IR Query: '{canonical}'")
    assert "misfire" in canonical, "Expected 'misfire' expansion from 'shuddering'"
    assert "gas" not in canonical or "fuel vapor leak" in canonical, "Expected synonym expansion for fuel odor"

    # Test 2: DTC Hierarchy Fallback (P0301 -> P0300 family, P0171 -> P0100 family)
    hierarchy = resolve_dtc_hierarchy(["P0301", "P0171", "C0123"])
    print(f"\nDTC Hierarchy Output:")
    for h in hierarchy:
        print(f"  {h['exact_code']} -> Family: {h['family_code']} ({h['family_name']}) | System: {h['system']}")

    assert hierarchy[0]["exact_code"] == "P0301"
    assert hierarchy[0]["family_code"] == "P0300"
    assert hierarchy[0]["system"] == "Powertrain"
    assert hierarchy[1]["exact_code"] == "P0171"
    assert hierarchy[1]["family_code"] == "P0100"
    assert hierarchy[2]["system"] == "Chassis"

    print("\nIR Query Processing & DTC Hierarchy Tests: ALL PASSED!")


async def test_vin_decoding():
    print("\n=== [4] Testing ISO 3779 VIN Checksum & NHTSA Decoder ===")

    # Test 1: Offline MOD-11 Checksum Validation
    valid_vin = "1HGCR2F85HA000000"  # Real Honda Accord VIN with calculated 9th check digit 5
    invalid_vin = "1HGCR2F89HA000000"  # Checksum mismatch
    illegal_vin = "1HGCR2F85HI000000"  # Contains illegal character 'I'

    check_valid = validate_vin_checksum(valid_vin)
    print(f"Valid VIN ({valid_vin}) check: valid={check_valid['is_valid']}, check_digit={check_valid['actual_check_digit']}")
    assert check_valid["is_valid"] is True

    check_invalid = validate_vin_checksum(invalid_vin)
    print(f"Invalid VIN ({invalid_vin}) check: valid={check_invalid['is_valid']}, error={check_invalid['error']}")
    assert check_invalid["is_valid"] is False

    check_illegal = validate_vin_checksum(illegal_vin)
    print(f"Illegal VIN ({illegal_vin}) check: valid={check_illegal['is_valid']}, error={check_illegal['error']}")
    assert check_illegal["is_valid"] is False

    # Test 2: Online NHTSA VIN Decoder
    print(f"\nQuerying NHTSA to decode '{valid_vin}'...")
    decoded = await decode_vin_nhtsa(valid_vin)
    print(f"Decoded: Make={decoded.get('make')}, Model={decoded.get('model')}, Year={decoded.get('year')}, Engine={decoded.get('engine_displacement_l')}L, Fuel={decoded.get('fuel_type')}")
    assert decoded["success"] is True
    assert decoded["make"].upper() == "HONDA"
    assert "ACCORD" in decoded["model"].upper()
    assert decoded["year"] == 2017

    # Test 3: Unstructured text containing a VIN
    text_with_vin = "Technician scan on VIN 1HGCR2F85HA000000 showing rough idling and code P0301"
    extracted_vin = extract_vin(text_with_vin)
    assert extracted_vin == valid_vin

    print("\nVIN Checksum & NHTSA Decoder Tests: ALL PASSED!")


async def main():
    await test_extraction_cases()
    await test_nhtsa_and_payloads()
    await test_ir_query_and_dtc_hierarchy()
    await test_vin_decoding()
    print("\n==========================================")
    print("ALL AGENT 1 NLP & INTEGRATION TESTS PASSED!")
    print("==========================================")


if __name__ == "__main__":
    asyncio.run(main())
