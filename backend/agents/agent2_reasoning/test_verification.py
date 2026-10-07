# scratch_verify.py in backend/
from core.models import Hypothesis, DiagnosticResult, Agent1Payload
from agents.agent2_reasoning.agent2_logic import verify_hypotheses

bogus = Hypothesis(
    root_cause_component="Distributor cap",
    failure_mode="Cracked housing causing spark scatter",
    confidence=80,
    supporting_evidence=["P0AA6"],
    confirming_test="Visual inspection of distributor cap",
)
real = Hypothesis(
    root_cause_component="High voltage battery pack module",
    failure_mode="Cell imbalance triggering isolation fault",
    confidence=60,
    supporting_evidence=["P0AA6"],
    confirming_test="Battery isolation resistance test",
)

result = DiagnosticResult(
    reasoning_steps=["test"],
    primary_hypothesis=bogus,
    differential_hypotheses=[real],
    severity="high",
    safety_warning="High voltage system",
)

payload = Agent1Payload(
    session_id="test-verification-001",
    vehicle={"year": 2022, "make": "Tesla", "model": "Model 3"},
    dtc_codes=["P0AA6"],
    user_note="warning light, reduced power",
)

out = verify_hypotheses(result, payload)
print("STATUS:", out.status)
print("PRIMARY:", out.primary_hypothesis.root_cause_component)
for h in [out.primary_hypothesis] + out.differential_hypotheses:
    print(f"  {h.root_cause_component}: verified={h.verified} {h.verification_note}")