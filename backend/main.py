from importlib import import_module
import groq

# Load FastAPI dynamically so static analyzers do not report an unresolved
# direct import when the selected interpreter does not expose the package.
FastAPI = import_module("fastapi").FastAPI
HTTPException = import_module("fastapi").HTTPException
from models import Agent1Payload, DiagnosticResult
from agent2_logic import deduce_root_cause


app = FastAPI(title="Auto-Triage Agent 2")

@app.post("/api/v1/diagnose", response_model=DiagnosticResult)
async def run_diagnostics(payload: Agent1Payload) :
     #Process the payload through the cognitive engine
     try:
         result = deduce_root_cause(payload)
     except groq.APIStatusError as e:
         raise HTTPException(status_code=500, detail=f"Groq API error: {e}")
     return result             