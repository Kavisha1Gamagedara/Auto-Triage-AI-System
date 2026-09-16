import requests
import json

# The local URL for your Agent 2 FastAPI server
URL = "http://127.0.0.1:8000/api/v1/diagnose"

# A mock JSON payload formatted exactly as Agent 1 would send it
mock_payload = {
    "session_id": "MID-EVAL-TEST-001",
    "vehicle": {
        "make": "Toyota",
        "model": "Townace",
        "year": 1995
    },
    "dtc_codes": ["P0251"],
    "user_note": "Engine lacks power and stalls. Suspected fuel delivery issue or injection pump timing fault on the 1C engine."
}

try:
    print("Sending mock payload to Agent 2...")
    response = requests.post(URL, json=mock_payload)
    response.raise_for_status()
    
    print("\n✅ Success! Agent 2 Output:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.ConnectionError:
    print("\n[ERROR] Connection refused. Is your FastAPI server running on port 8000?")
except requests.exceptions.HTTPError:
    print(f"\n[HTTP {response.status_code} Error from Agent 2]:\n{response.text}")