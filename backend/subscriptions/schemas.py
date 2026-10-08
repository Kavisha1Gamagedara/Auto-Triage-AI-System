from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

# 4 Subscription Tier Definitions & Limits
SUBSCRIPTION_TIERS = {
    "basic": {
        "id": "basic",
        "name": "Basic Free",
        "price_lkr": 0,
        "limit": 2,
        "period": "daily",
        "description": "Essential entry diagnostics for independent technicians.",
        "features": [
            "2 Autonomous Diagnoses per Day",
            "Agent 1 NHTSA vPIC Ground Truth Check",
            "Agent 2 Physics of Failure Root Cause",
            "Standard Multi-Agent Particle Pipeline",
            "SAE DTC Cascade Diagnostics"
        ],
        "badge": "FREE TIER",
        "is_unlimited": False
    },
    "plus": {
        "id": "plus",
        "name": "Plus Tier",
        "price_lkr": 30000,
        "limit": 300,
        "period": "monthly",
        "description": "High-volume diagnostics for busy repair bays & independent garages.",
        "features": [
            "300 Autonomous Diagnoses per Month",
            "Priority Groq Llama-3 70B Reasoning Core",
            "Agent 3 OEM Workshop Manual Dense Vector RAG",
            "Interactive Holographic Particle Flow",
            "Exportable Executive Repair Dossiers",
            "Monthly Quota Rollover Support"
        ],
        "badge": "MOST POPULAR",
        "is_unlimited": False
    },
    "pro": {
        "id": "pro",
        "name": "Pro Tier",
        "price_lkr": 50000,
        "limit": 600,
        "period": "monthly",
        "description": "Comprehensive multi-agent pipeline with OEM torque specs & BOM procurement.",
        "features": [
            "600 Autonomous Diagnoses per Month",
            "Agent 4 Automated BOM Catalog & Parts Resolver",
            "3-Tier Multi-Distributor Quoting (OEM / Aftermarket / Economy)",
            "ChromaDB Dense Semantic Manual Chunk Retrieval",
            "Sub-50ms Execution SLA & Full Telemetry Drawer",
            "Multi-Vehicle Workshop Queue"
        ],
        "badge": "PROFESSIONAL",
        "is_unlimited": False
    },
    "ultra": {
        "id": "ultra",
        "name": "Ultra Tier",
        "price_lkr": 100000,
        "limit": 999999,
        "period": "monthly",
        "description": "Unrestricted enterprise throughput, priority LLM reasoning & zero quota caps.",
        "features": [
            "Unlimited Autonomous Diagnoses per Month",
            "Zero Daily or Monthly Quota Limits (Infinite Runs)",
            "Dedicated Low-Latency Inference Pipeline",
            "Full Multi-Agent LangGraph Asynchronous DAG Engine",
            "Enterprise Multi-Mechanic Team Seat Management",
            "24/7 Priority Automotive Engineering Support"
        ],
        "badge": "ENTERPRISE",
        "is_unlimited": True
    }
}


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    phone: str = Field(..., min_length=7, max_length=25)
    password: str = Field(..., min_length=6, max_length=100)
    workshop_name: Optional[str] = "Independent Workshop"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format (must contain @ and a valid domain)")
        return v


class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class QuotaInfo(BaseModel):
    tier: str
    limit: int
    used: int
    remaining: int
    period: str
    is_unlimited: bool
    can_diagnose: bool


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: str  # 'admin' | 'mechanic'
    tier: str  # 'basic' | 'plus' | 'pro' | 'ultra'
    workshop_name: Optional[str] = None
    created_at: str
    last_active: str
    subscription_status: str  # 'active' | 'expired'
    subscription_expires: Optional[str] = None
    quota: QuotaInfo


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class CheckoutSimulateRequest(BaseModel):
    tier: str  # 'plus' | 'pro' | 'ultra'
    payment_method: str = "card"  # 'card' | 'bank_transfer' | 'lanka_qr'
    test_card_number: Optional[str] = "4242 4242 4242 4242"
    test_card_name: Optional[str] = "Master Mechanic"
    test_cvv: Optional[str] = "123"
    should_fail: Optional[bool] = False


class CheckoutResponse(BaseModel):
    success: bool
    transaction_ref: str
    tier: str
    amount_lkr: int
    payment_method: str
    timestamp: str
    message: str
    user: UserOut


class AdminUpdateUserSubscription(BaseModel):
    tier: str
    reset_usage: Optional[bool] = False
    bonus_tries: Optional[int] = 0


class AdminMetrics(BaseModel):
    total_users: int
    mechanics_count: int
    admins_count: int
    tier_distribution: Dict[str, int]
    monthly_recurring_revenue_lkr: int
    total_diagnoses_today: int
