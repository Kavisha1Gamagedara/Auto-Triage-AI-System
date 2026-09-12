import json
import os
from dotenv import load_dotenv
from groq import Groq
from models import Agent1Payload, DiagnosticResult

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

RESULT_SCHEMA = json.dumps(DiagnosticResult.model_json_schema(), indent=2)

SYSTEM_PROMPT = f"""
You are an expert Master Auto Mechanic. Analyze the vehicle specifications, DTC codes, and user symptoms to deduce the SINGLE most likely physical component that has failed.
Evaluate the data logically: cross-reference electrical codes with physical symptoms to isolate the root cause. Do not guess blindly. Output the exact component name clearly so a parts database can search for it.

Respond with ONLY a valid JSON object - no markdown, no code fences, no extra text.
The JSON object must match this JSON schema exactly, using these exact field names:
{RESULT_SCHEMA}
"""

def deduce_root_cause(payload: Agent1Payload) -> DiagnosticResult:
    # Construct the context for the LLM
    diagnostic_context = (
        f"Vehicle: {payload.vehicle.get('year')} {payload.vehicle.get('make')} {payload.vehicle.get('model')}\n"
        f"DTC Codes: {', '.join(payload.dtc_codes)}\n"
        f"Mechanic Notes: {payload.user_note}"
    )

    # Execute the structured LLM call
    response = client.chat.completions.create(

        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": diagnostic_context}
        ],
        response_format={"type":"json_object"},
        temperature=0.1 # Keep temperature low for deterministic, factual reasoning
    )

    choice = response.choices[0]
    raw = choice.message.content
 
    # Debug output - remove once everything works
    print("MODEL:", GROQ_MODEL)
    print("RAW LLM OUTPUT:", repr(raw))
    print("FINISH REASON:", choice.finish_reason)
 
    if not raw:
        raise ValueError(f"LLM returned no content (finish_reason={choice.finish_reason})")
 
    # Convert the JSON string to a dict, then validate it against the Pydantic model
    result_dict = json.loads(raw)
    return DiagnosticResult.model_validate(result_dict)

