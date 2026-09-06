# Auto-Triage AI

A multi-agent automotive triage and procurement system. The platform ingests unstructured mechanic or driver complaints, parses vehicle details and DTC codes, validates vehicle existence against official databases, performs diagnostic reasoning, and looks up repair manuals and replacement parts in parallel.

## System Design

The project uses a Fork-Join multi-agent workflow orchestrated with LangGraph and exposed through a FastAPI backend.

```
[ Frontend / Client ]
         │
         ▼
[ Agent 1: Ingestion Gateway ]
         │ (Validated A2A payload)
         ▼
[ Agent 2: Diagnostic Reasoning ]
         │
    ┌────┴────┐ (Parallel Fork)
    ▼         ▼
[ Agent 3 ] [ Agent 4 ]
Repair RAG  Procurement
    └────┬────┘ (Join)
         ▼
[ Final Triage & Parts Report ]
```

### The 4 Agents

- **Agent 1 (Ingestion & Validation)**: Acts as the entry gateway. Sanitizes incoming text against prompt injection, runs NLP/NER to pull Make, Model, Year, and DTC codes, and queries the NHTSA vPIC API to confirm the vehicle exists.
- **Agent 2 (Diagnostic Reasoning)**: Analyzes DTC codes and reported symptoms to determine the mechanical root cause and severity rating.
- **Agent 3 (Technical Repair RAG)**: Queries vector storage (ChromaDB) containing OEM repair manuals to generate step-by-step repair guides with citations.
- **Agent 4 (Procurement & Pricing)**: Queries a MongoDB parts catalog to find matching OEM and aftermarket part numbers and approximate local prices.

## Repository Layout

```
Auto-Triage-AI/
├── backend/
│   ├── main.py              # FastAPI entrypoint and routes
│   ├── models.py            # Pydantic schemas for requests and A2A contracts
│   ├── nhtsa_validator.py   # Async NHTSA vPIC API client
│   ├── nlp_extractor.py     # Entity extraction and input sanitization
│   ├── test_pipeline.py     # Local smoke tests
│   └── requirements.txt     # Backend dependencies
├── .gitignore
└── README.md
```

## Setup & Local Development

### 1. Prerequisites
- Python 3.10 or newer
- Git

### 2. Create and Activate Virtual Environment

Windows (PowerShell):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Linux / macOS:
```bash
cd backend
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Run the Dev Server
```bash
uvicorn main:app --reload --port 8000
```

Once running, interactive docs are available at `http://localhost:8000/docs`.

### 5. Run Smoke Tests
```bash
python test_pipeline.py
```

## API Endpoints (Agent 1)

### `GET /api/health`
Returns service status.

Response:
```json
{
  "status": "healthy",
  "agent": "Agent 1 (Ingestion & Validation)"
}
```

### `POST /api/v1/ingest`
Ingests raw diagnostic text, extracts vehicle parameters and DTC codes, verifies vehicle data with NHTSA, and returns the payload for Agent 2.

Sample Request:
```json
{
  "session_id": "sess_001",
  "raw_text": "2019 Honda Civic threw code P0171 and is running lean."
}
```

Sample Response:
```json
{
  "session_id": "sess_001",
  "vehicle_details": {
    "make": "Honda",
    "model": "Civic",
    "year": 2019,
    "is_verified": true
  },
  "dtc_codes": ["P0171"],
  "damaged_parts": []
}
```
