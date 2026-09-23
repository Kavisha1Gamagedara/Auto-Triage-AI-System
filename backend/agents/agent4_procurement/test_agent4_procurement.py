"""Tests for the Agent 4 procurement pipeline.

Runs against the live catalog via get_db(), matching test_agent4_resolver.py.

No test here may make a real LLM call: every test that exercises the
uncurated path patches _propose_bom_via_llm. A test that hits the network
would be slow, non-deterministic and would spend the project's Groq quota.
"""

import json

import pytest

import agent4_procurement as a4
from models import ProcurementResponse

# A part with a row in bom_dependencies, and one without. If the curated
# table changes, these are the two constants to update.
CURATED_PART = "Brake Pads"
UNCURATED_PART = "Handbrake Cable"

VEHICLE = ("Toyota", "Corolla", 2020)

NO_COMPANIONS = {"requires": [], "recommends": []}


@pytest.fixture(scope="module", autouse=True)
def _warm_resolver():
    """Build the BM25 index once for the whole module."""
    a4.get_resolver()


@pytest.fixture(autouse=True)
def _reset_counter():
    a4.reset_llm_call_count()
    yield


def quote(part, vehicle=VEHICLE, **kw):
    make, model, year = vehicle
    return a4.get_procurement_quote(part, make, model, year, **kw)


# ---------------------------------------------------------------------------
# THE CORE RULE: the LLM may propose, only the database may price
# ---------------------------------------------------------------------------

def test_curated_part_never_calls_the_llm(monkeypatch):
    """A part in bom_dependencies must not reach the model at all.

    The LLM function is replaced with one that raises: if the curated branch
    ever calls it - in parallel, to supplement, anywhere - the test fails
    loudly rather than silently spending a request.
    """
    def explode(*args, **kwargs):
        raise AssertionError("LLM was called on a curated-table hit")

    monkeypatch.setattr(a4, "_propose_bom_via_llm", explode)

    for part in ["Brake Pads", "Water Pump", "Alternator", "Timing Belt",
                 "Windscreen", "Fuel Pump", "AC Compressor", "CV Joint"]:
        result = quote(part)
        assert result["resolved_part"] == part

    assert a4.LLM_CALL_COUNT == 0


def test_counter_is_not_inflated_by_a_mock(monkeypatch):
    """LLM_CALL_COUNT increments inside the real function only.

    This is what makes "zero LLM calls" a measurement rather than a claim:
    a mocked call must not move the counter, or the counter proves nothing.
    """
    calls = []

    def fake(*args, **kwargs):
        calls.append(args)
        return NO_COMPANIONS

    monkeypatch.setattr(a4, "_propose_bom_via_llm", fake)
    quote(UNCURATED_PART)

    assert len(calls) == 1
    assert a4.LLM_CALL_COUNT == 0


def test_uncurated_part_reaches_the_llm(monkeypatch):
    """The fallback path is live: an absent part does consult the model."""
    monkeypatch.setattr(a4, "_propose_bom_via_llm", lambda *a, **k: NO_COMPANIONS)

    result = quote(UNCURATED_PART)

    assert result["resolved_part"] == UNCURATED_PART
    assert any("not in the curated dependency table" in w for w in result["warnings"])


def test_no_price_or_part_number_survives_from_the_llm(monkeypatch):
    """Figures in a proposal are never echoed into the response."""
    poisoned = {
        "requires": ["Brake Fluid DOT4 - LKR 9999 - PN FAKE-123"],
        "recommends": ["Brake Disc costs 88888"],
    }
    monkeypatch.setattr(a4, "_propose_bom_via_llm", lambda *a, **k: poisoned)

    result = quote(UNCURATED_PART)
    priced = json.dumps(result["tiers"])

    assert "9999" not in priced
    assert "FAKE" not in priced
    assert "88888" not in priced

    for tier in result["tiers"].values():
        for part in tier["parts"]:
            assert isinstance(part["price_lkr"], int)


def test_llm_failure_degrades_instead_of_erroring(monkeypatch):
    """A missing API key or dead endpoint still returns a usable quote."""
    def boom(*args, **kwargs):
        raise RuntimeError("GROQ_API_KEY is not set")

    monkeypatch.setattr(a4, "_propose_bom_via_llm", boom)

    result = quote(UNCURATED_PART)

    assert result["resolved_part"] == UNCURATED_PART
    assert result["bill_of_materials"] == [UNCURATED_PART]
    assert any("Companion-part proposal unavailable" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# STRICT RESOLUTION OF MACHINE PROPOSALS
# ---------------------------------------------------------------------------

def test_vague_llm_proposals_are_not_priced(monkeypatch):
    """Padded prose must land in unpriced_items, never in a tier basket.

    Regression: alias_partial returned 0.9 and BM25 returned a perfect 1.0
    for any query containing a one-token part name, both above the 0.7
    pricing floor. "whatever pads they use" became a priced set of Brake
    Pads. Strict mode resolves machine proposals without the n-gram stage
    and requires the proposal to be built only from words the part owns.
    """
    vague = {
        "requires": ["whatever pads they use", "a new battery maybe"],
        "recommends": ["possibly the radiator", "check the mirror probably"],
    }
    monkeypatch.setattr(a4, "_propose_bom_via_llm", lambda *a, **k: vague)

    result = quote(UNCURATED_PART)

    assert result["bill_of_materials"] == [UNCURATED_PART]
    assert len(result["unpriced_items"]) == 4
    for tier in result["tiers"].values():
        assert [p["part_name"] for p in tier["parts"]] == [UNCURATED_PART]


def test_clean_llm_proposals_are_still_priced(monkeypatch):
    """Strict mode must not reject well-formed proposals.

    Exact names, alias surface forms and reordered names all still price;
    only padding is refused.
    """
    clean = {"requires": ["Brake Fluid DOT4"], "recommends": ["brake fluid", "Brake Disc"]}
    monkeypatch.setattr(a4, "_propose_bom_via_llm", lambda *a, **k: clean)

    result = quote(UNCURATED_PART)

    assert "Brake Fluid DOT4" in result["bill_of_materials"]
    assert "Brake Disc" in result["bill_of_materials"]
    assert result["unpriced_items"] == []


def test_llm_lists_are_capped_in_code(monkeypatch):
    """The prompt asks for 3; the code enforces it regardless of the reply."""
    flood = {
        "requires": ["Brake Fluid DOT4", "Brake Disc", "Brake Pads",
                     "Brake Hardware Clips", "Brake Caliper"],
        "recommends": ["Air Filter", "Cabin Filter", "Spark Plug", "Drive Belt"],
    }
    monkeypatch.setattr(a4, "_propose_bom_via_llm", lambda *a, **k: flood)

    result = quote(UNCURATED_PART)
    roles = [i for i in result["bill_of_materials"] if i != UNCURATED_PART]

    assert len(roles) <= 2 * a4.MAX_PER_LIST


# ---------------------------------------------------------------------------
# SAFETY RULES
# ---------------------------------------------------------------------------

def test_safety_rule_uses_the_primary_parts_category():
    """Not whichever row the database returned first.

    A Brake Pads basket also contains braking hardware and fluid, and an
    Alternator basket pulls in Drive Belt (engine_management) and Battery
    (electrical). Only the primary part's category may decide suppression.
    """
    assert quote("Brake Pads")["suppressed_tiers"] == ["Economy"]
    assert quote("Alternator")["suppressed_tiers"] == []
    assert quote("Water Pump")["suppressed_tiers"] == []


def test_rule_blocking_two_tiers_drops_both():
    """block_tiers is ';'-separated and restraint_system blocks two."""
    result = quote("Seat Belt")

    assert result["suppressed_tiers"] == ["Certified_Aftermarket", "Economy"]
    assert list(result["tiers"]) == ["OEM_Genuine"]
    assert any("single-use safety devices" in w for w in result["warnings"])


def test_suppressed_tier_is_absent_not_zeroed():
    """A withheld tier must not look like an unavailable one."""
    result = quote("Brake Pads")

    assert "Economy" not in result["tiers"]
    assert "Economy" in result["suppressed_tiers"]


def test_explicit_no_restriction_rule_suppresses_nothing():
    """The 8 'reviewed, no restriction' rows must not block a tier."""
    for part in ["Bonnet", "Radiator", "Battery", "Headlight", "Clutch Kit"]:
        result = quote(part)
        assert result["suppressed_tiers"] == [], part
        assert len(result["tiers"]) == 3, part


# ---------------------------------------------------------------------------
# PRICING
# ---------------------------------------------------------------------------

def test_tier_total_is_the_sum_of_its_line_items():
    result = quote("Brake Pads")

    for name, tier in result["tiers"].items():
        assert tier["tier_total_lkr"] == sum(p["price_lkr"] for p in tier["parts"]), name


def test_cheapest_row_is_chosen_per_item():
    """Within a tier, each BOM item takes its lowest-priced row."""
    from db import get_db

    db = get_db()
    result = quote("Brake Pads")

    for tier_name, tier in result["tiers"].items():
        for part in tier["parts"]:
            rows = db.parts.find({
                "make": "Toyota", "model": "Corolla", "generation": "E210",
                "part_name": part["part_name"], "tier": tier_name,
            })
            assert part["price_lkr"] == min(r["price_lkr"] for r in rows)


def test_oem_is_never_cheaper_than_certified():
    """Sanity check on tier ordering for a fully stocked basket."""
    result = quote("Brake Pads")
    assert result["tiers"]["OEM_Genuine"]["tier_total_lkr"] > \
           result["tiers"]["Certified_Aftermarket"]["tier_total_lkr"]


def test_every_priced_field_comes_from_the_catalog():
    result = quote("Brake Pads")

    for tier in result["tiers"].values():
        for part in tier["parts"]:
            assert part["brand"]
            assert part["part_number"]
            assert part["role"] in {"primary", "required", "recommended"}


# ---------------------------------------------------------------------------
# GRACEFUL FAILURE — never a 500 for a domain miss
# ---------------------------------------------------------------------------

def test_unknown_part_returns_a_valid_response_with_candidates():
    result = quote("flux capacitor")

    assert result["resolved_part"] is None
    assert result["match_method"] == "none"
    assert result["bill_of_materials"] == []
    assert len(result["candidates"]) > 0
    assert len(result["warnings"]) > 0
    ProcurementResponse(**result)


def test_unlisted_vehicle_returns_a_valid_response_with_a_warning():
    result = quote("Brake Pads", vehicle=("Tesla", "Cybertruck", 2024))

    assert result["resolved_part"] == "Brake Pads"
    assert any("No catalog generation covers" in w for w in result["warnings"])
    ProcurementResponse(**result)


def test_boundary_year_warns_about_the_ambiguity():
    """Generation ranges touch: 2018 matches both E170 and E210."""
    result = quote("Brake Pads", vehicle=("Toyota", "Corolla", 2018))

    assert any("more than one generation" in w for w in result["warnings"])


def test_severity_and_safety_warning_pass_through_untouched():
    kw = {"severity": "Critical", "safety_warning": "Do not drive the vehicle."}

    ok = quote("Brake Pads", **kw)
    failed = quote("flux capacitor", **kw)

    for result in (ok, failed):
        assert result["severity"] == "Critical"
        assert result["safety_warning"] == "Do not drive the vehicle."


def test_mechanic_slang_resolves_through_the_full_pipeline():
    """The resolver's partial matching stays enabled for human input."""
    assert quote("dynamo not charging")["resolved_part"] == "Alternator"
    assert quote("shockers gone")["resolved_part"] == "Shock Absorber"


# ---------------------------------------------------------------------------
# CONTRACT
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("part,vehicle", [
    ("Brake Pads", VEHICLE),
    ("Seat Belt", VEHICLE),
    ("flux capacitor", VEHICLE),
    ("Brake Pads", ("Tesla", "Cybertruck", 2024)),
    ("Traction Battery Pack", ("BYD", "Atto 3", 2023)),
])
def test_response_validates_and_serialises(part, vehicle, monkeypatch):
    monkeypatch.setattr(a4, "_propose_bom_via_llm", lambda *a, **k: NO_COMPANIONS)

    result = quote(part, vehicle=vehicle)

    ProcurementResponse(**result)
    json.dumps(result)

    assert isinstance(result["match_confidence"], float)
    for tier in result["tiers"].values():
        assert isinstance(tier["tier_total_lkr"], int)
        assert isinstance(tier["complete"], bool)


def test_resolver_is_built_once():
    assert a4.get_resolver() is a4.get_resolver()
