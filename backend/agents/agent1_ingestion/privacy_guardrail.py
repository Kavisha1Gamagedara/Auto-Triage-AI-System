"""
Responsible AI: Automated PII Masking & Privacy Guardrail for Agent 1.
Ensures User Data Protection, Privacy Compliance & Confidentiality at the Ingestion Boundary.

Compliance Standards:
- Sri Lanka Personal Data Protection Act (PDPA No. 9 of 2022)
- EU General Data Protection Regulation (GDPR Art. 5(1)(c) - Data Minimisation)
- Responsible AI Principles (Fairness, Privacy & User Protection)

Redacts & Masks:
1. Sri Lankan National Identity Card (NIC) numbers (Old 9-digit + V/X and Modern 12-digit formats)
2. Sri Lankan (+94 / 07x) and international mobile & telephone numbers
3. Customer personal names (via contextual markers and spaCy Named Entity Recognition)
4. Email addresses
5. Payment / credit card numbers
6. Driver's license numbers
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("privacy_guardrail")

# Non-person words that spaCy might misclassify as PERSON in automotive contexts
VEHICLE_PERSON_EXCLUSIONS = {
    "toyota", "honda", "ford", "nissan", "suzuki", "bmw", "audi", "mazda", "hyundai",
    "kia", "chevrolet", "chevy", "mercedes", "benz", "mitsubishi", "subaru", "lexus",
    "aqua", "vezel", "civic", "camry", "prius", "corolla", "wagon", "leaf", "alto",
    "vitz", "axio", "premio", "allion", "land", "cruiser", "prado", "hilux", "ranger"
}

# 1. Sri Lankan National Identity Card (NIC) Patterns
# Old format: 9 digits followed by V or X (e.g. 951234567V, 892345678X)
REGEX_OLD_NIC = re.compile(r"\b([0-9]{9}[vVxX])\b")
# New format: 12 digits starting with 19 or 20 (e.g. 199512345678, 200112345678)
REGEX_NEW_NIC = re.compile(r"\b((?:19|20)[0-9]{10})\b")

# 2. Telephone & Mobile Patterns (Sri Lankan primary, plus standard international)
REGEX_SL_PHONE = re.compile(r"(?:\+94|0094|0)\s*(?:7[01245678]|11|21|23|24|25|26|27|31|32|33|34|35|36|37|38|41|45|47|51|52|54|55|57|63|65|66|67|81|91)[-\s]?[0-9]{3}[-\s]?[0-9]{4}\b")
REGEX_INTL_PHONE = re.compile(r"\b\+?[1-9]\d{0,2}[-.\s]\(?\d{2,4}\)?[-.\s]\d{3,4}[-.\s]\d{3,4}\b")

# 3. Email Addresses
REGEX_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# 4. Payment / Credit Card Numbers (16-digit spaced or dashed)
REGEX_PAYMENT_CARD = re.compile(r"\b(?:\d{4}[-\s]){3}\d{4}\b")

# 5. Sri Lankan Driver's License Number (e.g. B1234567 or DL-1234567)
REGEX_DRIVING_LICENSE = re.compile(r"\b(?:DL[-\s]?)?([A-Z][0-9]{7})\b")

# 6. Contextual Customer Name Preambles (e.g. "Customer: Kamal Perera", "Driver: Nimal Silva")
REGEX_CUSTOMER_NAME = re.compile(
    r"(?i)\b(?:customer|owner|driver|client|contact\s+person|mr\.|mrs\.|ms\.)\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"
)


def _mask_partially(value: str, entity_type: str) -> str:
    """Creates a privacy-preserving obfuscated preview for the audit log."""
    clean = value.strip()
    if entity_type == "SRI_LANKAN_NIC":
        if len(clean) == 10:
            return f"{clean[:2]}*****{clean[-2:]}"
        elif len(clean) == 12:
            return f"{clean[:4]}******{clean[-2:]}"
    elif entity_type == "PHONE_NUMBER":
        return f"{clean[:3]}-***-{clean[-3:]}" if len(clean) >= 6 else "***"
    elif entity_type == "EMAIL_ADDRESS":
        parts = clean.split("@")
        if len(parts) == 2:
            u, d = parts
            return f"{u[0]}***@{d}"
    elif entity_type == "CUSTOMER_NAME":
        words = clean.split()
        return " ".join(f"{w[0]}***" for w in words)
    elif entity_type == "PAYMENT_CARD":
        return f"****-****-****-{clean[-4:]}"
    elif entity_type == "DRIVING_LICENSE":
        return f"{clean[0]}*****{clean[-1]}"
    return "***"


def mask_pii(text: str, nlp_doc: Optional[Any] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Detects and redacts Personally Identifiable Information (PII) from user/mechanic complaint text.
    Returns:
        (sanitized_text, privacy_guardrail_report)
    """
    if not text or not isinstance(text, str):
        return text, {
            "pii_detected": False,
            "total_redactions": 0,
            "redacted_entities": [],
            "compliance_standard": "Sri Lanka PDPA No. 9 of 2022 & GDPR Art. 5(1)(c)",
            "sanitized_text": text
        }

    redacted_entities: List[Dict[str, str]] = []
    sanitized = text

    # 1. Redact Sri Lankan NIC (Old 9+V/X format)
    for match in REGEX_OLD_NIC.finditer(sanitized):
        val = match.group(1)
        # Avoid false positives with DTCs like P0171
        if not val.upper().startswith(("P0", "C0", "B0", "U0")):
            token = "[REDACTED_NIC]"
            redacted_entities.append({
                "entity_type": "SRI_LANKAN_NIC",
                "preview_masked": _mask_partially(val, "SRI_LANKAN_NIC"),
                "token": token
            })
            sanitized = sanitized.replace(val, token)

    # 2. Redact Sri Lankan NIC (Modern 12-digit format)
    for match in REGEX_NEW_NIC.finditer(sanitized):
        val = match.group(1)
        token = "[REDACTED_NIC]"
        redacted_entities.append({
            "entity_type": "SRI_LANKAN_NIC",
            "preview_masked": _mask_partially(val, "SRI_LANKAN_NIC"),
            "token": token
        })
        sanitized = sanitized.replace(val, token)

    # 3. Redact Email Addresses
    for match in REGEX_EMAIL.finditer(sanitized):
        val = match.group(0)
        token = "[REDACTED_EMAIL]"
        redacted_entities.append({
            "entity_type": "EMAIL_ADDRESS",
            "preview_masked": _mask_partially(val, "EMAIL_ADDRESS"),
            "token": token
        })
        sanitized = sanitized.replace(val, token)

    # 4. Redact Phone Numbers (Sri Lankan & International)
    for match in REGEX_SL_PHONE.finditer(sanitized):
        val = match.group(0)
        token = "[REDACTED_PHONE]"
        redacted_entities.append({
            "entity_type": "PHONE_NUMBER",
            "preview_masked": _mask_partially(val, "PHONE_NUMBER"),
            "token": token
        })
        sanitized = sanitized.replace(val, token)

    for match in REGEX_INTL_PHONE.finditer(sanitized):
        val = match.group(0)
        if "[REDACTED" not in val:
            token = "[REDACTED_PHONE]"
            redacted_entities.append({
                "entity_type": "PHONE_NUMBER",
                "preview_masked": _mask_partially(val, "PHONE_NUMBER"),
                "token": token
            })
            sanitized = sanitized.replace(val, token)

    # 5. Redact Payment Cards
    for match in REGEX_PAYMENT_CARD.finditer(sanitized):
        val = match.group(0)
        token = "[REDACTED_PAYMENT_CARD]"
        redacted_entities.append({
            "entity_type": "PAYMENT_CARD",
            "preview_masked": _mask_partially(val, "PAYMENT_CARD"),
            "token": token
        })
        sanitized = sanitized.replace(val, token)

    # 6. Redact Driver's Licenses
    for match in REGEX_DRIVING_LICENSE.finditer(sanitized):
        val = match.group(1)
        # Verify it doesn't match DTCs (B0001, etc.)
        if not val.upper().startswith(("B00", "B01", "B02", "B03")):
            token = "[REDACTED_DRIVING_LICENSE]"
            redacted_entities.append({
                "entity_type": "DRIVING_LICENSE",
                "preview_masked": _mask_partially(val, "DRIVING_LICENSE"),
                "token": token
            })
            sanitized = sanitized.replace(val, token)

    # 7. Redact Contextual Customer Personal Names
    for match in REGEX_CUSTOMER_NAME.finditer(sanitized):
        val = match.group(1)
        name_lower = val.lower().split()[0]
        if name_lower not in VEHICLE_PERSON_EXCLUSIONS:
            token = "[REDACTED_CUSTOMER]"
            redacted_entities.append({
                "entity_type": "CUSTOMER_NAME",
                "preview_masked": _mask_partially(val, "CUSTOMER_NAME"),
                "token": token
            })
            sanitized = sanitized.replace(val, token)

    # 8. spaCy NER Person entity fallback (if doc provided)
    if nlp_doc is not None and hasattr(nlp_doc, "ents"):
        for ent in nlp_doc.ents:
            if ent.label_ == "PERSON":
                raw_name = ent.text.strip()
                name_words = raw_name.lower().split()
                # Skip automotive brands
                if not any(w in VEHICLE_PERSON_EXCLUSIONS for w in name_words) and len(raw_name) > 3:
                    if raw_name in sanitized and "[REDACTED" not in raw_name:
                        token = "[REDACTED_CUSTOMER]"
                        redacted_entities.append({
                            "entity_type": "CUSTOMER_NAME",
                            "preview_masked": _mask_partially(raw_name, "CUSTOMER_NAME"),
                            "token": token
                        })
                        sanitized = sanitized.replace(raw_name, token)

    has_pii = len(redacted_entities) > 0
    if has_pii:
        logger.info(f"[PrivacyGuardrail] Redacted {len(redacted_entities)} sensitive PII items from intake text.")

    report = {
        "pii_detected": has_pii,
        "total_redactions": len(redacted_entities),
        "redacted_entities": redacted_entities,
        "compliance_standard": "Sri Lanka Personal Data Protection Act (PDPA No. 9 of 2022) & GDPR Art. 5(1)(c)",
        "sanitized_text": sanitized
    }

    return sanitized, report
