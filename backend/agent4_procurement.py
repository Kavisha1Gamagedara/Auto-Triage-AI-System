"""Agent 4 - Procurement & Pricing.

Turns Agent 2's root-cause component into a priced, tiered bill of materials
for a specific vehicle.

CORE RULE: THE LLM MAY PROPOSE, ONLY THE DATABASE MAY PRICE.

An LLM is consulted for exactly one thing - which companion parts a repair
also needs - and only when the curated bom_dependencies table has no entry
for the part. Every name it proposes is re-resolved against the catalog, and
every price and part number on the way out is read from MongoDB. No figure in
this module's output originates from a model.
"""

import json
import os

from db import get_db
from agent4_resolver import PartResolver

TIERS = ["OEM_Genuine", "Certified_Aftermarket", "Economy"]

# An LLM-proposed name must resolve at least this well before it is allowed
# to be priced. Below it, the item is reported unpriced rather than guessed.
LLM_RESOLVE_ACCEPT = 0.7

MAX_PER_LIST = 3

# Incremented by _propose_bom_via_llm only. The curated-table path never
# touches it, which is what makes "zero LLM calls on the happy path"
# demonstrable rather than merely asserted.
LLM_CALL_COUNT = 0

_resolver: PartResolver | None = None


def reset_llm_call_count() -> None:
    """Reset the LLM call counter. For tests and demos."""
    global LLM_CALL_COUNT
    LLM_CALL_COUNT = 0


def get_resolver() -> PartResolver:
    """Return the shared resolver, building its BM25 index at most once.

    Built on first use rather than at import so that importing this module
    does not require a live database connection.
    """
    global _resolver
    if _resolver is None:
        _resolver = PartResolver(get_db())
    return _resolver


# --------------------------------------------------------------------------
# STEP 3b - the only LLM call in Agent 4, isolated for mocking
# --------------------------------------------------------------------------

BOM_SYSTEM_PROMPT = """You are a master auto parts counter clerk.
Given a primary replacement part, list the companion parts a workshop must
also fit (requires) and should advise the customer to fit (recommends).

Rules:
- Use generic catalog part names only, e.g. "Air Filter", "Brake Fluid DOT4".
- NEVER output prices, currency amounts, part numbers, or brand names.
- Maximum 3 items per list. Fewer is better than padding with guesses.
- requires = mandatory to complete the job safely.
- recommends = sensible same-visit replacements.

Respond with ONLY a valid JSON object - no markdown, no code fences:
{"requires": ["..."], "recommends": ["..."]}"""


def _propose_bom_via_llm(part_name: str, make: str, model: str, year: int) -> dict:
    """Ask the LLM which companion parts a repair needs. Names only.

    Returns {"requires": [str], "recommends": [str]}. Nothing returned here is
    trusted: every name is re-resolved against the catalog by the caller, and
    pricing is never sourced from this response.
    """
    global LLM_CALL_COUNT
    LLM_CALL_COUNT += 1

    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please add GROQ_API_KEY to your .env file.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        messages=[
            {"role": "system", "content": BOM_SYSTEM_PROMPT},
            {"role": "user", "content": f"Primary part: {part_name}\nVehicle: {year} {make} {model}"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = response.choices[0].message.content
    if not raw:
        raise ValueError("BOM proposal returned no content")

    data = json.loads(raw)
    return {
        "requires": [str(x) for x in data.get("requires", []) if str(x).strip()],
        "recommends": [str(x) for x in data.get("recommends", []) if str(x).strip()],
    }


def _build_bom(canonical: str, make: str, model: str, year: int, warnings: list[str]) -> tuple[list[dict], list[str]]:
    """Assemble the bill of materials for a resolved primary part.

    Returns (items, unpriced). Each item is {"name", "role"}.

    The curated table is authoritative: when it has the part this function
    returns before the LLM branch is reachable.
    """
    db = get_db()
    items = [{"name": canonical, "role": "primary"}]
    seen = {canonical}

    def extend(names: list[str], role: str) -> None:
        for name in names[:MAX_PER_LIST]:
            if name not in seen:
                seen.add(name)
                items.append({"name": name, "role": role})

    bom_doc = db.bom_dependencies.find_one({"primary_part": canonical}, {"_id": 0})

    if bom_doc:
        # Curated path. No LLM call is made here, and none may be made after
        # this return - the model is not consulted to supplement a hit.
        extend(list(bom_doc.get("requires") or []), "required")
        extend(list(bom_doc.get("recommends") or []), "recommended")
        return items, []

    # Fallback path only: the part is absent from bom_dependencies.
    warnings.append(
        f"'{canonical}' is not in the curated dependency table; companion parts were proposed by the "
        f"reasoning model and re-checked against the catalog."
    )

    try:
        proposal = _propose_bom_via_llm(canonical, make, model, year)
    except Exception as exc:
        warnings.append(f"Companion-part proposal unavailable ({exc}); quoting the primary part only.")
        return items, []

    resolver = get_resolver()
    unpriced: list[str] = []

    for role, key in (("required", "requires"), ("recommended", "recommends")):
        accepted = 0
        for proposed in proposal.get(key, []):
            if accepted >= MAX_PER_LIST:
                break
            # Strict mode: the alias n-gram stage is disabled for machine
            # proposals. It would otherwise pull a part name out of vague
            # prose at confidence 0.9 - above the pricing floor - so
            # "whatever pads they use" became a priced set of Brake Pads.
            match = resolver.resolve(proposed, allow_partial=False)
            # A proposal the catalog cannot confirm is reported, never priced.
            if match["canonical"] and match["confidence"] >= LLM_RESOLVE_ACCEPT:
                if match["canonical"] not in seen:
                    seen.add(match["canonical"])
                    items.append({"name": match["canonical"], "role": role})
                accepted += 1
            elif proposed not in unpriced:
                unpriced.append(proposed)

    return items, unpriced


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def get_procurement_quote(
    root_cause_component: str,
    make: str,
    model: str,
    year: int,
    severity: str = "Medium",
    safety_warning: str = "",
) -> dict:
    """Produce a tiered, priced quote for a root-cause component.

    Unknown parts and unlisted vehicles are normal outcomes, not errors: they
    return a valid response with warnings and, where possible, candidates.
    """
    db = get_db()
    warnings: list[str] = []

    empty_tiers = {tier: {"tier_total_lkr": 0, "complete": False, "parts": []} for tier in TIERS}

    def blank(resolved=None, method="none", confidence=0.0, candidates=None) -> dict:
        return {
            "resolved_part": resolved,
            "match_method": method,
            "match_confidence": float(confidence),
            "bill_of_materials": [],
            "unpriced_items": [],
            "tiers": dict(empty_tiers),
            "suppressed_tiers": [],
            "severity": severity,
            "safety_warning": safety_warning,
            "warnings": warnings,
            "candidates": candidates or [],
        }

    # --- STEP 1: resolve the component to a canonical catalog name ---------
    # Only the component name is resolved. Failure-mode prose would poison
    # the lexical match, so it is never passed here.
    match = get_resolver().resolve(root_cause_component)

    if not match["canonical"]:
        warnings.append(
            f"Could not match '{root_cause_component}' to any part in the catalog. "
            f"No pricing was attempted."
        )
        return blank(candidates=match["candidates"])

    canonical = match["canonical"]

    # --- STEP 2: identify the vehicle generation --------------------------
    generations = list(
        db.generations.find(
            {"make": make, "model": model, "year_from": {"$lte": year}, "year_to": {"$gte": year}},
            {"_id": 0},
        )
    )

    if not generations:
        warnings.append(
            f"No catalog generation covers a {year} {make} {model}. Parts are priced per generation, "
            f"so no quote could be produced."
        )
        return blank(canonical, match["method"], match["confidence"])

    if len(generations) > 1:
        # Generation year ranges touch at the boundary (E170 ends 2018, E210
        # starts 2018). Pick the newer one and say so rather than silently
        # taking whichever the index returned first.
        generations.sort(key=lambda g: g["year_from"], reverse=True)
        others = ", ".join(g["generation"] for g in generations[1:])
        warnings.append(
            f"Year {year} falls in more than one generation ({generations[0]['generation']}, {others}); "
            f"quoted against {generations[0]['generation']}. Confirm by VIN."
        )

    generation = generations[0]["generation"]

    # --- STEP 3: bill of materials ----------------------------------------
    items, unpriced_items = _build_bom(canonical, make, model, year, warnings)
    bom_names = [item["name"] for item in items]

    # --- STEP 4: one indexed query for every price ------------------------
    rows = list(
        db.parts.find(
            {"make": make, "model": model, "generation": generation, "part_name": {"$in": bom_names}},
            {"_id": 0},
        )
    )

    if not rows:
        warnings.append(
            f"'{canonical}' is not stocked for the {make} {model} {generation}."
        )

    by_name_tier: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        by_name_tier.setdefault((row["part_name"], row["tier"]), []).append(row)

    # --- STEP 5: safety rules for the PRIMARY part's category -------------
    primary_rows = [r for r in rows if r["part_name"] == canonical]
    if primary_rows:
        primary_category = primary_rows[0]["part_category"]
    else:
        any_row = db.parts.find_one({"part_name": canonical}, {"_id": 0, "part_category": 1})
        primary_category = any_row["part_category"] if any_row else None

    suppressed_tiers: list[str] = []
    if primary_category:
        rule = db.safety_rules.find_one({"part_category": primary_category}, {"_id": 0})
        if rule:
            # block_tiers is ';'-separated; restraint_system and ev_drivetrain
            # each block two tiers.
            blocked = [t.strip() for t in str(rule.get("block_tiers", "")).split(";") if t.strip()]
            suppressed_tiers = [t for t in TIERS if t in blocked]
            if suppressed_tiers:
                warnings.append(
                    f"{', '.join(suppressed_tiers)} suppressed for {primary_category}: {rule.get('reason', '')}"
                )

    # --- STEP 6: cheapest row per item, per surviving tier -----------------
    tiers: dict[str, dict] = {}
    for tier in TIERS:
        if tier in suppressed_tiers:
            continue

        tier_parts = []
        total = 0
        complete = True

        for item in items:
            candidates = by_name_tier.get((item["name"], tier), [])
            if not candidates:
                complete = False
                continue
            best = min(candidates, key=lambda r: r["price_lkr"])
            total += int(best["price_lkr"])
            tier_parts.append(
                {
                    "part_name": best["part_name"],
                    "brand": best["brand"],
                    "part_number": best["part_number"],
                    "price_lkr": int(best["price_lkr"]),
                    "role": item["role"],
                }
            )

        tiers[tier] = {"tier_total_lkr": int(total), "complete": complete, "parts": tier_parts}

    return {
        "resolved_part": canonical,
        "match_method": match["method"],
        "match_confidence": float(match["confidence"]),
        "bill_of_materials": bom_names,
        "unpriced_items": unpriced_items,
        "tiers": tiers,
        "suppressed_tiers": suppressed_tiers,
        "severity": severity,
        "safety_warning": safety_warning,
        "warnings": warnings,
        "candidates": [],
    }


if __name__ == "__main__":
    import sys

    probes = [
        ("Brake Pads", "Toyota", "Corolla", 2020),
        ("shockers", "Toyota", "Corolla", 2020),
        ("Seat Belt", "Toyota", "Corolla", 2020),
        ("flux capacitor", "Toyota", "Corolla", 2020),
        ("Brake Pads", "Tesla", "Cybertruck", 2024),
    ]

    for component, mk, md, yr in probes:
        before = LLM_CALL_COUNT
        quote = get_procurement_quote(component, mk, md, yr, severity="High", safety_warning="Support the vehicle on stands.")
        print(f"--- {component!r} on a {yr} {mk} {md} ---")
        print(f"  resolved   : {quote['resolved_part']} ({quote['match_method']}, {quote['match_confidence']:.2f})")
        print(f"  BOM        : {quote['bill_of_materials']}")
        for tier, data in quote["tiers"].items():
            print(f"  {tier:<22} LKR {data['tier_total_lkr']:>8,}  complete={data['complete']}")
        if quote["suppressed_tiers"]:
            print(f"  suppressed : {quote['suppressed_tiers']}")
        if quote["candidates"]:
            print(f"  candidates : {quote['candidates']}")
        for w in quote["warnings"]:
            print(f"  warning    : {w}")
        print(f"  LLM calls  : {LLM_CALL_COUNT - before} (total {LLM_CALL_COUNT})")
        print()

    print(f"Total LLM calls across all probes: {LLM_CALL_COUNT}")
    sys.exit(0)
