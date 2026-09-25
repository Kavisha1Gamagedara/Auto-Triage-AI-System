import json
import unicodedata
from core.models import DiagnosticResult, Agent1Payload
import os
from dotenv import load_dotenv
from groq import Groq
try:
    from core.models import Agent1Payload, DiagnosticResult
except ImportError:
    from models import Agent1Payload, DiagnosticResult

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please add GROQ_API_KEY to your .env file or environment variables.")
    return Groq(api_key=api_key)

SYSTEM_PROMPT = """You are an expert automotive diagnostic technician performing structured differential diagnosis.

Work in this exact order:
1. Reason step by step from the DTC codes and described symptoms to a set of candidate causes. Record these in "reasoning_steps".
2. Only then rank the candidates and assign confidence.

Rules:
- Produce ONE primary hypothesis and 1-3 differential hypotheses.
- Differentials must be genuinely DIFFERENT components or systems, never a rewording of the primary.
- Every hypothesis must physically exist on the stated year/make/model and be consistent with its drivetrain.
- "confidence" is independent per hypothesis and must NOT sum to 100 across hypotheses.
- The primary hypothesis must carry the highest confidence.
- "supporting_evidence" must reference the actual DTC codes and actual phrases from the user note. Never invent symptoms that were not reported.
- "confirming_test" must be the cheapest test that separates this hypothesis from the others.
- If evidence is thin, express that through low confidence values rather than inventing certainty.
- Use only plain ASCII characters. No typographic dashes, curly quotes, or emoji.

Respond with a single JSON object and nothing else, matching this schema exactly:
{schema}
"""

SYSTEM_CONTENT = SYSTEM_PROMPT.replace(
    "{schema}",json.dumps(DiagnosticResult.model_json_schema(), indent=2)
)

def deduce_root_cause(payload: Agent1Payload) -> DiagnosticResult:
    client = get_client()
    diagnostic_context = (
        f"Vehicle: {payload.vehicle.get('year')} {payload.vehicle.get('make')} {payload.vehicle.get('model')}\n"
        f"DTC Codes: {', '.join(payload.dtc_codes)}\n"
        f"Mechanic Notes: {payload.user_note}"
    )

    # If multi-DTC cascade is detected by Agent 1, inject root trigger priority hint
    if payload.dtc_cascade and payload.dtc_cascade.has_cascade:
        cascade = payload.dtc_cascade
        diagnostic_context += (
            f"\nMulti-DTC Cascade Analysis: Root trigger code is {cascade.primary_code} "
            f"({cascade.primary_description} in {cascade.primary_subsystem}). "
            f"Downstream cascade symptoms: {', '.join(cascade.cascade_codes)}. "
            f"Diagnosis hint: Focus root-cause deduction primarily on the upstream trigger {cascade.primary_code} "
            f"rather than replacing parts for downstream cascade codes."
        )


    # Execute the structured LLM call
    response = client.chat.completions.create(

        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_CONTENT},
            {"role": "user", "content": diagnostic_context}
        ],
        response_format={"type":"json_object"},
        max_completion_tokens=4096,
        temperature=0.1 # Keep temperature low for deterministic, factual reasoning
    )

    choice = response.choices[0]
    raw = choice.message.content

    if not raw:
        raise ValueError(f"LLM returned no content (finish_reason={choice.finish_reason})")

    #Fold typgraphic characters to ASCII equivalents before parsing,
    #so downstream agents and Windows consoles never choke on curly quotes or em-dashes.
    raw = unicodedata.normalize("NFKC",raw)
    
    # Debug output - remove once everything works
    print("MODEL:", GROQ_MODEL)
    print("RAW LLM OUTPUT:", repr(raw))
    print("FINISH REASON:", choice.finish_reason)
 
    if not raw:
        raise ValueError(f"LLM returned no content (finish_reason={choice.finish_reason})")
 
    # Convert the JSON string to a dict, then validate it against the Pydantic model
    result_dict = json.loads(raw)
    return DiagnosticResult.model_validate(result_dict)

