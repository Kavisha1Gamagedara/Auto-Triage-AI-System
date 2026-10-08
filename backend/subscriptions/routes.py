from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header, status

from .schemas import (
    SUBSCRIPTION_TIERS,
    UserRegister,
    UserLogin,
    UserOut,
    AuthResponse,
    QuotaInfo,
    CheckoutSimulateRequest,
    CheckoutResponse,
    AdminUpdateUserSubscription,
    AdminMetrics,
    TierUpdatePayload,
    TierCreatePayload
)
from .store import store, verify_token, generate_token

router = APIRouter()


async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Extracts authenticated user if Authorization header is present."""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    payload = verify_token(token)
    if not payload:
        return None
    user = store.get_user_by_id(payload.get("uid"))
    return user


async def require_authenticated_user(authorization: Optional[str] = Header(None)) -> dict:
    """Enforces that the user is logged in (Mechanic or Admin)."""
    user = await get_current_user_optional(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_REQUIRED",
                "message": "Guest users can view the web app but must log in to execute diagnosis."
            }
        )
    return user


async def require_admin_user(authorization: Optional[str] = Header(None)) -> dict:
    """Enforces that the user is an Administrator."""
    user = await require_authenticated_user(authorization)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "message": "Access restricted to System Administrators only."
            }
        )
    return user


# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@router.post("/auth/register", response_model=AuthResponse, tags=["Authentication"])
async def register(req: UserRegister):
    try:
        user = store.register_user(
            name=req.name,
            email=req.email,
            phone=req.phone,
            password=req.password,
            workshop_name=req.workshop_name
        )
        token = generate_token(user["id"], user["email"], user["role"])
        return {
            "token": token,
            "user": store.format_user_out(user)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/auth/login", response_model=AuthResponse, tags=["Authentication"])
async def login(req: UserLogin):
    user = store.authenticate(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )
    token = generate_token(user["id"], user["email"], user["role"])
    return {
        "token": token,
        "user": store.format_user_out(user)
    }


@router.get("/auth/me", response_model=UserOut, tags=["Authentication"])
async def get_me(current_user: dict = Depends(require_authenticated_user)):
    return store.format_user_out(current_user)


# ==========================================
# SUBSCRIPTION & DEVELOPER GATEWAY ENDPOINTS
# ==========================================

@router.get("/subscriptions/tiers", tags=["Subscriptions"])
async def list_tiers():
    """Returns the 4 canonical subscription tiers with prices in LKR and limits."""
    return store.get_tiers()


@router.get("/subscriptions/quota", response_model=QuotaInfo, tags=["Subscriptions"])
async def get_my_quota(current_user: dict = Depends(require_authenticated_user)):
    return store.get_quota(current_user["id"])


@router.post("/subscriptions/checkout-simulate", response_model=CheckoutResponse, tags=["Subscriptions"])
async def simulate_developer_checkout(
    req: CheckoutSimulateRequest,
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Developer Mock Payment Gateway:
    Processes test checkout in LKR and immediately provisions Plus, Pro, or Ultra tier.
    """
    try:
        res = store.process_developer_checkout(
            user_id=current_user["id"],
            tier=req.tier,
            payment_method=req.payment_method,
            should_fail=req.should_fail or False
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==========================================
# ADMIN MANAGEMENT ENDPOINTS
# ==========================================

@router.get("/admin/users", response_model=List[UserOut], tags=["Admin Management"])
async def admin_list_users(
    search: Optional[str] = None,
    tier: Optional[str] = None,
    admin: dict = Depends(require_admin_user)
):
    """Admin view: search and inspect all users across the system."""
    return store.get_all_users(search=search, tier=tier)


@router.put("/admin/users/{user_id}/subscription", response_model=UserOut, tags=["Admin Management"])
async def admin_update_subscription(
    user_id: str,
    req: AdminUpdateUserSubscription,
    admin: dict = Depends(require_admin_user)
):
    """Admin action: override or change any mechanic's subscription tier."""
    try:
        updated = store.admin_update_subscription(
            target_user_id=user_id,
            new_tier=req.tier,
            reset_usage=req.reset_usage or False
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/admin/metrics", response_model=AdminMetrics, tags=["Admin Management"])
async def admin_metrics(admin: dict = Depends(require_admin_user)):
    """Admin dashboard stats: total users, active paid subs, MRR in LKR, diagnoses today."""
    return store.get_admin_metrics()


@router.put("/admin/tiers/{tier_id}", tags=["Admin Management"])
async def admin_update_tier(
    tier_id: str,
    payload: TierUpdatePayload,
    admin: dict = Depends(require_admin_user)
):
    """
    Admin exclusive: Update subscription price in LKR, diagnostic quota limits, 
    cadence, and details for any tier.
    """
    try:
        data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
        updated = store.update_tier(tier_id, data)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/admin/tiers", tags=["Admin Management"], status_code=status.HTTP_201_CREATED)
async def admin_create_tier(
    payload: TierCreatePayload,
    admin: dict = Depends(require_admin_user)
):
    """
    Admin exclusive: Create a brand new subscription tier with custom price,
    quota limits, cadence, features, and styling.
    """
    try:
        data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
        new_tier = store.create_tier(data)
        return new_tier
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/admin/tiers/{tier_id}", tags=["Admin Management"])
async def admin_delete_tier(
    tier_id: str,
    admin: dict = Depends(require_admin_user)
):
    """
    Admin exclusive: Delete a custom tier (cannot delete standard core tiers).
    """
    try:
        store.delete_tier(tier_id)
        return {"status": "success", "message": f"Tier '{tier_id}' deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


