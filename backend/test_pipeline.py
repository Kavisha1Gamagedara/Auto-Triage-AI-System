import asyncio
from models import DiagnosticRequest, Agent1Payload, VehicleDetails
from nlp_extractor import extract_entities, sanitize_input, extract_dtc_codes, extract_year
from nhtsa_validator import verify_vehicle


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
    payload = Agent1Payload(
        session_id="sess_live_123",
        vehicle_details=VehicleDetails(
            make="Ford",
            model="F-150",
            year=2017,
            is_verified=True
        ),
        dtc_codes=["P0300"],
        damaged_parts=["spark plug"]
    )
    print("\nVerified Agent 1 A2A Payload:")
    print(payload.model_dump_json(indent=2))

    print("\nNHTSA & Payload Verification: ALL PASSED!")


async def main():
    await test_extraction_cases()
    await test_nhtsa_and_payloads()
    print("\n==========================================")
    print("ALL AGENT 1 NLP & INTEGRATION TESTS PASSED!")
    print("==========================================")


if __name__ == "__main__":
    asyncio.run(main())
