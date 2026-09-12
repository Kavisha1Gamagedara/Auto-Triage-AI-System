from pydantic import BaseModel, Field
from typing import List, Dict

# The payload received from Agent 1
class Agent1Payload(BaseModel):
    session_id: str
    vehicle: Dict[str, str | int]  # {"make": "Toyota", "model": "Corolla", "year": 2019}
    dtc_codes: List[str]
    user_note: str

# The strictly formatted payload output to Agents 3 & 4
class DiagnosticResult(BaseModel):
    root_cause_component: str = Field(description="Exact physical part needing replacement (e.g., 'Mass Air Flow Sensor')")
    failure_mode: str = Field(description="Mechanical reasoning for why the part failed")
    severity: str = Field(description="Risk level: Low, Medium, or Critical")
    safety_warning: str = Field(description="Specific safety hazards for the mechanic")