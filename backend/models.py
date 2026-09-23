from pydantic import BaseModel, Field
from typing import List, Dict
from typing import List, Literal
from pydantic import BaseModel, Field, computed_field, model_validator

# The payload received from Agent 1
class Agent1Payload(BaseModel):
    session_id: str
    vehicle: Dict[str, str | int]  # {"make": "Toyota", "model": "Corolla", "year": 2019}
    dtc_codes: List[str]
    user_note: str

#Extending output schema for alternative dianosis
class Hypothesis(BaseModel):
    root_cause_component: str =Field(
    ...,description="The specific failing component, e.g. 'Mass Airflow (MAF) Sensor'"
    )
    failure_mode: str = Field(
    ...,decsription="How the component fails, e.g. 'Contaminated hot-wire element causing under-reported airflow'"

    )
    confidence: int =Field(
        ...,ge=0, le=100,
        description="Independent confidence score(0-100) for this hypothesis.Confidence across hypotheses do not" \
        " sum to 100."
        
    )
    supporting_evidence: List[str] = Field(
        ..., description="Which DTC codes and which phrases from the user note support this hypothesis"
    )
    confirming_test: str =Field(
        ..., description="The single cheapest workshop test that would confirm or eliminate this hypothesis"
    )


# The strictly formatted payload output to Agents 3 & 4
class DiagnosticResult(BaseModel):
     reasoning_steps: List[str] = Field(
        ..., description="Ordered diagnostic reasoning, from symptoms to candidate causes, BEFORE committing to a ranking"
    )
     primary_hypothesis: Hypothesis
     differential_hypotheses: List[Hypothesis] = Field(
        default_factory=list, max_length=3,
        description="Alternative causes, ranked by descending confidence. Must be distinct components, not restatements of the primary."
    )
     severity: Literal["low", "moderate", "high", "critical"]
     safety_warning: str

     @model_validator(mode="after")
     def primary_must_rank_highest(self):
        if self.differential_hypotheses:
            best = max(self.differential_hypotheses, key=lambda h: h.confidence)
            if best.confidence > self.primary_hypothesis.confidence:
                others = [h for h in self.differential_hypotheses if h is not best]
                others.append(self.primary_hypothesis)
                self.primary_hypothesis = best
                self.differential_hypotheses = sorted(
                    others, key=lambda h: h.confidence, reverse=True
                )
            else:
                self.differential_hypotheses = sorted(
                    self.differential_hypotheses, key=lambda h: h.confidence, reverse=True
                )
        return self

    # Backwards compatibility: Agent 3 / Agent 4 may already read these flat fields.
     @computed_field
     @property
     def root_cause_component(self) -> str:
        return self.primary_hypothesis.root_cause_component

     @computed_field
     @property
     def failure_mode(self) -> str:
        return self.primary_hypothesis.failure_mode