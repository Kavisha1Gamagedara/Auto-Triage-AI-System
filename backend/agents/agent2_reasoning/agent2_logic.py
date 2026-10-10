import json
import unicodedata
import os
import logging
from dotenv import load_dotenv
from groq import Groq
try:
    from core.models import Agent1Payload, DiagnosticResult, Hypothesis, VerificationResponse
except ImportError:
    from models import Agent1Payload, DiagnosticResult, Hypothesis, VerificationResponse

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

logger = logging.getLogger(__name__)

#New module level code for DB Connection Loss
def _load_catalog_parts() -> list[str]:
    """Agent 4's part vocabulary. Fetched once; empty list disables constraining."""
    try:
        from core.db import get_db
        names = sorted(get_db().parts.distinct("part_name"))
        logger.info("Loaded %d catalog part names for constrained vocabulary", len(names))
        return names
    except Exception as exc:
        logger.warning("Catalog vocabulary unavailable, falling back to free text: %s", exc)
        return []

CATALOG_PARTS = _load_catalog_parts()

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
- "catalog_part_name" must be chosen EXACTLY from the catalog list provided below, copied character for character. If no catalog entry genuinely matches the failing component, set it to null. Never force an approximate match: a null is more useful downstream than a wrong part name.

Respond with a single JSON object and nothing else, matching this schema exactly:
{schema}
"""
CATALOG_BLOCK =(
    "\n\nAvailable catalog part names:\n" + "\n".join(f"- {n}" for n in CATALOG_PARTS)
    if CATALOG_PARTS else
    "\n\nNo catalog is available. Set catalog_part_name to null for every hypothesis."
)

SYSTEM_CONTENT = SYSTEM_PROMPT.replace(
    "{schema}",json.dumps(DiagnosticResult.model_json_schema(), indent=2)
) + CATALOG_BLOCK

#Validating the Parts match is real
def _check_catalog_names(result: DiagnosticResult) -> DiagnosticResult:
    if not CATALOG_PARTS:
        return result
    valid = set(CATALOG_PARTS)
    for h in [result.primary_hypothesis] + result.differential_hypotheses:
        if h.catalog_part_name and h.catalog_part_name not in valid:
            logger.warning("Hallucinated catalog name discarded: %r", h.catalog_part_name)
            h.catalog_part_name = None
    return result

VERIFIER_PROMPT = """You are a vehicle systems expert. You are NOT diagnosing anything.

For each candidate component listed, work through these in order:
1. What drivetrain does this vehicle use? State it explicitly: internal combustion, hybrid, plug-in hybrid, or battery electric. If the model name is one you recognise as electric-only or hybrid-only, say so.
2. Which systems does that drivetrain rule out entirely? A battery electric vehicle has no fuel tank, no EVAP system, no exhaust, no spark ignition, no engine oil system, and no transmission in the conventional sense.
3. Only then, for each candidate: does this component physically exist on this vehicle, and could a fault in it set the listed DTC codes?

Mark plausible=false only when you are confident the component does not exist on this vehicle
or cannot set these codes. Uncertainty is not grounds for rejection.

Common failures to catch: distributor caps on coil-on-plug engines; spark plugs, oxygen sensors,
catalytic converters, fuel pumps, fuel injectors, EVAP components or engine thermostats on battery
electric vehicles; carburettor parts on fuel-injected engines; timing belts on timing-chain engines.
Use only plain ASCII. Respond with a single JSON object matching this schema:
{schema}
"""

VERIFIER_CONTENT = VERIFIER_PROMPT.replace(
    "{schema}", json.dumps(VerificationResponse.model_json_schema(), indent=2)
)

def verify_hypotheses(result: DiagnosticResult, payload: Agent1Payload) -> DiagnosticResult:
    client =get_client()
    candidates = [result.primary_hypothesis] + result.differential_hypotheses

    listing ="\n".join(
        f"{i}. {h.root_cause_component} - {h.failure_mode}"
        for i, h in enumerate(candidates)
    )
    context =(
        f"Vehicle: {payload.vehicle.get('year')} {payload.vehicle.get('make')} {payload.vehicle.get('model')}\n"
        f"DTC Codes: {', '.join(payload.dtc_codes)}\n"
        f"Candidate:\n{listing}"
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": VERIFIER_CONTENT},
            {"role": "user", "content": context}
        ],
        response_format ={"type":"json_object"},
        max_completion_tokens=2048,
        temperature=0.0,
    )

    raw = response.choices[0].message.content
    if not raw:
        return result  # verification unavailable; return diagnosis unchanged

    raw = unicodedata.normalize("NFKC", raw)
    verdicts = VerificationResponse.model_validate_json(raw).verdicts

    for v in verdicts:
        if 0 <= v.index < len(candidates) and not v.plausible:
            candidates[v.index].verified = False
            candidates[v.index].verification_note = v.reason

    return _rebuild(result, candidates)

def _rebuild(result: DiagnosticResult, candidates: list[Hypothesis]) -> DiagnosticResult:
    verified = [h for h in candidates if h.verified]
    rejected = [h for h in candidates if not h.verified]

    if not verified:
        result.status = "unverified"
        return result

    verified.sort(key=lambda h: h.confidence, reverse=True)
    result.primary_hypothesis = verified[0]
    result.differential_hypotheses = verified[1:] + rejected
    result.status = "diagnosed"
    return result

def deduce_root_cause(payload: Agent1Payload) -> DiagnosticResult:
    # -------------------------------------------------------------------------
    # SECURITY CIRCUIT BREAKER (NIST AI RMF 1.0 & OWASP LLM01 / LLM10)
    # If Agent 1's Input Security Perimeter flagged a Critical attack, trip circuit breaker.
    # Withhold downstream LLM invocation to prevent compute exhaustion & phantom hypotheses.
    # -------------------------------------------------------------------------
    sec = getattr(payload, "security_guardrail", None)
    sec_level = None
    sec_score = 0.0
    threat_info = "Adversarial prompt injection override detected"

    if isinstance(sec, dict):
        sec_level = sec.get("threat_level")
        sec_score = sec.get("risk_score", 0.0)
        detected = sec.get("detected_threats", [])
        if detected and isinstance(detected, list) and len(detected) > 0:
            first_t = detected[0]
            if isinstance(first_t, dict) and first_t.get("pattern_matched"):
                threat_info = f"Matched '{first_t['pattern_matched']}'"
    elif sec is not None:
        sec_level = getattr(sec, "threat_level", None)
        sec_score = getattr(sec, "risk_score", 0.0)
        detected = getattr(sec, "detected_threats", [])
        if detected and len(detected) > 0:
            p_match = getattr(detected[0], "pattern_matched", None) or (detected[0].get("pattern_matched") if isinstance(detected[0], dict) else None)
            if p_match:
                threat_info = f"Matched '{p_match}'"

    if sec_level == "CRITICAL_ATTACK_BLOCKED":
        logger.warning(
            "Security Circuit Breaker tripped: Adversarial injection detected (%s, Risk: %s). Halting Agent 2 reasoning.",
            threat_info, sec_score
        )
        return DiagnosticResult(
            status="unverified",
            reasoning_steps=[
                "Intake Audit: Zero OBD-II diagnostic trouble codes (DTCs) detected in customer intake text.",
                "Non-Technical Request: Submitted notes contained non-diagnostic directives rather than physical vehicle symptoms.",
                "Diagnostic Pause: Autonomous reasoning paused to prevent guessing phantom components or recommending incorrect repairs.",
                "Commercial Safeguard: Parts catalog procurement and repair manuals are paused until genuine fault codes are provided.",
                "Technician Action: Please enter valid diagnostic trouble codes (e.g., P0171, P0300) or describe vehicle symptoms."
            ],
            primary_hypothesis=Hypothesis(
                root_cause_component="PIPELINE_SUSPENDED_SECURITY_QUARANTINE",
                failure_mode="No recognized vehicle failure symptoms or diagnostic trouble codes (DTCs) provided. Diagnostic deduction paused.",
                confidence=0,
                supporting_evidence=[
                    "Zero OBD-II diagnostic trouble codes supplied in complaint notes",
                    f"Non-diagnostic directives intercepted by Agent 1 Input Security Perimeter ({threat_info})"
                ],
                confirming_test="Enter valid OBD-II diagnostic trouble codes or mechanic observations and re-run diagnostic triage.",
                verified=False,
                verification_note=f"Security Guardrail: Intercepted prompt override ({threat_info}, Risk Score: {sec_score}/100). LLM inference bypassed (0 tokens).",
                catalog_part_name=None
            ),
            differential_hypotheses=[],
            severity="critical",
            safety_warning="DIAGNOSTIC PAUSED: No verified mechanical faults or diagnostic trouble codes present. Autonomous vehicle repair actions and parts procurement are withheld.",
            freeze_frame_analysis=payload.freeze_frame_analysis
        )

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

    # If OBD-II Freeze Frame Telemetry is present, inject physical sensor ground-truth
    if payload.freeze_frame_analysis:
        ffa = payload.freeze_frame_analysis
        trim_str = f"Total Fuel Trim: {ffa.total_fuel_trim_pct}% ({ffa.trim_condition})" if ffa.total_fuel_trim_pct is not None else ""
        ruled_out = ", ".join(ffa.ruled_out_components) if ffa.ruled_out_components else "None"
        targets = ", ".join(ffa.high_probability_targets) if ffa.high_probability_targets else "None"
        diagnostic_context += (
            f"\n\nOBD-II FREEZE FRAME GROUND-TRUTH TELEMETRY:\n"
            f"- Operating State: {ffa.operating_state}\n"
            f"- Telemetry Analysis Verdict: {ffa.root_cause_verdict}\n"
            f"{('- ' + trim_str + chr(10)) if trim_str else ''}"
            f"- HIGH-PROBABILITY TARGETS: {targets}\n"
            f"- RULED-OUT COMPONENTS: {ruled_out}\n"
            f"CRITICAL TECHNICIAN INSTRUCTION:\n"
            f"You MUST ground your reasoning in this empirical telemetry. "
            f"Do NOT diagnose any of the ruled-out components as your primary hypothesis because the freeze-frame sensor data disproves them. "
            f"Directly cite the freeze-frame parameters and operating state in your reasoning_steps and supporting_evidence."
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

    # Fold typographic characters to ASCII equivalents before parsing,
    # so downstream agents and Windows consoles never choke on curly quotes or em-dashes.
    raw = unicodedata.normalize("NFKC", raw)
    raw = raw.encode("ascii", "ignore").decode("ascii")

    logger.debug("Model: %s, finish_reason: %s", GROQ_MODEL, choice.finish_reason)
    logger.debug("Raw LLM output: %r", raw)

    if not raw:
        raise ValueError(f"LLM returned no content (finish_reason={choice.finish_reason})")

    # Convert the JSON string to a dict, then validate it against the Pydantic model
    result_dict = json.loads(raw)
    result = DiagnosticResult.model_validate(result_dict)
    result = _check_catalog_names(result)

    if payload.freeze_frame_analysis:
        result.freeze_frame_analysis = payload.freeze_frame_analysis

    try:
        final_result = verify_hypotheses(result, payload)
    except Exception as exc:
        print(f"Verification stage failed, returning raw result: {exc}")
        final_result = result

    if payload.freeze_frame_analysis and not getattr(final_result, "freeze_frame_analysis", None):
        final_result.freeze_frame_analysis = payload.freeze_frame_analysis

    return final_result
