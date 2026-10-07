"""Measures how often Agent 2's output names a part that exists in Agent 4's catalog.

Run with:  python -m agents.agent2_reasoning.test_vocabulary
"""

from core.models import Agent1Payload
from agents.agent2_reasoning.agent2_logic import deduce_root_cause, CATALOG_PARTS

CASES = [
    {"vehicle": {"year": 2015, "make": "Toyota", "model": "Corolla"},
     "dtc_codes": ["P0301"],
     "user_note": "rough idle when cold, slight shudder at low speed"},

    {"vehicle": {"year": 2019, "make": "Honda", "model": "Civic"},
     "dtc_codes": ["P0171"],
     "user_note": "rough idle at stoplights, hesitation on acceleration"},

    {"vehicle": {"year": 2017, "make": "Toyota", "model": "Aqua"},
     "dtc_codes": ["P0420"],
     "user_note": "check engine light on, slight sulphur smell from exhaust"},

    {"vehicle": {"year": 2016, "make": "Suzuki", "model": "Wagon R"},
     "dtc_codes": ["P0135"],
     "user_note": "poor fuel economy, engine light came on last week"},

    {"vehicle": {"year": 2018, "make": "Honda", "model": "Vezel"},
     "dtc_codes": ["C0051"],
     "user_note": "grinding noise when braking, pedal feels soft"},

    {"vehicle": {"year": 2014, "make": "Toyota", "model": "Premio"},
     "dtc_codes": ["P0562"],
     "user_note": "dim headlights at idle, battery warning light flickers"},

    {"vehicle": {"year": 2020, "make": "Nissan", "model": "Leaf"},
     "dtc_codes": ["P0441"],
     "user_note": "fuel smell near the rear, light on after refuelling"},

    {"vehicle": {"year": 2013, "make": "Toyota", "model": "Vitz"},
     "dtc_codes": ["P0128"],
     "user_note": "takes a long time to warm up, heater blows cold"},
]


def main():
    print(f"Catalog loaded: {len(CATALOG_PARTS)} part names\n")

    hits = 0
    for i, case in enumerate(CASES, 1):
        payload = Agent1Payload(session_id=f"vocab-test-{i:03d}", **case)
        try:
            result = deduce_root_cause(payload)
        except Exception as exc:
            print(f"{i}. FAILED: {exc}")
            continue

        h = result.primary_hypothesis
        matched = h.catalog_part_name is not None
        hits += matched
        flag = "HIT " if matched else "MISS"
        print(f"{i}. [{flag}] {h.root_cause_component}")
        print(f"        catalog: {h.catalog_part_name}")

    print(f"\nCatalog hit rate: {hits}/{len(CASES)} ({hits / len(CASES):.0%})")


if __name__ == "__main__":
    main()