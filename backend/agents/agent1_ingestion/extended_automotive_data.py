"""
Agent 1 Extended Automotive Data:
Comprehensive knowledge base covering:
- Global, JDM, and European Vehicle Make/Model Registry (NHTSA fallback)
- JDM Chassis/Frame Number Format Validator
- Modern Electric Vehicle (EV), Hybrid, and ADAS Component Lexicons
- Hybrid / EV OBD-II Diagnostic Trouble Codes (DTC) Taxonomy & Descriptions
- Hybrid / High-Voltage & Electrical Causal Cascade Propagation Rules
"""

import re
from typing import Dict, List, Set, Tuple, Optional, Any

# ==============================================================================
# 1. GLOBAL VEHICLE MAKE & MODEL CATALOG (Covers JDM, European, Asian & Global)
# ==============================================================================
GLOBAL_VEHICLE_CATALOG: Dict[str, List[str]] = {
    "toyota": [
        "premio", "allion", "townace", "vitz", "axio", "fielder", "hiace", "hilux",
        "aqua", "passo", "rush", "noah", "voxy", "harrier", "crown", "yaris", "corolla",
        "camry", "prius", "prius c", "prius prime", "rav4", "highlander", "tacoma",
        "tundra", "4runner", "c-hr", "bz4x", "land cruiser", "land cruiser prado",
        "alphard", "vellfire", "sienta", "rumion", "auris", "avensis", "fortuner"
    ],
    "honda": [
        "civic", "accord", "cr-v", "fit", "jazz", "vezel", "freed", "shuttle",
        "insight", "grace", "city", "pilot", "odyssey", "stepwgn", "cr-z", "hr-v",
        "h-rv", "element", "ridgeline", "passport", "s2000", "e:np1", "prologue"
    ],
    "nissan": [
        "altima", "sentra", "rogue", "leaf", "note", "dayz", "serena", "caravan",
        "x-trail", "qashqai", "juke", "pathfinder", "frontier", "navara", "march",
        "kicks", "ariya", "maxima", "murano", "patrol", "tiida", "wingroad", "sylphy"
    ],
    "suzuki": [
        "wagon r", "alto", "spacia", "swift", "baleno", "vitara", "jimny", "celerio",
        "sx4", "s-cross", "ertiga", "dzire", "hustler", "every", "carry", "ignis", "solio"
    ],
    "mitsubishi": [
        "outlander", "pajero", "montero", "pajero sport", "l200", "triton", "eclipse cross",
        "asx", "rvr", "mirage", "attrage", "lancer", "lancer evolution", "delica", "ek wagon", "ek space"
    ],
    "mazda": [
        "mazda2", "mazda3", "mazda6", "cx-3", "cx-5", "cx-30", "cx-50", "cx-60", "cx-9",
        "cx-90", "mx-5", "mx-5 miata", "flair", "demio", "axela", "atenza", "biante"
    ],
    "daihatsu": [
        "mira", "mira e:s", "move", "tanto", "hijet", "hijet cargo", "rocky", "terios",
        "cast", "wake", "thor", "taft", "boon", "sirion", "copen"
    ],
    "hyundai": [
        "elantra", "sonata", "tucson", "santa fe", "ioniq", "ioniq 5", "ioniq 6", "kona",
        "venue", "accent", "i10", "i20", "i30", "creta", "palisade", "santa cruz", "staria"
    ],
    "kia": [
        "optima", "k5", "forte", "sportage", "sorento", "ev6", "ev9", "soul", "niro",
        "rio", "seltos", "stonic", "carnival", "telluride", "picanto", "ceed", "cerato"
    ],
    "ford": [
        "f-150", "f-250", "f-350", "mustang", "mustang mach-e", "explorer", "escape",
        "ranger", "bronco", "bronco sport", "edge", "expedition", "focus", "fiesta",
        "transit", "transit custom", "mondeo", "kuga", "everest"
    ],
    "chevrolet": [
        "silverado", "malibu", "equinox", "tahoe", "suburban", "colorado", "traverse",
        "blazer", "bolt", "bolt ev", "bolt euv", "camaro", "trax", "cruze", "spark", "impala"
    ],
    "subaru": [
        "outback", "forester", "impreza", "crosstrek", "legacy", "wrx", "brz", "ascent",
        "solterra", "levorg", "xv"
    ],
    "volkswagen": [
        "golf", "jetta", "passat", "tiguan", "atlas", "id.4", "id.3", "polo", "arteon",
        "taos", "touareg", "t-roc", "t-cross", "transporter", "caddy"
    ],
    "bmw": [
        "3 series", "5 series", "7 series", "1 series", "2 series", "4 series",
        "x1", "x2", "x3", "x4", "x5", "x6", "x7", "i4", "i7", "ix", "ix3", "m3", "m5"
    ],
    "mercedes-benz": [
        "c-class", "e-class", "s-class", "a-class", "b-class", "cla", "cls",
        "glc", "gle", "gls", "g-class", "eqe", "eqs", "eqa", "eqb", "vito", "sprinter"
    ],
    "audi": [
        "a1", "a3", "a4", "a5", "a6", "a7", "a8", "q2", "q3", "q5", "q7", "q8",
        "e-tron", "q4 e-tron", "rs3", "rs6"
    ],
    "volvo": [
        "xc40", "xc60", "xc90", "s60", "s90", "v60", "v90", "ex30", "ex90", "c40"
    ],
    "tesla": [
        "model 3", "model y", "model s", "model x", "cybertruck", "roadster"
    ],
    "renault": [
        "clio", "megane", "captur", "kadjar", "duster", "kwid", "zoe", "arkana", "koleos"
    ],
    "peugeot": [
        "208", "308", "508", "2008", "3008", "5008", "partner", "expert", "boxer", "e-208"
    ],
    "byd": [
        "atto 3", "seal", "dolphin", "song plus", "tang", "han", "yuan plus", "seagull"
    ]
}


def is_recognized_global_vehicle(make: str, model: str) -> bool:
    """
    Validates vehicle make and model against the global catalog (including JDM / European).
    Allows exact token containment and typo ratio matching.
    """
    if not make or not model:
        return False

    clean_make = make.strip().lower()
    clean_model = model.strip().lower()

    models = GLOBAL_VEHICLE_CATALOG.get(clean_make)
    if not models:
        # Check alias (e.g. chevy -> chevrolet, vw -> volkswagen)
        alias_map = {"chevy": "chevrolet", "vw": "volkswagen", "merc": "mercedes-benz", "mercedes": "mercedes-benz"}
        clean_make = alias_map.get(clean_make, clean_make)
        models = GLOBAL_VEHICLE_CATALOG.get(clean_make)

    if not models:
        return False

    # 1. Exact match or token match
    if clean_model in models:
        return True

    for m in models:
        if clean_model == m or clean_model in m.split() or m in clean_model:
            return True

    # 2. Fuzzy approximate check
    try:
        from rapidfuzz import process, fuzz
        best_match, score, _ = process.extractOne(clean_model, models, scorer=fuzz.ratio)
        if score >= 80.0:
            return True
    except Exception:
        pass

    return False


# ==============================================================================
# 2. JDM CHASSIS / FRAME NUMBER VALIDATION
# ==============================================================================
# Japanese Chassis numbers typically have the format:
# [Prefix]-[ModelCode]-[6-8 digits], e.g. "DBA-ZRT260-3021948", "NZE141-1029482", "E-EG6-1002345"
JDM_CHASSIS_REGEX = re.compile(
    r"^(?:(?:DAA|DBA|CBA|UA|E|GH|ABA|6AA|5BA|3BA|CAA|4AA)-)?([A-Z0-9]{3,7})-([0-9]{6,8})$",
    re.IGNORECASE
)


def is_jdm_chassis_number(raw_string: str) -> bool:
    """
    Returns True if raw_string matches standard Japanese Domestic Market chassis/frame number format.
    """
    if not raw_string or not isinstance(raw_string, str):
        return False
    clean = raw_string.strip().upper()
    return bool(JDM_CHASSIS_REGEX.match(clean))


def validate_chassis_or_vin(identifier: str) -> Dict[str, Any]:
    """
    Unified validator for both 17-character ISO 3779 VINs and Japanese Chassis / Frame numbers.
    """
    if not identifier or not isinstance(identifier, str):
        return {"is_valid": False, "type": "unknown", "clean_id": "", "error": "Identifier is empty"}

    clean_id = identifier.strip().upper()

    # Case 1: Japanese Chassis Number
    if is_jdm_chassis_number(clean_id):
        match = JDM_CHASSIS_REGEX.match(clean_id)
        model_code = match.group(1) if match else ""
        serial_no = match.group(2) if match else ""
        return {
            "is_valid": True,
            "type": "jdm_chassis",
            "clean_id": clean_id,
            "model_code": model_code,
            "serial_number": serial_no,
            "error": None
        }

    # Case 2: Standard 17-character VIN
    return {
        "is_valid": len(clean_id) == 17,
        "type": "vin_iso3779",
        "clean_id": clean_id,
        "error": None if len(clean_id) == 17 else f"Invalid length ({len(clean_id)}) for standard 17-char VIN"
    }


# ==============================================================================
# 2.1 POPULAR SRI LANKAN JDM CHASSIS / MODEL CODE MECHANICAL REGISTRY
# ==============================================================================
JDM_CHASSIS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "NHP10": {
        "make": "Toyota",
        "model": "Aqua",
        "years": "2011-2021",
        "engine_code": "1NZ-FXE",
        "engine_displacement": "1.5L Atkinson Cycle",
        "drivetrain": "Hybrid (FWD)",
        "transmission": "e-CVT (P510 Planetary)",
        "hv_battery": "144V Ni-MH (0.9 kWh, 20 modules)",
        "inverter": "G9200-52011 Inverter/Converter",
        "dealer_campaigns": [
            "Toyota Lanka Free Campaign: Brake Booster Pump & Accumulator Assembly (ABS warning light/spongy pedal)",
            "Toyota Global Campaign: Hybrid Inverter Intelligent Power Module (IPM) Software Reflash"
        ]
    },
    "MXPK11": {
        "make": "Toyota",
        "model": "Aqua",
        "years": "2021-present",
        "engine_code": "M15A-FXE",
        "engine_displacement": "1.5L Dynamic Force 3-Cylinder",
        "drivetrain": "Hybrid (FWD)",
        "transmission": "e-CVT",
        "hv_battery": "Bipolar Nickel-Hydrogen (Ni-MH)",
        "inverter": "Toyota Dynamic Inverter Unit",
        "dealer_campaigns": []
    },
    "RU3": {
        "make": "Honda",
        "model": "Vezel Hybrid",
        "years": "2013-2020",
        "engine_code": "LEB-H1",
        "engine_displacement": "1.5L i-VTEC Earth Dreams DOHC",
        "drivetrain": "Hybrid (FWD)",
        "transmission": "7-Speed i-DCD Dual Clutch Transmission",
        "hv_battery": "Lithium-Ion IPU (0.86 kWh)",
        "inverter": "Integrated Power Unit (IPU)",
        "dealer_campaigns": [
            "Stafford Motors Service Bulletin: i-DCD Dual-Clutch Actuator Fluid Deterioration & Transmission Overheating Software Reflash",
            "Stafford Motors Service Bulletin: Electric Water Pump Diagnostic Update"
        ]
    },
    "RU1": {
        "make": "Honda",
        "model": "Vezel",
        "years": "2013-2020",
        "engine_code": "L15B",
        "engine_displacement": "1.5L i-VTEC Petrol",
        "drivetrain": "FWD",
        "transmission": "CVT",
        "hv_battery": None,
        "inverter": None,
        "dealer_campaigns": []
    },
    "GP5": {
        "make": "Honda",
        "model": "Fit Hybrid",
        "years": "2013-2020",
        "engine_code": "LEB-H1",
        "engine_displacement": "1.5L i-VTEC Earth Dreams DOHC",
        "drivetrain": "Hybrid (FWD)",
        "transmission": "7-Speed i-DCD Dual Clutch Transmission",
        "hv_battery": "Lithium-Ion IPU (0.86 kWh)",
        "inverter": "Integrated Power Unit (IPU)",
        "dealer_campaigns": [
            "Stafford Motors Service Bulletin: i-DCD Dual-Clutch Transmission Software Reflash & Actuator Service"
        ]
    },
    "GM4": {
        "make": "Honda",
        "model": "Grace Hybrid",
        "years": "2014-2020",
        "engine_code": "LEB-H1",
        "engine_displacement": "1.5L i-VTEC Earth Dreams DOHC",
        "drivetrain": "Hybrid (FWD)",
        "transmission": "7-Speed i-DCD Dual Clutch Transmission",
        "hv_battery": "Lithium-Ion IPU",
        "inverter": "Integrated Power Unit (IPU)",
        "dealer_campaigns": [
            "Stafford Motors Service Bulletin: i-DCD Dual-Clutch Fluid Diagnostic Check"
        ]
    },
    "MH34S": {
        "make": "Suzuki",
        "model": "Wagon R",
        "years": "2012-2017",
        "engine_code": "R06A",
        "engine_displacement": "660cc 3-Cylinder DOHC",
        "drivetrain": "ENE-CHARGE Mild Hybrid",
        "transmission": "CVT",
        "hv_battery": "Lithium-Ion Auxiliary Battery (under passenger seat)",
        "inverter": "High-Efficiency Alternator / Charge Controller",
        "dealer_campaigns": []
    },
    "MH44S": {
        "make": "Suzuki",
        "model": "Wagon R",
        "years": "2014-2017",
        "engine_code": "R06A",
        "engine_displacement": "660cc 3-Cylinder DOHC S-ENE Charge",
        "drivetrain": "S-ENE Charge (ISG Motor)",
        "transmission": "CVT",
        "hv_battery": "Lithium-Ion Auxiliary Battery",
        "inverter": "Integrated Starter Generator (ISG)",
        "dealer_campaigns": [
            "AMW Service Advisory: ISG Drive Belt Tension & Lithium Auxiliary Battery Diagnostic Check"
        ]
    },
    "MH55S": {
        "make": "Suzuki",
        "model": "Wagon R",
        "years": "2017-present",
        "engine_code": "R06A",
        "engine_displacement": "660cc 3-Cylinder Mild Hybrid",
        "drivetrain": "Mild Hybrid (ISG Motor)",
        "transmission": "CVT",
        "hv_battery": "Lithium-Ion Auxiliary Battery",
        "inverter": "ISG Motor Generator",
        "dealer_campaigns": []
    },
    "ZVW30": {
        "make": "Toyota",
        "model": "Prius",
        "years": "2009-2015",
        "engine_code": "2ZR-FXE",
        "engine_displacement": "1.8L DOHC Atkinson Cycle",
        "drivetrain": "Hybrid (FWD)",
        "transmission": "e-CVT (P410 Planetary)",
        "hv_battery": "201.6V Ni-MH (1.3 kWh, 28 modules)",
        "inverter": "G9200-47140 Inverter/Converter",
        "dealer_campaigns": [
            "Toyota Lanka Free Campaign: Brake Booster Master Cylinder & Pump Accumulator (C1246/C1391 pressure loss)",
            "Toyota Global Campaign: Hybrid Inverter IPM Transistor Thermal Overheat Protection"
        ]
    },
    "ZVW50": {
        "make": "Toyota",
        "model": "Prius",
        "years": "2015-2022",
        "engine_code": "2ZR-FXE",
        "engine_displacement": "1.8L DOHC Atkinson Cycle",
        "drivetrain": "Hybrid (FWD)",
        "transmission": "e-CVT (P610 Planetary)",
        "hv_battery": "Lithium-Ion / Ni-MH",
        "inverter": "Toyota 4th Gen Inverter Assembly",
        "dealer_campaigns": []
    },
    "NKE165": {
        "make": "Toyota",
        "model": "Corolla Axio Hybrid",
        "years": "2013-2020",
        "engine_code": "1NZ-FXE",
        "engine_displacement": "1.5L Atkinson Cycle Hybrid",
        "drivetrain": "Hybrid (FWD)",
        "transmission": "e-CVT",
        "hv_battery": "144V Ni-MH",
        "inverter": "G9200 Inverter/Converter",
        "dealer_campaigns": []
    },
    "NZE161": {
        "make": "Toyota",
        "model": "Corolla Axio",
        "years": "2012-2020",
        "engine_code": "1NZ-FE",
        "engine_displacement": "1.5L Petrol DOHC",
        "drivetrain": "FWD",
        "transmission": "Super CVT-i",
        "hv_battery": None,
        "inverter": None,
        "dealer_campaigns": []
    },
    "NZE141": {
        "make": "Toyota",
        "model": "Corolla Axio",
        "years": "2006-2012",
        "engine_code": "1NZ-FE",
        "engine_displacement": "1.5L Petrol DOHC",
        "drivetrain": "FWD",
        "transmission": "Super CVT-i",
        "hv_battery": None,
        "inverter": None,
        "dealer_campaigns": []
    },
    "ZRT260": {
        "make": "Toyota",
        "model": "Premio",
        "years": "2007-2021",
        "engine_code": "2ZR-FE / 2ZR-FAE",
        "engine_displacement": "1.8L Valvematic Petrol",
        "drivetrain": "FWD",
        "transmission": "Super CVT-i",
        "hv_battery": None,
        "inverter": None,
        "dealer_campaigns": []
    },
    "NZT260": {
        "make": "Toyota",
        "model": "Premio",
        "years": "2007-2021",
        "engine_code": "1NZ-FE",
        "engine_displacement": "1.5L DOHC Petrol",
        "drivetrain": "FWD",
        "transmission": "Super CVT-i",
        "hv_battery": None,
        "inverter": None,
        "dealer_campaigns": []
    },
    "KSP130": {
        "make": "Toyota",
        "model": "Vitz",
        "years": "2010-2020",
        "engine_code": "1KR-FE",
        "engine_displacement": "1.0L 3-Cylinder Petrol",
        "drivetrain": "FWD",
        "transmission": "Super CVT-i",
        "hv_battery": None,
        "inverter": None,
        "dealer_campaigns": []
    },
    "NSP130": {
        "make": "Toyota",
        "model": "Vitz",
        "years": "2010-2020",
        "engine_code": "1NR-FKE",
        "engine_displacement": "1.3L 4-Cylinder Petrol",
        "drivetrain": "FWD",
        "transmission": "Super CVT-i",
        "hv_battery": None,
        "inverter": None,
        "dealer_campaigns": []
    },
    "A200A": {
        "make": "Toyota",
        "model": "Raize",
        "years": "2019-present",
        "engine_code": "1KR-VET",
        "engine_displacement": "1.0L 3-Cylinder Turbo",
        "drivetrain": "FWD",
        "transmission": "D-CVT",
        "hv_battery": None,
        "inverter": None,
        "dealer_campaigns": []
    },
    "ZE1": {
        "make": "Nissan",
        "model": "Leaf EV",
        "years": "2017-present",
        "engine_code": "EM57 Motor",
        "engine_displacement": "110kW / 160kW Pure Electric",
        "drivetrain": "BEV (FWD)",
        "transmission": "Single-Speed Reduction Gear",
        "hv_battery": "40 kWh / 62 kWh Laminated Lithium-Ion",
        "inverter": "Nissan Integrated Inverter Module",
        "dealer_campaigns": []
    },
    "AZE0": {
        "make": "Nissan",
        "model": "Leaf EV",
        "years": "2012-2017",
        "engine_code": "EM57 Motor",
        "engine_displacement": "80kW Pure Electric",
        "drivetrain": "BEV (FWD)",
        "transmission": "Single-Speed Reduction Gear",
        "hv_battery": "24 kWh / 30 kWh Lithium-Ion",
        "inverter": "Nissan PDM / Inverter Assembly",
        "dealer_campaigns": []
    },
    "HE12": {
        "make": "Nissan",
        "model": "Note e-Power",
        "years": "2016-2020",
        "engine_code": "HR12DE + EM57",
        "engine_displacement": "1.2L 3-Cylinder Series Hybrid",
        "drivetrain": "e-Power Electric Drive (FWD)",
        "transmission": "Single-Speed Reduction Gear",
        "hv_battery": "1.5 kWh Lithium-Ion Drive Battery",
        "inverter": "e-Power Integrated Inverter",
        "dealer_campaigns": []
    }
}


def lookup_jdm_chassis_specs(identifier_or_text: str) -> Optional[Dict[str, Any]]:
    """
    Scans a string (chassis number, model code, or query text) to find and extract JDM specifications.
    E.g. 'NHP10', 'DBA-ZRT260-3021948', 'Toyota Aqua NHP10 2015' -> returns full mechanical specs.
    """
    if not identifier_or_text or not isinstance(identifier_or_text, str):
        return None

    clean = identifier_or_text.strip().upper()

    # 1. Exact or partial match with known model codes in registry
    for code, specs in JDM_CHASSIS_REGISTRY.items():
        # Match whole word model code (e.g. NHP10 in 'Aqua NHP10' or in 'DAA-NHP10-2184920')
        if re.search(rf"\b{re.escape(code)}\b", clean):
            return {
                "model_code": code,
                "found_in_registry": True,
                **specs
            }

    # 2. Extract model code from JDM chassis pattern e.g. DAA-ZVW30-1234567
    m = JDM_CHASSIS_REGEX.match(clean)
    if m:
        extracted_code = m.group(1).upper()
        if extracted_code in JDM_CHASSIS_REGISTRY:
            return {
                "model_code": extracted_code,
                "found_in_registry": True,
                **JDM_CHASSIS_REGISTRY[extracted_code]
            }
        return {
            "model_code": extracted_code,
            "found_in_registry": False,
            "make": "JDM Vehicle",
            "model": extracted_code,
            "dealer_campaigns": []
        }

    return None



# ==============================================================================
# 3. MODERN EV, HYBRID & ADAS PHYSICAL COMPONENTS
# ==============================================================================
EV_HYBRID_ADAS_COMPONENTS: List[str] = [
    # High-Voltage Powertrain & Battery
    "traction battery",
    "hybrid battery",
    "high voltage battery",
    "battery module",
    "battery cell",
    "battery management system",
    "bms",
    "inverter",
    "converter",
    "dc-dc converter",
    "inverter converter",
    "onboard charger",
    "obc",
    "charge port",
    "charging port",
    "high voltage contactor",
    "contactor",
    "precharge relay",
    "high voltage service plug",
    "service plug",
    "safety plug",
    "high voltage interlock",
    "high voltage cable",
    "motor generator",
    "electric drive motor",
    "traction motor",
    "mg1",
    "mg2",
    "electric transaxle",
    # Thermal Management for EV / Hybrid
    "inverter coolant pump",
    "inverter water pump",
    "electric water pump",
    "battery chiller",
    "battery cooling fan",
    "heat pump",
    "electric ac compressor",
    # Braking & Regeneration
    "regenerative brake",
    "regenerative braking actuator",
    "brake stroke sensor",
    "brake actuator",
    # Advanced Driver Assistance Systems (ADAS) & Sensors
    "radar sensor",
    "millimeter wave radar",
    "front camera",
    "adas camera",
    "forward collision camera",
    "lidar sensor",
    "ultrasonic sensor",
    "parking sensor",
    "blind spot monitor",
    "lane keep assist camera",
    "steering angle sensor"
]


# ==============================================================================
# 4. EXTENDED DTC TAXONOMY & DESCRIPTIONS (HYBRID, EV & OEM SPECIFIC)
# ==============================================================================
EXTENDED_DTC_TAXONOMY: Dict[str, Dict[str, str]] = {
    "P0A": {"family": "P0A00", "family_name": "Hybrid / EV Propulsion System", "system": "High Voltage Powertrain"},
    "P0B": {"family": "P0B00", "family_name": "Hybrid Battery Energy Storage", "system": "High Voltage Powertrain"},
    "P0C": {"family": "P0C00", "family_name": "Hybrid / EV Inverter & Motor Drive", "system": "High Voltage Powertrain"},
    "P1":  {"family": "P1000", "family_name": "Manufacturer Controlled Powertrain", "system": "Powertrain (Manufacturer Specific)"},
    "P2":  {"family": "P2000", "family_name": "Fuel and Air Metering Auxiliary Control", "system": "Powertrain"},
    "P3":  {"family": "P3000", "family_name": "Hybrid Battery Control & Aux Powertrain", "system": "High Voltage Powertrain"},
    "U1":  {"family": "U1000", "family_name": "Manufacturer Controlled CAN Network Communication", "system": "Network Communication"}
}

EXTENDED_DTC_DESCRIPTIONS: Dict[str, str] = {
    # High Voltage Battery & Hybrid Management
    "P0A80": "Replace Hybrid Battery Pack",
    "P0A7F": "Hybrid Battery Pack Deterioration",
    "P0A93": "Inverter Cooling System Performance",
    "P0A7A": "Generator Inverter Performance",
    "P0A94": "DC-DC Converter Performance",
    "P0AA6": "Hybrid / EV Battery Voltage System Isolation Fault",
    "P0A0D": "High Voltage System Interlock Circuit High",
    "P0A1F": "Battery Energy Control Module (BECM) Performance",
    "P0B3C": "High Voltage Battery Voltage Sense Circuit Low",
    "P0C73": "Motor Electronics Coolant Pump 'A' Control Performance",
    
    # Toyota / Lexus / Honda Hybrid OEM codes
    "P3000": "High Voltage Battery Control System Malfunction",
    "P3006": "High Voltage Battery SOC (State of Charge) Highly Uneven",
    "P3009": "High Voltage Power Leak to Vehicle Chassis Detected",
    "P3011": "Battery Block 1 Malfunction / Delta Voltage High",
    "P3012": "Battery Block 2 Malfunction / Delta Voltage High",
    "P3190": "Poor Engine Power Output (Hybrid ICE Limp Mode)",
    "P3191": "Engine Does Not Start (Hybrid System Failure)",

    # Common OEM Specific Combustion & Electrical Codes
    "P1259": "VTEC System Malfunction (Bank 1)",
    "P1450": "Unable to Bleed Fuel Tank Vacuum (EVAP System)",
    "P1135": "Air-Fuel Ratio Sensor Heater Circuit Malfunction (Bank 1 Sensor 1)",
    "P1155": "Air-Fuel Ratio Sensor Heater Circuit Malfunction (Bank 2 Sensor 1)",
    "P0560": "System Voltage Malfunction",
    "P0562": "System Voltage Low (12V Auxiliary Rail)",
    "P0563": "System Voltage High (12V Auxiliary Rail)",

    # High-Speed CAN Network & Module Timeout Codes
    "U0100": "Lost Communication with ECM / PCM 'A'",
    "U0111": "Lost Communication with Battery Energy Control Module 'A'",
    "U0129": "Lost Communication with Brake System Control Module (Regen / ABS)",
    "U0140": "Lost Communication with Body Control Module (BCM)",
    "U0298": "Lost Communication with DC-DC Converter Control Module 'A'",
    "U1000": "Class 2 Communication Malfunction / CAN Communication Circuit"
}


# ==============================================================================
# 5. HYBRID, EV & ELECTRICAL CAUSAL CASCADE RULES
# ==============================================================================
EXTENDED_DTC_CASCADE_RULES: List[Tuple[Tuple[str, ...], Tuple[str, ...], str]] = [
    # 1. Inverter Coolant Pump Failure -> Inverter Overtemperature
    (
        ("P0A93", "P0C73"),
        ("P0A7A", "P0A94"),
        "Inverter electric water pump impeller stall stops coolant circulation, causing IGBT switching transistor thermal runaway and triggering inverter overtemperature fail-safe."
    ),
    # 2. High Voltage Isolation Leak -> System Shutdown / Contactor Open
    (
        ("P0AA6", "P3009"),
        ("P3000", "P0A80"),
        "High voltage direct current leakage exceeding 10mA to the vehicle unibody chassis triggers isolation fault detection, commanding high voltage safety contactors to disconnect and disabling Ready mode."
    ),
    # 3. Hybrid Battery Cell Deterioration -> Master Battery System Derate
    (
        ("P0A80", "P0A7F", "P3006", "P3011", "P3012"),
        ("P3000", "P3190"),
        "Internal resistance and delta capacity imbalance (>0.3V) across NiMH/Li-Ion cell blocks triggers battery degradation limits, prompting the ECM to derate propulsion power."
    ),
    # 4. Low 12V Auxiliary Battery Rail -> Multi-ECU CAN Network Dropouts
    (
        ("P0562", "P0560"),
        ("U0100", "U0111", "U0129", "U1000"),
        "12V auxiliary AGM/lead-acid battery voltage dipping below 9.6V brown-outs automotive microcontrollers, terminating CAN bus differential signaling and producing cascading module communication loss."
    ),
    # 5. VTEC Hydraulic Pressure Starvation -> Variable Timing Failure
    (
        ("P0524", "P0520"),
        ("P1259",),
        "Insufficient engine oil lubrication pressure starves hydraulic timing spool actuators, preventing VTEC rocker arm synchronization pins from locking into high-lift cam profiles."
    )
]
