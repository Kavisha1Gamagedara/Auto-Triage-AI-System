"""
Local Workshop Fleet History & Return-Visit Store.
Uses the vehicle registration plate (e.g. 'WP CAB-1234') or JDM Chassis Number (e.g. 'NHP10-2184920')
as the primary key to maintain local workshop return-visit diagnostic history.

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


def _ensure_store_exists():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        initial_data = {
            # Seed with common Sri Lankan return-visit vehicles for immediate testing
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
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to create fleet history store: {e}")


def get_vehicle_history(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Looks up past shop visits for a plate number or chassis code.
    """
    if not identifier:
        return None

    _ensure_store_exists()
    clean_id = identifier.strip().upper()

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Direct lookup by plate key
        if clean_id in data:
            record = data[clean_id]
            return _format_history_summary(record)

        # Lookup by chassis key
        for _, record in data.items():
            if record.get("chassis_number", "").upper() == clean_id:
                return _format_history_summary(record)

    except Exception as e:
        logger.error(f"Error reading fleet history: {e}")

    return None


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
    """
    Records a completed triage session into the local fleet database.
    """
    _ensure_store_exists()
    clean_id = identifier.strip().upper()

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    now_iso = datetime.now(timezone.utc).isoformat()

    if clean_id not in data:
        data[clean_id] = {
            "plate_number": clean_id,
            "chassis_number": chassis_number.strip().upper() if chassis_number else None,
            "make": make,
            "model": model,
            "year": year,
            "first_registered_at": now_iso,
            "total_visits": 0,
            "visits": []
        }

    vehicle_entry = data[clean_id]
    vehicle_entry["total_visits"] += 1
    new_visit = {
        "visit_index": vehicle_entry["total_visits"],
        "timestamp": now_iso,
        "dtc_codes": dtc_codes or [],
        "root_cause_component": root_cause_component or "Pending Diagnosis",
        "technician_notes": technician_notes or ""
    }
    vehicle_entry["visits"].append(new_visit)

    # Update chassis if available
    if chassis_number and not vehicle_entry.get("chassis_number"):
        vehicle_entry["chassis_number"] = chassis_number.strip().upper()

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save fleet visit: {e}")

    return _format_history_summary(vehicle_entry)


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
