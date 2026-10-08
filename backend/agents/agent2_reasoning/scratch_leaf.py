# scratch_leaf.py
from core.models import Agent1Payload
from agents.agent2_reasoning.agent2_logic import deduce_root_cause

p = Agent1Payload(
    session_id="leaf-001",
    vehicle={"year": 2020, "make": "Nissan", "model": "Leaf"},
    dtc_codes=["P0441"],
    user_note="fuel smell near the rear, light on after refuelling",
)
r = deduce_root_cause(p)
print("STATUS:", r.status)
for h in [r.primary_hypothesis] + r.differential_hypotheses:
    print(f"  {h.root_cause_component}: verified={h.verified} {h.verification_note}")