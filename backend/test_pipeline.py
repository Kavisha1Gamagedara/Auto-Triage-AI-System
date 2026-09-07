import asyncio
from models import DiagnosticRequest, Agent1Payload, VehicleDetails
from nlp_extractor import extract_entities, sanitize_input
from nhtsa_validator import verify_vehicle


async def run_smoke_tests():
    print("=== [1] Testing Sanitization & Extraction ===")
    sample_text = "  2019 Honda Civic with trouble code P0171 running rough \x00\x1f  "
    clean = sanitize_input(sample_text)
    print(f"Sanitized input: '{clean}'")
    assert "\x00" not in clean, "Sanitization failed to strip null bytes"

    extracted = extract_entities(clean)
    print(f"Extracted entities: {extracted}")
    assert extracted["make"] == "Honda"
    assert "P0171" in extracted["dtc_codes"]
    print("Extraction & Sanitization: PASSED")

    print("\n=== [2] Testing Pydantic Schemas ===")
    req = DiagnosticRequest(session_id="test_sess_001", raw_text=clean)
    assert req.session_id == "test_sess_001"

    payload = Agent1Payload(
        session_id=req.session_id,
        vehicle_details=VehicleDetails(
            make=extracted["make"],
            model=extracted["model"],
            year=extracted["year"],
            is_verified=True
        ),
        dtc_codes=extracted["dtc_codes"],
        damaged_parts=[]
    )
    print(f"Serialized Agent 1 Payload: {payload.model_dump_json(indent=2)}")
    print("Pydantic Models: PASSED")

    print("\n=== [3] Testing NHTSA vPIC External Validator ===")
    # Valid vehicle
    print("Testing valid vehicle (2019 Honda Civic)...")
    valid_res = await verify_vehicle("Honda", "Civic", 2019)
    print(f"2019 Honda Civic valid? {valid_res}")
    assert valid_res is True, "Expected 2019 Honda Civic to be verified by NHTSA"

    # Invalid vehicle
    print("Testing invalid vehicle (2019 Honda FalconX99)...")
    invalid_res = await verify_vehicle("Honda", "FalconX99", 2019)
    print(f"2019 Honda FalconX99 valid? {invalid_res}")
    assert invalid_res is False, "Expected fictitious vehicle to fail verification"
    print("NHTSA Verification: PASSED")

    print("\nALL BACKEND UNIT TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_smoke_tests())
