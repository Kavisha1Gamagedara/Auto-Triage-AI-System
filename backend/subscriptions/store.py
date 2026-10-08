import os
import json
import uuid
import hmac
import hashlib
import base64
import copy
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple

from .schemas import SUBSCRIPTION_TIERS, QuotaInfo, UserOut

STORE_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "subscriptions_db.json")
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "auto-triage-ai-master-secret-key-2026")


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hashes password with SHA256 and unique salt."""
    if not salt:
        salt = uuid.uuid4().hex[:16]
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    new_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(new_hash, hashed)


def generate_token(user_id: str, email: str, role: str) -> str:
    """Generates a secure HMAC-SHA256 signed token."""
    payload = {
        "uid": user_id,
        "em": email,
        "ro": role,
        "iat": datetime.now(timezone.utc).isoformat()
    }
    payload_str = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(SECRET_KEY.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
    return f"{payload_str}.{signature}"


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifies HMAC signature and parses payload."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_str, signature = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_str.encode()).decode())
        return payload
    except Exception:
        return None


class SubscriptionStore:
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.transactions: List[Dict[str, Any]] = []
        self.tiers: Dict[str, Dict[str, Any]] = copy.deepcopy(SUBSCRIPTION_TIERS)
        self._load()
        self._seed_default_accounts()

    def _load(self):
        """Loads data from persistent JSON file."""
        if os.path.exists(STORE_FILE_PATH):
            try:
                with open(STORE_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.users = data.get("users", {})
                    self.transactions = data.get("transactions", [])
                    loaded_tiers = data.get("tiers")
                    if loaded_tiers and isinstance(loaded_tiers, dict):
                        for k, v in loaded_tiers.items():
                            if k in self.tiers:
                                self.tiers[k].update(v)
                            else:
                                self.tiers[k] = v
            except Exception as e:
                print(f"[SubscriptionStore] Error loading local file: {e}")
                self.users = {}
                self.transactions = []

    def _save(self):
        """Persists data to disk atomically."""
        try:
            os.makedirs(os.path.dirname(STORE_FILE_PATH), exist_ok=True)
            with open(STORE_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump({
                    "users": self.users,
                    "transactions": self.transactions,
                    "tiers": self.tiers,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[SubscriptionStore] Failed to save database: {e}")

    def get_tiers(self) -> List[Dict[str, Any]]:
        """Returns current list of active subscription tiers."""
        return list(self.tiers.values())

    def get_tier(self, tier_id: str) -> Optional[Dict[str, Any]]:
        """Gets tier configuration by id."""
        return self.tiers.get(tier_id)

    def update_tier(self, tier_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Admin override: Updates pricing, quota limits, and details for a tier."""
        if tier_id not in self.tiers:
            raise ValueError(f"Subscription tier '{tier_id}' does not exist.")
        tier = self.tiers[tier_id]
        for field in ["price_lkr", "limit", "period", "description", "badge", "name", "is_unlimited"]:
            if field in updates and updates[field] is not None:
                tier[field] = updates[field]
        self._save()
        return tier

    def _seed_default_accounts(self):
        """Seeds initial accounts for quick demo and testing if not existing."""
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Admin Account
        admin_email = "admin@autotriage.io"
        if not any(u.get("email") == admin_email for u in self.users.values()):
            pwd_hash, salt = hash_password("admin123")
            admin_id = "user_admin_001"
            self.users[admin_id] = {
                "id": admin_id,
                "name": "Head of Operations (Admin)",
                "email": admin_email,
                "phone": "+94 11 234 5678",
                "role": "admin",
                "tier": "ultra",
                "workshop_name": "Auto-Triage HQ Command",
                "password_hash": pwd_hash,
                "salt": salt,
                "created_at": now_iso,
                "last_active": now_iso,
                "subscription_status": "active",
                "subscription_expires": None,
                "daily_usage": {},
                "monthly_usage": {},
                "total_usage": 0
            }

        # 2. Mechanic Account (Basic Free - 2 tries/day)
        mech_email = "mechanic@workshop.com"
        if not any(u.get("email") == mech_email for u in self.users.values()):
            pwd_hash, salt = hash_password("mechanic123")
            mech_id = "user_mech_001"
            self.users[mech_id] = {
                "id": mech_id,
                "name": "Kavisha Gamagedara (Master Tech)",
                "email": mech_email,
                "phone": "+94 77 123 4567",
                "role": "mechanic",
                "tier": "basic",
                "workshop_name": "Apex Performance & Diagnostic Lab",
                "password_hash": pwd_hash,
                "salt": salt,
                "created_at": now_iso,
                "last_active": now_iso,
                "subscription_status": "active",
                "subscription_expires": None,
                "daily_usage": {},
                "monthly_usage": {},
                "total_usage": 0
            }

        # 3. Mechanic Account (Plus Tier - 300 tries/mo)
        plus_email = "plus@workshop.com"
        if not any(u.get("email") == plus_email for u in self.users.values()):
            pwd_hash, salt = hash_password("plus123")
            plus_id = "user_plus_001"
            exp_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            self.users[plus_id] = {
                "id": plus_id,
                "name": "Nuwan Perera (Plus Garage)",
                "email": plus_email,
                "phone": "+94 71 987 6543",
                "role": "mechanic",
                "tier": "plus",
                "workshop_name": "Colombo Speed Motors",
                "password_hash": pwd_hash,
                "salt": salt,
                "created_at": now_iso,
                "last_active": now_iso,
                "subscription_status": "active",
                "subscription_expires": exp_date,
                "daily_usage": {},
                "monthly_usage": {},
                "total_usage": 14
            }

        self._save()

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower()
        for u in self.users.values():
            if u.get("email", "").lower() == clean_email:
                return u
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.users.get(user_id)

    def register_user(self, name: str, email: str, phone: str, password: str, workshop_name: Optional[str] = None) -> Dict[str, Any]:
        clean_email = email.strip().lower()
        if self.get_user_by_email(clean_email):
            raise ValueError("A user with this email address is already registered.")

        user_id = f"user_{uuid.uuid4().hex[:12]}"
        pwd_hash, salt = hash_password(password)
        now_iso = datetime.now(timezone.utc).isoformat()

        user_data = {
            "id": user_id,
            "name": name.strip(),
            "email": clean_email,
            "phone": phone.strip(),
            "role": "mechanic",
            "tier": "basic",  # Defaults to Basic free tier (2 tries/day)
            "workshop_name": (workshop_name or "Independent Workshop").strip(),
            "password_hash": pwd_hash,
            "salt": salt,
            "created_at": now_iso,
            "last_active": now_iso,
            "subscription_status": "active",
            "subscription_expires": None,
            "daily_usage": {},
            "monthly_usage": {},
            "total_usage": 0
        }

        self.users[user_id] = user_data
        self._save()
        return user_data

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if verify_password(password, user.get("password_hash", ""), user.get("salt", "")):
            user["last_active"] = datetime.now(timezone.utc).isoformat()
            self._save()
            return user
        return None

    def get_quota(self, user_id: str) -> QuotaInfo:
        user = self.users.get(user_id)
        if not user:
            return QuotaInfo(
                tier="guest",
                limit=0,
                used=0,
                remaining=0,
                period="none",
                is_unlimited=False,
                can_diagnose=False
            )

        tier_id = user.get("tier", "basic")
        tier_cfg = self.tiers.get(tier_id, self.tiers.get("basic", SUBSCRIPTION_TIERS["basic"]))
        is_unlimited = tier_cfg.get("is_unlimited", False) or user.get("role") == "admin"
        limit = tier_cfg.get("limit", 2)
        period = tier_cfg.get("period", "daily")

        now = datetime.now(timezone.utc)
        today_key = now.strftime("%Y-%m-%d")
        month_key = now.strftime("%Y-%m")

        if is_unlimited:
            used = user.get("daily_usage", {}).get(today_key, 0)
            return QuotaInfo(
                tier=tier_id,
                limit=999999,
                used=used,
                remaining=999999,
                period="unlimited",
                is_unlimited=True,
                can_diagnose=True
            )

        if period == "daily":
            used = user.get("daily_usage", {}).get(today_key, 0)
        else:
            used = user.get("monthly_usage", {}).get(month_key, 0)

        remaining = max(0, limit - used)
        can_diagnose = remaining > 0

        return QuotaInfo(
            tier=tier_id,
            limit=limit,
            used=used,
            remaining=remaining,
            period=period,
            is_unlimited=False,
            can_diagnose=can_diagnose
        )

    def record_usage(self, user_id: str) -> QuotaInfo:
        """Increments diagnosis execution quota for user."""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found.")

        now = datetime.now(timezone.utc)
        today_key = now.strftime("%Y-%m-%d")
        month_key = now.strftime("%Y-%m")

        daily_map = user.setdefault("daily_usage", {})
        monthly_map = user.setdefault("monthly_usage", {})

        daily_map[today_key] = daily_map.get(today_key, 0) + 1
        monthly_map[month_key] = monthly_map.get(month_key, 0) + 1
        user["total_usage"] = user.get("total_usage", 0) + 1
        user["last_active"] = now.isoformat()

        self._save()
        return self.get_quota(user_id)

    def process_developer_checkout(self, user_id: str, tier: str, payment_method: str = "card", should_fail: bool = False) -> Dict[str, Any]:
        """Simulates Developer Sandbox Payment Gateway and immediately provisions tier."""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found.")

        if tier not in self.tiers or tier == "basic":
            raise ValueError(f"Invalid subscription upgrade target tier: {tier}")

        tier_info = self.tiers[tier]
        amount_lkr = tier_info["price_lkr"]
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        tx_ref = f"AT-PAY-{now.strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:6].upper()}"

        if should_fail:
            tx_record = {
                "transaction_ref": tx_ref,
                "user_id": user_id,
                "user_email": user["email"],
                "tier": tier,
                "amount_lkr": amount_lkr,
                "payment_method": payment_method,
                "status": "declined",
                "timestamp": now_iso,
                "gateway": "Developer Mock Gateway v2.4 (Simulated Decline)"
            }
            self.transactions.append(tx_record)
            self._save()
            return {
                "success": False,
                "transaction_ref": tx_ref,
                "tier": tier,
                "amount_lkr": amount_lkr,
                "payment_method": payment_method,
                "timestamp": now_iso,
                "message": "Payment simulation was intentionally declined by developer trigger.",
                "user": self.format_user_out(user)
            }

        # Provision 30 days subscription
        expires_at = (now + timedelta(days=30)).isoformat()
        user["tier"] = tier
        user["subscription_status"] = "active"
        user["subscription_expires"] = expires_at

        # Reset month quota for this new purchase
        month_key = now.strftime("%Y-%m")
        user.setdefault("monthly_usage", {})[month_key] = 0

        tx_record = {
            "transaction_ref": tx_ref,
            "user_id": user_id,
            "user_email": user["email"],
            "tier": tier,
            "amount_lkr": amount_lkr,
            "payment_method": payment_method,
            "status": "succeeded",
            "timestamp": now_iso,
            "gateway": "Developer Mock Sandbox Payment Gateway"
        }
        self.transactions.append(tx_record)
        self._save()

        return {
            "success": True,
            "transaction_ref": tx_ref,
            "tier": tier,
            "amount_lkr": amount_lkr,
            "payment_method": payment_method,
            "timestamp": now_iso,
            "message": f"Successfully activated {tier_info['name']} ({amount_lkr:,} LKR/month) via Developer Payment Gateway.",
            "user": self.format_user_out(user)
        }

    def admin_update_subscription(self, target_user_id: str, new_tier: str, reset_usage: bool = False) -> Dict[str, Any]:
        """Admin override to upgrade, downgrade, or reset any user's subscription."""
        user = self.users.get(target_user_id)
        if not user:
            raise ValueError("Target user not found.")

        if new_tier not in self.tiers:
            raise ValueError(f"Unknown tier: {new_tier}")

        user["tier"] = new_tier
        if new_tier == "basic":
            user["subscription_expires"] = None
        else:
            user["subscription_expires"] = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        user["subscription_status"] = "active"

        if reset_usage:
            now = datetime.now(timezone.utc)
            today_key = now.strftime("%Y-%m-%d")
            month_key = now.strftime("%Y-%m")
            user.setdefault("daily_usage", {})[today_key] = 0
            user.setdefault("monthly_usage", {})[month_key] = 0

        self._save()
        return self.format_user_out(user)

    def get_all_users(self, search: Optional[str] = None, tier: Optional[str] = None) -> List[Dict[str, Any]]:
        result = []
        q = (search or "").strip().lower()

        for u in self.users.values():
            if tier and u.get("tier") != tier:
                continue
            if q:
                match = (
                    q in u.get("name", "").lower() or
                    q in u.get("email", "").lower() or
                    q in u.get("phone", "").lower() or
                    q in u.get("workshop_name", "").lower()
                )
                if not match:
                    continue
            result.append(self.format_user_out(u))

        # Sort by creation date descending
        result.sort(key=lambda x: x["created_at"], reverse=True)
        return result

    def get_admin_metrics(self) -> Dict[str, Any]:
        total_users = len(self.users)
        mechanics = sum(1 for u in self.users.values() if u.get("role") == "mechanic")
        admins = sum(1 for u in self.users.values() if u.get("role") == "admin")

        tier_dist = {"basic": 0, "plus": 0, "pro": 0, "ultra": 0}
        mrr = 0
        today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        total_today = 0

        for u in self.users.values():
            t = u.get("tier", "basic")
            tier_dist[t] = tier_dist.get(t, 0) + 1
            if t in self.tiers:
                mrr += self.tiers[t]["price_lkr"]
            total_today += u.get("daily_usage", {}).get(today_key, 0)

        return {
            "total_users": total_users,
            "mechanics_count": mechanics,
            "admins_count": admins,
            "tier_distribution": tier_dist,
            "monthly_recurring_revenue_lkr": mrr,
            "total_diagnoses_today": total_today
        }

    def format_user_out(self, user: Dict[str, Any]) -> Dict[str, Any]:
        quota = self.get_quota(user["id"])
        quota_dict = quota.model_dump() if hasattr(quota, "model_dump") else quota.dict()
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user.get("phone", ""),
            "role": user.get("role", "mechanic"),
            "tier": user.get("tier", "basic"),
            "workshop_name": user.get("workshop_name", "Independent Workshop"),
            "created_at": user.get("created_at", ""),
            "last_active": user.get("last_active", ""),
            "subscription_status": user.get("subscription_status", "active"),
            "subscription_expires": user.get("subscription_expires"),
            "quota": quota_dict
        }


# Singleton instance
store = SubscriptionStore()
