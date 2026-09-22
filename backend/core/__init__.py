"""
Auto-Triage AI System - Core Package
Contains shared Pydantic models, database connections, and system-wide schemas.
"""

from .models import (
    DiagnosticRequest,
    Agent1Payload,
    VehicleDetails,
    DiagnosticResult,
    SpellcheckRequest,
    DTCCascadeRequest,
    DTCCascadeAnalysis,
    DTCCascadeChain,
    RepairRequest,
    ProcurementRequest,
    ProcurementResponse,
    FuzzyCorrection,
    DTCCodeHierarchy
)
from .db import get_db, MONGO_URI, MONGO_DB

__all__ = [
    "DiagnosticRequest",
    "Agent1Payload",
    "VehicleDetails",
    "DiagnosticResult",
    "SpellcheckRequest",
    "DTCCascadeRequest",
    "DTCCascadeAnalysis",
    "DTCCascadeChain",
    "RepairRequest",
    "ProcurementRequest",
    "ProcurementResponse",
    "FuzzyCorrection",
    "DTCCodeHierarchy",
    "get_db",
    "MONGO_URI",
    "MONGO_DB"
]
