"""
Local & Cloud Workshop Fleet History & Return-Visit Store.
Uses the vehicle registration plate (e.g. 'WP CAB-1234') or JDM Chassis Number (e.g. 'NHP10-2184920')
as the primary key to maintain workshop return-visit diagnostic history.

Architecture: Dual-Mode Resilient Persistence
- Primary: MongoDB Cloud Atlas (collection: 'fleet_history' in 'auto_triage' database)
- Resilient Fallback & Local Mirror: 'backend/data/fleet_history.json'
- Guarantees 0-downtime: if MongoDB is unreachable or offline, the system seamlessly operates on local JSON.
- Writes are mirrored to local JSON for 100% offline parity.

When a vehicle returns to the shop, Agent 1 surfaces:
- Total prior visits count
- Historical DTC fault codes
- Previous root-cause components repaired
- Last visit timestamp and mileage notes
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("fleet_history_store")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
HISTORY_FILE = os.path.join(DATA_DIR, "fleet_history.json")

# Default seed data for Sri Lankan workshops
DEFAULT_SEED_FLEET = {
    "WP CAB-1234": {
        "plate_number": "WP CAB-1234",
        "chassis_number": "NHP10-2091482",
        "make": "Toyota",
        "model": "Aqua",
        "year": 2014,
        "first_registered_at": "2024-03-15T09:30:00Z",
        "total_visits": 2,
        "visits": [
            {
                "visit_index": 1,
                "timestamp": "2024-03-15T09:30:00Z",
                "dtc_codes": ["P0A80"],
                "root_cause_component": "Hybrid Battery Pack",
                "technician_notes": "Hybrid battery reconditioned and cooling fan filter cleaned."
            },
            {
                "visit_index": 2,
                "timestamp": "2024-08-20T14:15:00Z",
                "dtc_codes": ["C1241"],
                "root_cause_component": "12V Auxiliary Battery",
                "technician_notes": "Low auxiliary battery voltage detected; replaced with Amaron AGM battery."
            }
        ]
    },
    "WP CAA-5678": {
        "plate_number": "WP CAA-5678",
        "chassis_number": "RU3-1084921",
        "make": "Honda",
        "model": "Vezel Hybrid",
        "year": 2015,
        "first_registered_at": "2024-05-10T11:00:00Z",
        "total_visits": 1,
        "visits": [
            {
                "visit_index": 1,
                "timestamp": "2024-05-10T11:00:00Z",
                "dtc_codes": ["P0841"],
                "root_cause_component": "Dual-Clutch Transmission Actuator",
                "technician_notes": "Clutch actuator fluid replaced with Honda Ultra Dot 4 and re-learned."
            }
        ]
    }
}


class FleetHistoryStore:
    def __init__(self):
        self._mongo_col = None
        self._mongo_tried = False
        self._ensure_local_store_exists()
        self._init_mongo()

    def _init_mongo(self):
        """Attempts to obtain and verify connection to MongoDB fleet_history collection."""
        try:
            from core.db import get_db
            db = get_db()
            db.command("ping")
            col = db["fleet_history"]
            
            # Ensure indexes on lookup keys
            try:
                col.create_index("plate_number", unique=True, sparse=True)
                col.create_index("chassis_number", sparse=True)
            except Exception:
                pass

            # Auto-seed MongoDB if newly created or empty
            try:
                if col.count_documents({}) == 0:
                    seed_docs = []
                    local_data = self._read_local_file()
                    source = local_data if local_data else DEFAULT_SEED_FLEET
                    for key, val in source.items():
                        doc = dict(val)
                        seed_docs.append(doc)
                    if seed_docs:
                        col.insert_many(seed_docs)
                        logger.info(f"[FleetHistoryStore] Seeded {len(seed_docs)} fleet records into MongoDB Atlas.")
            except Exception as se:
                logger.warning(f"[FleetHistoryStore] Seeding check note: {se}")

            self._mongo_col = col
            self._mongo_tried = True
            logger.info("[FleetHistoryStore] Connected to MongoDB Atlas collection: 'fleet_history'")
        except Exception as e:
            logger.warning(f"[FleetHistoryStore] MongoDB unavailable ({e}). Using Local JSON fallback mode.")
            self._mongo_col = None
            self._mongo_tried = True

    def _get_mongo_collection(self):
        """Returns mongo collection, attempting lazy connect once if not yet tried."""
        if not self._mongo_tried:
            self._init_mongo()
        return self._mongo_col

    def _ensure_local_store_exists(self):
        """Ensures the local JSON fallback store exists with valid seed data."""
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_SEED_FLEET, f, indent=2)
            except Exception as e:
                logger.error(f"[FleetHistoryStore] Failed to create local fleet history file: {e}")

    def _read_local_file(self) -> Dict[str, Any]:
        """Reads local JSON file safely."""
        self._ensure_local_store_exists()
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[FleetHistoryStore] Error reading local fleet file: {e}")
            return {}

    def _write_local_file(self, data: Dict[str, Any]):
        """Writes data to local JSON file safely."""
        self._ensure_local_store_exists()
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[FleetHistoryStore] Error writing to local fleet file: {e}")

    def get_vehicle_history(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Looks up past shop visits for a plate number or chassis code.
        Dual-mode: Checks MongoDB first, falls back to local JSON if offline.
        """
        if not identifier:
            return None

        clean_id = identifier.strip().upper()
        col = self._get_mongo_collection()

        # 1. Attempt MongoDB Lookup
        if col is not None:
            try:
                doc = col.find_one({
                    "$or": [
                        {"plate_number": clean_id},
                        {"chassis_number": clean_id}
                    ]
                })
                if doc:
                    doc.pop("_id", None)
                    return _format_history_summary(doc)
            except Exception as me:
                logger.warning(f"[FleetHistoryStore] MongoDB query failed ({me}), falling back to local JSON.")

        # 2. Resilient Fallback to Local JSON
        local_data = self._read_local_file()
        if clean_id in local_data:
            return _format_history_summary(local_data[clean_id])

        for _, record in local_data.items():
            if record.get("chassis_number", "").upper() == clean_id:
                return _format_history_summary(record)

        return None

    def record_vehicle_visit(
        self,
        identifier: str,
        make: str,
        model: str,
        year: int,
        dtc_codes: List[str],
        chassis_number: Optional[str] = None,
        technician_notes: Optional[str] = None,
        root_cause_component: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records a completed triage session into the fleet database.
        Dual-mode: Saves to MongoDB and mirrors to local JSON file for offline resilience.
        """
        clean_id = identifier.strip().upper()
        clean_chassis = chassis_number.strip().upper() if chassis_number else None
        now_iso = datetime.now(timezone.utc).isoformat()

        # Fetch current record if any from local or Mongo to get prior count
        existing = self.get_vehicle_history(clean_id)
        current_total = existing["total_prior_visits"] if existing else 0
        new_total = current_total + 1

        new_visit = {
            "visit_index": new_total,
            "timestamp": now_iso,
            "dtc_codes": dtc_codes or [],
            "root_cause_component": root_cause_component or "Pending Diagnosis",
            "technician_notes": technician_notes or ""
        }

        # 1. Mirror to Local JSON Store for guaranteed offline parity
        local_data = self._read_local_file()
        if clean_id not in local_data:
            matched_key = None
            if clean_chassis:
                for k, v in local_data.items():
                    if v.get("chassis_number") == clean_chassis:
                        matched_key = k
                        break
            if matched_key:
                entry = local_data[matched_key]
            else:
                entry = {
                    "plate_number": clean_id,
                    "chassis_number": clean_chassis,
                    "make": make,
                    "model": model,
                    "year": year,
                    "first_registered_at": now_iso,
                    "total_visits": 0,
                    "visits": []
                }
                local_data[clean_id] = entry
        else:
            entry = local_data[clean_id]

        entry["total_visits"] = new_total
        entry["visits"].append(new_visit)
        if clean_chassis and not entry.get("chassis_number"):
            entry["chassis_number"] = clean_chassis

        self._write_local_file(local_data)

        # 2. Persist to MongoDB Cloud Atlas (if online)
        col = self._get_mongo_collection()
        if col is not None:
            try:
                query = {
                    "$or": [
                        {"plate_number": clean_id},
                        {"chassis_number": clean_id}
                    ]
                }
                if clean_chassis:
                    query["$or"].append({"chassis_number": clean_chassis})

                existing_doc = col.find_one(query)
                if existing_doc:
                    col.update_one(
                        {"_id": existing_doc["_id"]},
                        {
                            "$set": {
                                "total_visits": new_total,
                                "make": make,
                                "model": model,
                                "year": year,
                                **({"chassis_number": clean_chassis} if clean_chassis else {})
                            },
                            "$push": {"visits": new_visit}
                        }
                    )
                else:
                    new_doc = {
                        "plate_number": clean_id,
                        "chassis_number": clean_chassis,
                        "make": make,
                        "model": model,
                        "year": year,
                        "first_registered_at": now_iso,
                        "total_visits": 1,
                        "visits": [new_visit]
                    }
                    col.insert_one(new_doc)
            except Exception as me:
                logger.error(f"[FleetHistoryStore] Failed to persist visit to MongoDB: {me}")

        return _format_history_summary(entry)

    def get_status(self) -> Dict[str, Any]:
        """Returns the dual-mode operational status."""
        col = self._get_mongo_collection()
        return {
            "mode": "mongodb_atlas" if col is not None else "local_json_fallback",
            "mongodb_connected": col is not None,
            "database": "auto_triage" if col is not None else None,
            "collection": "fleet_history" if col is not None else None,
            "local_backup_file": HISTORY_FILE
        }


def _format_history_summary(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats the raw store record into a clean summary for Agent 1.
    """
    visits = record.get("visits", [])
    all_dtcs = []
    all_components = []
    for v in visits:
        for code in v.get("dtc_codes", []):
            if code not in all_dtcs:
                all_dtcs.append(code)
        comp = v.get("root_cause_component")
        if comp and comp != "Pending Diagnosis" and comp not in all_components:
            all_components.append(comp)

    last_visit = visits[-1] if visits else None

    return {
        "has_prior_history": True,
        "plate_number": record.get("plate_number"),
        "chassis_number": record.get("chassis_number"),
        "total_prior_visits": record.get("total_visits", 0),
        "first_visit_date": record.get("first_registered_at"),
        "last_visit_date": last_visit.get("timestamp") if last_visit else None,
        "historical_dtcs": all_dtcs,
        "previously_repaired_components": all_components,
        "recent_visit_notes": last_visit.get("technician_notes") if last_visit else "",
        "visits": visits
    }


# Singleton instance for application-wide use
_store = FleetHistoryStore()

def get_vehicle_history(identifier: str) -> Optional[Dict[str, Any]]:
    return _store.get_vehicle_history(identifier)

def record_vehicle_visit(
    identifier: str,
    make: str,
    model: str,
    year: int,
    dtc_codes: List[str],
    chassis_number: Optional[str] = None,
    technician_notes: Optional[str] = None,
    root_cause_component: Optional[str] = None
) -> Dict[str, Any]:
    return _store.record_vehicle_visit(
        identifier=identifier,
        make=make,
        model=model,
        year=year,
        dtc_codes=dtc_codes,
        chassis_number=chassis_number,
        technician_notes=technician_notes,
        root_cause_component=root_cause_component
    )

def get_fleet_store_status() -> Dict[str, Any]:
    return _store.get_status()
