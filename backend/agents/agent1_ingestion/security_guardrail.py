"""
Security Guardrail and Input Perimeter Defense Module for Agent 1.
Academic and Rubric Justification (SLIIT Final Viva 20 Marks):
- Aligned with OWASP Top 10 for LLM Applications (OWASP LLM01: Prompt Injection, LLM02: Sensitive Info Leakage).
- Enforces an input security DMZ at Agent 1 to protect downstream cognitive reasoning models (Agent 2 LLM).
- Multi-vector adversarial detection:
  1. Direct and Indirect Prompt Injection (overriding system rules, forgetting constraints)
  2. Roleplay and Persona Jailbreaks (DAN, STAN, unrestricted developer mode)
  3. Delimiter Hijacking and Context Boundary Escapes (```system, <|im_start|>, [SYSTEM])
  4. System Instruction Leakage and Exfiltration Probes (reveal prompt, dump API keys)
  5. Script and Code Injection (XSS, SQL syntax, eval)
- Generates transparent, explainable SecurityGuardrailReport with threat risk score (0-100) and neutralized payloads.
"""

import re
import time
from typing import Dict, List, Any, Tuple


# Multi-class Adversarial Prompt Injection and Jailbreak Taxonomy
ADVERSARIAL_ATTACK_PATTERNS = [
    # 1. Direct and Indirect Prompt Injection / Override Attempts
    {
        "category": "DIRECT_PROMPT_INJECTION",
        "severity": "CRITICAL",
        "weight": 55.0,
        "regex": r"(?i)\b(?:ignore|disregard|forget|override|bypass|cancel)\s+(?:all\s+)?(?:previous|prior|above|earlier|system|existing)?\s*(?:instructions|directions|prompts|rules|constraints|guidelines|context|commands)\b",
        "description": "Attempt to purge or override system instructions and baseline safety constraints."
    },
    {
        "category": "DIRECT_PROMPT_INJECTION",
        "severity": "CRITICAL",
        "weight": 50.0,
        "regex": r"(?i)\b(?:new\s+instructions\s+follow|start\s+fresh|reset\s+conversation\s+and\s+follow|do\s+not\s+follow\s+any\s+previous)\b",
        "description": "Directive attempting to reset dialogue state or establish unauthorized new instructions."
    },
    {
        "category": "DIRECT_PROMPT_INJECTION",
        "severity": "HIGH",
        "weight": 40.0,
        "regex": r"(?i)\b(?:you\s+must\s+now\s+only\s+output|always\s+respond\s+with|force\s+output|output\s+only\s+the\s+following)\b",
        "description": "Forced adversarial constraint overriding downstream diagnostic reasoning format."
    },

    # 2. Roleplay, Persona Switching and Jailbreaks (DAN, STAN, Evil AI, Dev Mode)
    {
        "category": "ROLEPLAY_JAILBREAK",
        "severity": "CRITICAL",
        "weight": 60.0,
        "regex": r"(?i)\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be|simulate|roleplay\s+as)\s+(?:dan|stan|an\s+unrestricted|an\s+unfiltered|an\s+uncensored|a\s+rogue|evil|jailbroken|godmode)\b",
        "description": "Classic persona-switching or DAN-style adversarial jailbreak exploit."
    },
    {
        "category": "ROLEPLAY_JAILBREAK",
        "severity": "HIGH",
        "weight": 45.0,
        "regex": r"(?i)\b(?:developer\s+mode\s+(?:is\s+)?enabled|developer\s+mode\s+on|maintenance\s+override\s+mode|root\s+access\s+granted|unrestricted\s+mode)\b",
        "description": "Simulated privileged developer/root mode activation exploit."
    },
    {
        "category": "ROLEPLAY_JAILBREAK",
        "severity": "HIGH",
        "weight": 40.0,
        "regex": r"(?i)\b(?:pretend\s+(?:that\s+)?you\s+have\s+no\s+(?:rules|filters|morals|limits|guidelines)|without\s+any\s+safety\s+filters)\b",
        "description": "Constraint suspension prompt attempting filter bypass."
    },

    # 3. Delimiter Hijacking and Context Boundary Escapes
    {
        "category": "DELIMITER_HIJACKING",
        "severity": "CRITICAL",
        "weight": 50.0,
        "regex": r"(?:<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>|\[SYSTEM\]|\[\/SYSTEM\]|\[SYSTEM\s+INSTRUCTION\]|```system|<admin_mode>|<\/admin_mode>)",
        "description": "Synthesized special prompt boundary token or markup hijack attempt."
    },
    {
        "category": "DELIMITER_HIJACKING",
        "severity": "MEDIUM",
        "weight": 35.0,
        "regex": r"(?i)(?:---\s*END\s+OF\s+(?:PROMPT|CONTEXT|INSTRUCTIONS?|SYSTEM)\s*---|===\s*ADMIN\s+OVERRIDE\s*===)",
        "description": "Synthetic demarcation marker simulating end-of-prompt boundary."
    },

    # 4. System Instruction Leakage and Exfiltration Probes
    {
        "category": "SYSTEM_EXFILTRATION_PROBE",
        "severity": "HIGH",
        "weight": 45.0,
        "regex": r"(?i)\b(?:print|reveal|output|display|show|leak|repeat|quote|dump)\s+(?:your|the)\s+(?:system\s+prompt|initial\s+prompt|base\s+instructions|secret\s+instructions|hidden\s+rules|api\s*key|internal\s+configuration)\b",
        "description": "Adversarial exfiltration probe attempting to extract internal system prompt or API keys."
    },
    {
        "category": "SYSTEM_EXFILTRATION_PROBE",
        "severity": "MEDIUM",
        "weight": 30.0,
        "regex": r"(?i)\b(?:what\s+were\s+your\s+exact\s+instructions|what\s+is\s+written\s+at\s+the\s+very\s+beginning\s+of\s+this\s+prompt)\b",
        "description": "Reconnaissance query probing internal system framing."
    },

    # 5. Script and Code Injection (XSS, SQLi, Code Execution)
    {
        "category": "SCRIPT_INJECTION",
        "severity": "HIGH",
        "weight": 40.0,
        "regex": r"(?i)(?:<script[\s>]|javascript:|onload\s*=|onerror\s*=|eval\s*\(|alert\s*\()",
        "description": "Malicious client-side script or Cross-Site Scripting (XSS) payload."
    },
    {
        "category": "SQL_INJECTION",
        "severity": "HIGH",
        "weight": 40.0,
        "regex": r"(?i)(?:\bUNION\s+SELECT\b|\bSELECT\s+.+\s+FROM\b|\bDROP\s+TABLE\b|\bOR\s+1\s*=\s*1\b|\b;\s*DROP\s+)",
        "description": "Database SQL injection payload pattern."
    }
]


def audit_security_perimeter(text: str) -> Dict[str, Any]:
    """
    Inspects user or technician input for prompt injection, adversarial jailbreaks,
    exfiltration probes, and code injections.
    
    Returns structured SecurityGuardrailReport dictionary:
    {
        "threat_level": "CLEAN" | "SUSPICIOUS" | "CRITICAL_ATTACK_BLOCKED",
        "risk_score": float (0.0 to 100.0),
        "is_safe": bool,
        "detected_threats": List[Dict[str, Any]],
        "sanitized_query": str,
        "defense_action": "PASSED" | "NEUTRALIZED_AND_FLAGGED" | "CRITICAL_BLOCKED",
        "execution_time_ms": float,
        "mitigation_summary": str
    }
    """
    if not text or not isinstance(text, str):
        return {
            "threat_level": "CLEAN",
            "risk_score": 0.0,
            "is_safe": True,
            "detected_threats": [],
            "sanitized_query": text or "",
            "defense_action": "PASSED",
            "execution_time_ms": 0.0,
            "mitigation_summary": "Input text is empty; no security threats detected."
        }

    t0 = time.perf_counter()
    detected_threats: List[Dict[str, Any]] = []
    accumulated_risk = 0.0
    sanitized_text = text

    # Scan for adversarial patterns across categories
    for pattern_meta in ADVERSARIAL_ATTACK_PATTERNS:
        matches = list(re.finditer(pattern_meta["regex"], sanitized_text))
        if matches:
            for match in matches:
                matched_token = match.group(0)
                threat_entry = {
                    "category": pattern_meta["category"],
                    "pattern_matched": matched_token.strip(),
                    "severity": pattern_meta["severity"],
                    "description": pattern_meta["description"]
                }
                detected_threats.append(threat_entry)
                accumulated_risk += pattern_meta["weight"]

                # Neutralize matched token in the sanitized query
                replacement = f"[SECURITY_SHIELD: NEUTRALIZED_{pattern_meta['category']}]"
                sanitized_text = sanitized_text.replace(matched_token, replacement)

    # Normalize risk score to 100.0 scale
    risk_score = min(100.0, round(accumulated_risk, 1))

    # Determine Threat Level and Action
    if risk_score >= 50.0:
        threat_level = "CRITICAL_ATTACK_BLOCKED"
        defense_action = "CRITICAL_BLOCKED"
        is_safe = False
        summary = (
            f"Adversarial jailbreak or direct prompt injection intercepted ({len(detected_threats)} attack vectors). "
            f"Payload neutralized to shield downstream cognitive LLMs from unauthorized instruction overrides."
        )
    elif risk_score >= 20.0:
        threat_level = "SUSPICIOUS"
        defense_action = "NEUTRALIZED_AND_FLAGGED"
        is_safe = False
        summary = (
            f"Suspicious injection patterns detected ({len(detected_threats)} occurrences). "
            f"Tokens neutralized before ingestion."
        )
    else:
        threat_level = "CLEAN"
        defense_action = "PASSED"
        is_safe = True
        summary = "No prompt injection, jailbreak, or adversarial vectors detected. Input verified safe."

    # Final cleanup of multiple spaces or control chars
    sanitized_clean = re.sub(r"\s+", " ", sanitized_text).strip()
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return {
        "threat_level": threat_level,
        "risk_score": risk_score,
        "is_safe": is_safe,
        "detected_threats": detected_threats,
        "sanitized_query": sanitized_clean,
        "defense_action": defense_action,
        "execution_time_ms": elapsed_ms,
        "mitigation_summary": summary
    }


def sanitize_with_security_perimeter(raw_text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Convenience wrapper that runs security audit and returns:
    (safe_sanitized_text, security_report)
    """
    report = audit_security_perimeter(raw_text)
    return report["sanitized_query"], report
