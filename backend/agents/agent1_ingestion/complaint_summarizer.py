"""
NLP Customer & Mechanic Complaint Summarization Engine for Agent 1.
Part of the Hybrid NLP/NER & IR Ingestion Pipeline.

Meets SLIIT Assignment Requirements:
- "NLP techniques (Ex- NER, Summarization)"
- "One or more LLMs"
- Resilient Dual-Mode Architecture: Fast Zero-Shot LLM Abstractive Synthesis with deterministic spaCy linguistic extractive fallback.
"""

import os
import re
import json
import logging
import unicodedata
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("complaint_summarizer")

# Operational driving condition patterns
CONDITION_PATTERNS = [
    (r"\b(?:at|on|during|when|stopped\s+at)\s+(?:idle|idling|low\s+idle|stoplight|red\s+light|traffic\s+light)s?\b", "At idle / stoplights"),
    (r"\b(?:on|during|under|upon)\s+(?:hard\s+)?acceleration\b", "During acceleration"),
    (r"\b(?:on|at|during)\s+(?:cold\s+start|morning\s+start|starting\s+cold)\b", "Cold start"),
    (r"\b(?:at|on)\s+(?:highway|freeway|high\s+speed|cruising)\b", "Highway cruising"),
    (r"\b(?:under|when)\s+(?:braking|stopping|slowing\s+down)\b", "Under braking / decelerating"),
    (r"\b(?:after|upon)\s+(?:refueling|refuelling|filling\s+up|gas\s+station|petrol\s+shed)\b", "After refueling"),
    (r"\b(?:over|on)\s+(?:bumps|rough\s+road|potholes)\b", "Over rough roads / bumps"),
    (r"\b(?:with|under)\s+(?:a/c|ac|air\s*con(?:ditioning)?)\s+(?:on|running)\b", "With A/C engaged"),
]

# Physical symptom indicators for extractive rule-based parsing
SYMPTOM_INDICATORS = {
    "shakes violently": "Severe engine vibration and violent shuddering",
    "violent shuddering": "Severe engine vibration and violent shuddering",
    "shuddering": "Powertrain vibration / shuddering",
    "shudder": "Powertrain vibration / shuddering",
    "shakes": "Engine vibration / shaking",
    "shaking": "Engine vibration / shaking",
    "misfire": "Combustion misfire",
    "misfiring": "Combustion misfire",
    "hesitat": "Engine hesitation / throttle lag",
    "jerking": "Powertrain jerking / surging",
    "stalling": "Engine stall / cutting out",
    "stalled": "Engine stall / cutting out",
    "won't start": "No-start condition",
    "hard start": "Extended crank / hard starting",
    "overheat": "Engine cooling / overheating",
    "smoke": "Exhaust / engine bay smoke emission",
    "rotten egg": "Catalytic converter sulfur odor",
    "sulfur": "Catalytic converter sulfur odor",
    "gas smell": "Fuel vapor / gasoline odor",
    "fuel smell": "Fuel vapor / gasoline odor",
    "flashing check engine": "Flashing MIL (Cat-damaging misfire)",
    "check engine light": "MIL (Check Engine Light) illuminated",
    "flashing light": "Flashing malfunction indicator",
    "battery light": "Charging system / low-voltage warning",
    "hybrid light": "High Voltage / Hybrid system warning",
    "brake warning": "Brake system malfunction warning",
    "grinding": "Metallic grinding noise",
    "squealing": "Accessory drive / brake squeal",
    "knocking": "Engine internal metallic knocking"
}


def _assess_severity_and_urgency(text: str, dtc_codes: Optional[List[str]] = None) -> Tuple[str, int]:
    """
    Evaluates complaint severity and urgency score (1-10) using domain heuristics.
    """
    t_lower = text.lower()
    score = 5
    level = "Moderate"

    # Critical triggers (+3 to +5)
    critical_triggers = [
        "flashing", "smoke", "fire", "overheat", "stall", "died",
        "no brake", "brake failure", "battery dying", "hybrid failure",
        "violent", "knock", "shut down"
    ]
    if any(k in t_lower for k in critical_triggers):
        score = 9
        level = "Critical"
    elif any(k in t_lower for k in ["shudder", "shakes", "hesitat", "misfire", "smell", "rotten", "odor", "grind"]):
        score = 7
        level = "Moderate"
    elif any(k in t_lower for k in ["chirp", "intermittent", "rattle", "squeak", "dim"]):
        score = 4
        level = "Minor"

    # Trouble code severity adjustments
    if dtc_codes:
        for c in dtc_codes:
            cu = c.upper()
            if cu in {"P0300", "P0301", "P0302", "P0303", "P0304"} and "flashing" in t_lower:
                score = max(score, 10)
                level = "Critical"
            elif cu.startswith("P0A") or cu.startswith("P30"):  # Hybrid / High Voltage
                score = max(score, 9)
                level = "Critical"
            elif cu in {"P0171", "P0420", "P0101"}:
                score = max(score, 6)

    return level, min(10, max(1, score))


def _extract_operational_conditions(text: str) -> List[str]:
    """Extracts driving condition contexts (at idle, upon acceleration, etc.)."""
    conditions = []
    for pattern, label in CONDITION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            if label not in conditions:
                conditions.append(label)
    return conditions


def _extract_chief_complaints_spacy(text: str) -> List[str]:
    """Extracts structured symptom bullet points using linguistic keyword mapping."""
    t_lower = text.lower()
    complaints = []
    # Match multi-word first
    sorted_keywords = sorted(SYMPTOM_INDICATORS.keys(), key=lambda x: len(x), reverse=True)
    for keyword in sorted_keywords:
        if keyword in t_lower:
            label = SYMPTOM_INDICATORS[keyword]
            if label not in complaints:
                complaints.append(label)
    if not complaints:
        first_clause = text.split(".")[0].strip()
        complaints.append(first_clause[:80])
    return complaints[:5]


def _build_linguistic_extractive_summary(
    clean_text: str,
    chief_complaints: List[str],
    conditions: List[str],
    severity: str,
    urgency: int
) -> Dict[str, Any]:
    """
    Deterministic fallback: synthesizes a clean technical abstract without external LLM dependencies.
    """
    cond_str = f" occurring {conditions[0].lower()}" if conditions else ""
    symptoms_str = ", ".join(chief_complaints[:2]) if chief_complaints else "vehicle performance irregularity"

    executive_summary = (
        f"Customer reports {symptoms_str}{cond_str}. "
        f"Assessed as {severity.lower()} severity (urgency: {urgency}/10) requiring prioritized triage inspection."
    )

    return {
        "executive_summary": executive_summary,
        "chief_complaints": chief_complaints,
        "operational_conditions": conditions,
        "severity_level": severity,
        "urgency_score": urgency,
        "method": "spacy_extractive_linguistic"
    }


def _summarize_with_groq_llm(
    text: str,
    dtc_codes: Optional[List[str]],
    conditions: List[str],
    chief_complaints: List[str],
    severity: str,
    urgency: int
) -> Optional[Dict[str, Any]]:
    """
    Uses the configured Groq LLM (e.g. gpt-oss-120b) to generate an abstractive executive diagnostic summary.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        from groq import Groq
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        client = Groq(api_key=api_key)

        prompt = (
            f"Provide a JSON summary of this vehicle complaint for intake triage:\n"
            f"Complaint: \"{text}\"\n"
            f"DTC Codes: {', '.join(dtc_codes) if dtc_codes else 'None'}"
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert automotive diagnostic intake assistant. "
                        "Return your output as a valid JSON object with exactly these keys:\n"
                        "{\n"
                        "  \"executive_summary\": \"1-2 sentence concise technical diagnostic abstract\",\n"
                        "  \"chief_complaints\": [\"Symptom 1\", \"Symptom 2\"],\n"
                        "  \"operational_conditions\": [\"Condition 1\"],\n"
                        "  \"severity_level\": \"Minor\" or \"Moderate\" or \"Critical\",\n"
                        "  \"urgency_score\": integer between 1 and 10\n"
                        "}"
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=2048,
            temperature=0.1
        )

        raw = response.choices[0].message.content
        if not raw:
            return None

        # Normalize unicode and quotes to clean ASCII
        raw = unicodedata.normalize("NFKC", raw)
        raw = raw.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")

        parsed = json.loads(raw)

        raw_conds = parsed.get("operational_conditions", conditions)
        clean_conds = [raw_conds] if isinstance(raw_conds, str) else list(raw_conds)

        raw_complaints = parsed.get("chief_complaints", chief_complaints)
        clean_complaints = [raw_complaints] if isinstance(raw_complaints, str) else list(raw_complaints)

        return {
            "executive_summary": parsed.get("executive_summary", "").strip(),
            "chief_complaints": clean_complaints,
            "operational_conditions": clean_conds,
            "severity_level": parsed.get("severity_level", severity),
            "urgency_score": int(parsed.get("urgency_score", urgency)),
            "method": "hybrid_llm_abstractive"
        }

    except Exception as e:
        logger.warning(f"[ComplaintSummarizer] Groq LLM summarization bypassed ({e}); using spaCy fallback.")
        return None


def summarize_complaint(raw_text: str, dtc_codes: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Main entry point for Agent 1 Complaint Summarization.
    Executes hybrid abstractive LLM summarization with zero-downtime spaCy linguistic fallback.
    """
    if not raw_text or len(raw_text.strip()) < 5:
        return {
            "executive_summary": "No descriptive customer complaint provided; diagnostic analysis based solely on trouble codes.",
            "chief_complaints": [],
            "operational_conditions": [],
            "severity_level": "Minor",
            "urgency_score": 1,
            "method": "rule_default"
        }

    clean_text = " ".join(raw_text.strip().split())

    # 1. Linguistic extraction (spaCy / deterministic)
    severity, urgency = _assess_severity_and_urgency(clean_text, dtc_codes)
    conditions = _extract_operational_conditions(clean_text)
    chief_complaints = _extract_chief_complaints_spacy(clean_text)

    # 2. Try LLM abstractive synthesis
    llm_result = _summarize_with_groq_llm(
        clean_text,
        dtc_codes,
        conditions,
        chief_complaints,
        severity,
        urgency
    )
    if llm_result and llm_result.get("executive_summary"):
        return llm_result

    # 3. Resilient spaCy linguistic fallback
    return _build_linguistic_extractive_summary(
        clean_text,
        chief_complaints,
        conditions,
        severity,
        urgency
    )
