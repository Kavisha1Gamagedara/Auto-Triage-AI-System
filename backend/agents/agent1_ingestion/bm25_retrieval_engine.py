"""
Information Retrieval (IR) Engine: Automotive Synset Query Expansion & Okapi BM25 Symptom Scorer.
Academic Justification (IRWA Course & SLIIT Viva 20 Marks):
- Tokenization, Case-Folding & Morphological Stemming
- Inverted Index Construction (Postings lists with Term Frequency $tf_{t,d}$)
- Document Length Normalization & Collection Statistics ($avgdl$, $N$, $df_t$)
- Robertson-Spärck Jones Probabilistic Okapi BM25 Scoring Function
- Vocabulary Mismatch Resolution via Automotive Domain Synset Query Expansion
- Explainable Relevance Attribution (Term-level BM25 Weight Decomposition)
"""

import math
import re
import time
from typing import Dict, List, Any, Optional, Tuple, Set

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None



# 1. Standard English & Colloquial Stopwords
IR_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", 
    "but", "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", 
    "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", 
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", 
    "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", 
    "of", "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", 
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the", 
    "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", 
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", 
    "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would", 
    "you", "your", "yours", "yourself", "yourselves",
    # Conversational fillers
    "customer", "states", "complaint", "noted", "reporting", "driver", "feels", "like", 
    "says", "car", "vehicle", "truck", "suv", "problem", "issue", "got", "getting", "showing"
}


# 2. Automotive Synset Thesaurus (Mechanic Vernacular / Slang to Canonical Diagnostic Terminology)
AUTOMOTIVE_SYNSET_THESAURUS: Dict[str, List[str]] = {
    # Misfire, combustion instability & hesitation
    "jerking": ["engine misfire", "hesitation", "transmission shudder", "cylinder misfire", "P0300"],
    "jerk": ["engine misfire", "hesitation", "shudder", "P0300"],
    "lagging": ["hesitation", "poor throttle response", "delayed acceleration", "lean condition", "P0171"],
    "lag": ["hesitation", "delayed throttle response", "P0171"],
    "knocking": ["engine detonation", "pre ignition", "spark knock", "rod bearing", "P0325"],
    "knock": ["engine detonation", "pre ignition", "spark knock", "P0325"],
    "shuddering": ["engine misfire", "torque converter shudder", "transmission shudder", "P0300"],
    "shudder": ["engine misfire", "hesitation", "transmission shudder", "P0300"],
    "hesitating": ["engine hesitation", "lean misfire", "fuel trim lean", "P0171"],
    "hesitation": ["engine hesitation", "lean misfire", "stumble on acceleration", "P0171"],
    "hesitates": ["engine hesitation", "lean misfire", "fuel starvation", "P0171"],
    "sputtering": ["fuel starvation", "ignition misfire", "unstable idle", "weak fuel pump", "P0300"],
    "sputter": ["fuel starvation", "ignition misfire", "P0300"],
    "bogging down": ["engine hesitation", "lean air fuel mixture", "mass air flow fault", "P0171"],
    "bogging": ["engine hesitation", "lean air fuel ratio", "P0171"],
    "shaking violently": ["severe cylinder misfire", "engine vibration", "rough idle misfire", "P0300"],
    "shakes violently": ["severe cylinder misfire", "engine vibration", "rough idle misfire", "P0300"],
    "rough idle": ["rough idle misfire", "unstable idle speed", "vacuum leak", "P0300", "P0171"],
    "bucking": ["engine surge", "ignition cutout", "severe misfire", "P0300"],
    "chugging": ["engine misfire", "cylinder dead misfire", "fuel starvation", "P0300"],

    # Emissions & exhaust smells
    "rotten eggs smell": ["catalytic converter degradation", "hydrogen sulfide", "sulfur odor", "P0420"],
    "rotten egg smell": ["catalytic converter degradation", "hydrogen sulfide", "sulfur odor", "P0420"],
    "sulfur smell": ["catalytic converter failure", "catalyst washcoat melting", "P0420"],
    "egg smell": ["catalytic converter failure", "hydrogen sulfide odor", "P0420"],
    "black smoke": ["rich fuel mixture", "excess unburned fuel", "stuck open fuel injector", "P0172"],
    "white smoke": ["burning coolant", "head gasket breach", "cylinder coolant leak", "P0128"],
    "blue smoke": ["engine oil burning", "piston ring wear", "valve guide seal leak"],
    "gas smell": ["fuel vapor leak", "evaporative emission purge valve", "P0442", "P0455"],
    "fuel smell": ["fuel vapor leak", "evaporative emission purge valve", "P0442", "P0455"],
    "smells like gas": ["fuel vapor leak", "evaporative emission purge valve", "P0442", "P0455"],
    "smells like fuel": ["fuel vapor leak", "evaporative emission purge valve", "P0442", "P0455"],

    # Airflow, vacuum & intake
    "vacuum leak": ["unmetered intake air leak", "positive fuel trim", "lean condition", "P0171"],
    "hissing sound": ["intake vacuum leak", "intake manifold gasket leak", "P0171"],
    "hissing": ["intake vacuum leak", "boost leak", "P0171"],
    "whistling": ["intake manifold vacuum leak", "turbocharger boost leak", "P0171"],

    # Starting & electrical
    "clicking sound when starting": ["starter motor solenoid", "weak battery voltage", "starter draw"],
    "clicking when starting": ["starter motor solenoid", "weak battery voltage", "starter draw"],
    "slow crank": ["weak starter motor", "discharged 12v battery", "high internal resistance"],
    "wont crank": ["starter failure", "neutral safety switch", "ignition switch open circuit"],
    "won't crank": ["starter failure", "neutral safety switch", "ignition switch open circuit"],

    # Hybrid & EV Powertrain
    "hybrid battery fan loud": ["high voltage battery overheating", "hybrid pack deterioration", "cell voltage delta", "P0A80"],
    "hybrid warning light": ["high voltage battery isolation fault", "hybrid inverter fail", "P0A80", "P0A7A"],
    "ev battery draining fast": ["hybrid battery cell degradation", "capacity degradation", "P0A80"],

    # Brakes & chassis
    "spongy brake": ["air in brake lines", "brake master cylinder failure", "hydraulic pressure loss", "C0035"],
    "spongy pedal": ["air in brake lines", "brake master cylinder failure", "C0035"],
    "clicking sound on turns": ["cv joint failure", "drive axle wear", "constant velocity boot torn"],
    "clicking on turns": ["cv joint failure", "drive axle wear", "constant velocity boot torn"],
    "grinding brakes": ["brake pad metal to metal", "rotor grooved wear", "brake caliper seizure"],
    "squealing brakes": ["brake pad wear indicator", "glazed brake pads", "rotor vibration"],
    "clunking over bumps": ["sway bar bushing", "strut mount failure", "ball joint wear"],

    # Transmission
    "slipping gears": ["transmission slipping", "torque converter clutch", "clutch wear", "P0700", "P0841"],
    "gear slipping": ["transmission slipping", "low fluid pressure", "P0700"],
    "harsh shift": ["transmission control solenoid", "line pressure valve", "P0700"],
    "delayed shift": ["transmission fluid degradation", "valve body sticking", "P0700"],

    # Sri Lankan & South Asian Workshop Vernacular
    "engine missing": ["engine misfire", "cylinder misfire", "spark plug defect", "P0300"],
    "engine miss": ["engine misfire", "cylinder misfire", "P0300"],
    "miss karanawa": ["engine misfire", "cylinder misfire", "P0300"],
    "pickup drop": ["acceleration hesitation", "lean fuel mixture", "mass air flow fault", "P0171", "P0101"],
    "pick up drop": ["acceleration hesitation", "lean fuel mixture", "mass air flow fault", "P0171", "P0101"],
    "loss of pickup": ["acceleration hesitation", "lean condition", "clogged fuel filter", "P0171"],
    "no pickup": ["acceleration hesitation", "poor throttle response", "P0171"],
    "pickup adu": ["poor acceleration", "lean condition", "P0171"],
    "gear slip wenawa": ["transmission slipping", "torque converter clutch", "P0700"],
    "starting trouble": ["no crank no start", "starter motor failure", "battery weak", "U0100"],
    "radiator water boiling": ["engine overheating", "thermostat stuck closed", "radiator boil over", "P0128"],
    "wathura boiling": ["engine overheating", "radiator leak", "P0128"],

    # British & Commonwealth Automotive Vernacular
    "conking out": ["engine stalling", "fuel cut", "crankshaft sensor intermittent", "P0101", "P0300"],
    "conked out": ["engine stalling", "fuel cut", "crankshaft sensor intermittent", "P0101", "P0300"],
    "pinking": ["engine detonation", "spark knock", "pre ignition", "P0325"],
    "spluttering": ["ignition misfire", "fuel starvation", "unstable combustion", "P0300"],
    "splutter": ["ignition misfire", "fuel starvation", "P0300"],
    "hunting idle": ["idle air control valve", "throttle body fluctuation", "vacuum leak", "P0505", "P0171"],
    "hunting": ["idle air control valve fluctuation", "unmetered air", "P0505"],
    "sluggish off the mark": ["poor acceleration from stop", "transmission torque converter slip", "lean stumble", "P0171"],
    "misfiring on all pots": ["multiple cylinder misfire", "ignition coil pack failure", "P0300"],

    # American & Global Colloquialisms
    "dieseling": ["engine dieseling", "after run combustion", "carbon deposit hot spot"],
    "backfiring": ["intake exhaust backfire", "camshaft timing misalignment", "severe misfire", "P0300"],
    "backfire": ["intake exhaust backfire", "camshaft timing misalignment", "severe misfire", "P0300"],
    "limp mode": ["transmission failsafe mode", "reduced engine power", "throttle actuator limp", "P0700"],
    "limp home mode": ["transmission failsafe mode", "reduced engine power", "throttle actuator limp", "P0700"],
    "whining noise": ["alternator diode failure", "power steering pump cavitation", "transmission fluid pump"],
    "whining sound": ["alternator diode failure", "power steering pump cavitation", "transmission fluid pump"],
    "ticking noise": ["hydraulic valve lifter tick", "fuel injector pulse", "low engine oil pressure"],
    "ticking sound": ["hydraulic valve lifter tick", "fuel injector pulse", "low engine oil pressure"],
    "roaring noise": ["wheel bearing hub failure", "tire cupping", "C0035"],
    "roaring sound": ["wheel bearing hub failure", "tire cupping", "C0035"],
    "humming noise": ["wheel bearing hub failure", "differential gear wear", "C0035"],
    "sweet smell": ["engine coolant leak", "radiator leak", "heater core breach", "P0128"],
    "sweet coolant smell": ["engine coolant leak", "radiator leak", "heater core breach", "P0128"],
    "burning oil smell": ["engine oil burning", "valve cover gasket leak on exhaust", "piston rings"],
    "burning rubber smell": ["serpentine belt slipping", "accessory pulley seized", "tire rubbing"],
    "clunking into gear": ["broken engine mount", "transmission mount", "u-joint driveline play"],
    "pedal sinking to floor": ["brake master cylinder bypass", "brake fluid hydraulic leak", "C0035"]
}


# 3. Official Diagnostic Trouble Code Corpus (Documents indexed into Inverted Index)
OFFICIAL_DTC_CORPUS: List[Dict[str, Any]] = [
    {
        "code": "P0171",
        "title": "System Too Lean (Bank 1)",
        "system": "Powertrain",
        "subsystem": "Fuel and Air Metering",
        "symptoms": [
            "engine hesitation", "rough idle", "lean misfire", "bogging down", "loss of power",
            "shuddering on acceleration", "engine surging", "stumble", "fuel trim high",
            "positive long term fuel trim", "intake vacuum leak", "unmetered air leak",
            "dirty mass air flow maf sensor", "weak fuel pump", "clogged fuel injector"
        ],
        "causes": [
            "intake manifold gasket leak", "cracked vacuum hose", "dirty mass air flow sensor",
            "low fuel pressure", "clogged fuel filter", "faulty front upstream oxygen sensor"
        ]
    },
    {
        "code": "P0172",
        "title": "System Too Rich (Bank 1)",
        "system": "Powertrain",
        "subsystem": "Fuel and Air Metering",
        "symptoms": [
            "black exhaust smoke", "strong fuel smell", "smells like gas", "rich fuel mixture",
            "high fuel consumption", "sooty spark plugs", "engine rough running", "stumbling idle",
            "negative fuel trim", "flooded engine", "excess fuel injection"
        ],
        "causes": [
            "leaking stuck open fuel injector", "faulty fuel pressure regulator", "restricted engine air filter",
            "faulty oxygen sensor", "evap canister purge valve stuck open"
        ]
    },
    {
        "code": "P0174",
        "title": "System Too Lean (Bank 2)",
        "system": "Powertrain",
        "subsystem": "Fuel and Air Metering",
        "symptoms": [
            "engine hesitation", "rough idle", "lean misfire bank 2", "bogging down", "v6 v8 lean condition",
            "vacuum leak", "fuel trim positive bank 2", "loss of power"
        ],
        "causes": [
            "bank 2 intake manifold vacuum leak", "dirty maf sensor", "bank 2 injector restriction"
        ]
    },
    {
        "code": "P0300",
        "title": "Random or Multiple Cylinder Misfire Detected",
        "system": "Powertrain",
        "subsystem": "Ignition and Misfire Detection",
        "symptoms": [
            "engine misfire", "jerking", "violent shuddering", "shakes violently at red lights",
            "engine shaking", "flashing check engine light", "loss of acceleration power",
            "unstable idle", "engine stumble", "sputtering", "bucking", "chugging", "exhaust popping",
            "unburnt fuel exhaust odor"
        ],
        "causes": [
            "worn fouled spark plugs", "failing ignition coils", "clogged fuel injectors",
            "low fuel pressure", "severe intake vacuum leak", "low engine compression"
        ]
    },
    {
        "code": "P0301",
        "title": "Cylinder 1 Misfire Detected",
        "system": "Powertrain",
        "subsystem": "Ignition and Misfire Detection",
        "symptoms": [
            "cylinder 1 misfire", "engine jerking", "rough idle", "engine shuddering", "spark plug 1 cracked",
            "cylinder 1 ignition coil failure", "cylinder 1 dead misfire", "loss of acceleration power"
        ],
        "causes": [
            "cylinder 1 spark plug defect", "cylinder 1 ignition coil failure", "cylinder 1 injector clog", "compression loss"
        ]
    },
    {
        "code": "P0302",
        "title": "Cylinder 2 Misfire Detected",
        "system": "Powertrain",
        "subsystem": "Ignition and Misfire Detection",
        "symptoms": [
            "cylinder 2 misfire", "engine jerking", "rough idle", "shuddering", "ignition coil 2 defect", "spark plug 2"
        ],
        "causes": [
            "cylinder 2 spark plug", "cylinder 2 coil pack", "cylinder 2 fuel injector"
        ]
    },
    {
        "code": "P0303",
        "title": "Cylinder 3 Misfire Detected",
        "system": "Powertrain",
        "subsystem": "Ignition and Misfire Detection",
        "symptoms": [
            "cylinder 3 misfire", "engine jerking", "rough idle", "shuddering", "ignition coil 3 defect", "spark plug 3"
        ],
        "causes": [
            "cylinder 3 spark plug", "cylinder 3 coil pack", "cylinder 3 fuel injector"
        ]
    },
    {
        "code": "P0304",
        "title": "Cylinder 4 Misfire Detected",
        "system": "Powertrain",
        "subsystem": "Ignition and Misfire Detection",
        "symptoms": [
            "cylinder 4 misfire", "engine jerking", "rough idle", "shuddering", "ignition coil 4 defect", "spark plug 4"
        ],
        "causes": [
            "cylinder 4 spark plug", "cylinder 4 coil pack", "cylinder 4 fuel injector"
        ]
    },
    {
        "code": "P0420",
        "title": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "system": "Powertrain",
        "subsystem": "Auxiliary Emission Controls",
        "symptoms": [
            "rotten eggs smell", "sulfur odor in exhaust", "catalytic converter failure",
            "exhaust restriction", "sluggish acceleration", "failed emissions smog test",
            "rattling noise from catalytic converter substrate", "unburnt hydrocarbon buildup"
        ],
        "causes": [
            "catalytic converter precious metal washcoat degradation", "chronic engine misfire thermal damage",
            "engine coolant or oil poisoning catalyst", "downstream rear oxygen sensor failure", "exhaust leak before catalyst"
        ]
    },
    {
        "code": "P0430",
        "title": "Catalyst System Efficiency Below Threshold (Bank 2)",
        "system": "Powertrain",
        "subsystem": "Auxiliary Emission Controls",
        "symptoms": [
            "rotten egg smell bank 2", "sulfur odor", "catalyst converter degradation", "sluggish acceleration"
        ],
        "causes": [
            "bank 2 catalytic converter failure", "downstream bank 2 o2 sensor defect"
        ]
    },
    {
        "code": "P0101",
        "title": "Mass or Volume Air Flow (MAF) Circuit Range/Performance",
        "system": "Powertrain",
        "subsystem": "Fuel and Air Metering",
        "symptoms": [
            "erratic engine idle", "engine stalling when stopping", "hard starting", "poor acceleration",
            "black exhaust smoke", "hesitation on throttle application", "hissing air sound"
        ],
        "causes": [
            "dirty contaminated mass air flow maf sensor wire", "cracked intake air boot duct",
            "unmetered vacuum air leak", "restricted air filter box"
        ]
    },
    {
        "code": "P0113",
        "title": "Intake Air Temperature (IAT) Circuit High Input",
        "system": "Powertrain",
        "subsystem": "Fuel and Air Metering",
        "symptoms": [
            "hard starting in cold weather", "poor fuel economy", "engine pinging knock", "hesitation"
        ],
        "causes": [
            "iat sensor disconnected or open circuit", "broken wiring harness", "internal sensor element failure"
        ]
    },
    {
        "code": "P0128",
        "title": "Coolant Thermostat (Coolant Temp Below Regulating Temp)",
        "system": "Powertrain",
        "subsystem": "Cooling System",
        "symptoms": [
            "engine takes too long to warm up", "cabin heater blowing lukewarm or cool air", "engine running cold",
            "reduced fuel mileage", "radiator fan running continuously", "temperature gauge low"
        ],
        "causes": [
            "thermostat stuck open", "faulty engine coolant temperature ect sensor", "low coolant level"
        ]
    },
    {
        "code": "P0442",
        "title": "EVAP Control System Small Leak Detected",
        "system": "Powertrain",
        "subsystem": "Evaporative Emissions",
        "symptoms": [
            "gas smell near fuel tank", "fuel vapor smell", "check engine light on after fueling",
            "no noticeable drivability symptoms"
        ],
        "causes": [
            "loose damaged or cracked gas fuel cap", "small crack in evap vapor hose", "leaking purge solenoid valve", "vent valve leak"
        ]
    },
    {
        "code": "P0455",
        "title": "EVAP Control System Gross/Large Leak Detected",
        "system": "Powertrain",
        "subsystem": "Evaporative Emissions",
        "symptoms": [
            "strong gasoline vapor odor", "fuel smell near filler neck", "large evaporative emission leak"
        ],
        "causes": [
            "missing or unlatched gas cap", "disconnected evap line", "stuck open vent control solenoid"
        ]
    },
    {
        "code": "P0700",
        "title": "Transmission Control System (TCM) Malfunction",
        "system": "Powertrain",
        "subsystem": "Automatic Transmission",
        "symptoms": [
            "transmission slipping gears", "delayed gear engagement", "harsh shifting thud", "stuck in limp home mode",
            "refuses to shift past 3rd gear", "transmission shudder under load"
        ],
        "causes": [
            "tcm transmission control module internal fault", "faulty transmission shift solenoid", "low transmission fluid level", "burnt atf fluid"
        ]
    },
    {
        "code": "P0841",
        "title": "Transmission Fluid Pressure Sensor/Switch 'A' Circuit Range/Performance",
        "system": "Powertrain",
        "subsystem": "Automatic Transmission",
        "symptoms": [
            "transmission slipping", "harsh gear shifts", "transmission fluid temperature warning", "erratic cvt ratio change"
        ],
        "causes": [
            "contaminated degraded transmission fluid", "defective fluid pressure sensor switch", "clogged valve body passage"
        ]
    },
    {
        "code": "P0A80",
        "title": "Replace Hybrid Battery Pack (Internal Degradation)",
        "system": "Hybrid / EV",
        "subsystem": "High Voltage Battery Management",
        "symptoms": [
            "hybrid system warning light check hybrid system", "high voltage battery cooling fan running on high loud",
            "rapid battery state of charge soc fluctuation", "sluggish hybrid acceleration", "ice engine running continuously",
            "high battery cell voltage delta block difference"
        ],
        "causes": [
            "nickel metal hydride ni-mh cell module capacity loss", "high internal resistance in hybrid cells",
            "corroded battery copper busbar terminals", "weak weak hybrid block voltage"
        ]
    },
    {
        "code": "P0A7A",
        "title": "Generator Inverter Performance Malfunction",
        "system": "Hybrid / EV",
        "subsystem": "Power Control Unit / Inverter",
        "symptoms": [
            "hybrid system shutdown while driving", "ready light turns off", "master warning triangle on", "inverter high temperature warning"
        ],
        "causes": [
            "electric inverter water pump failure", "air bubble in hybrid inverter cooling system", "igbt transistor thermal runaway"
        ]
    },
    {
        "code": "C0035",
        "title": "Left Front Wheel Speed Sensor Circuit",
        "system": "Chassis",
        "subsystem": "Anti-Lock Braking System (ABS) & Traction",
        "symptoms": [
            "abs warning light illuminated", "traction control vsc light on", "spongy brake pedal pulsation on dry pavement",
            "abnormal abs activation while stopping"
        ],
        "causes": [
            "damaged wheel speed sensor harness", "chipped tone ring reluctor wheel", "wheel bearing hub play"
        ]
    },
    {
        "code": "B0001",
        "title": "Driver Airbag Squib Circuit Open",
        "system": "Body",
        "subsystem": "Restraints and SRS Airbag",
        "symptoms": [
            "airbag srs warning light staying on", "horn or steering wheel controls inoperative"
        ],
        "causes": [
            "broken steering clockspring spiral cable", "loose connector under steering column", "defective airbag squib"
        ]
    },
    {
        "code": "U0100",
        "title": "Lost Communication With ECM / PCM 'A'",
        "system": "Network Communication",
        "subsystem": "CAN Bus Telemetry",
        "symptoms": [
            "engine no crank no start", "dashboard warning lights all flashing christmas tree", "scan tool cannot communicate with engine ecu",
            "intermittent engine stalling"
        ],
        "causes": [
            "can bus twisted pair wire shorted or open", "blown ecm power relay or fuse", "poor ecm ground connection", "failed engine computer"
        ]
    }
]


# 4. Text Processing Functions (Tokenization & Stemming)
def _simple_stem(word: str) -> str:
    """
    Morphological suffix stripper for basic stemming.
    Reduces morphological variants:
    misfiring -> misfir, misfires -> misfir, shuddering -> shudder,
    hesitation -> hesitat, smelling -> smell.
    """
    w = word.lower()
    # Strip common suffixes
    if w.endswith("sses"):
        return w[:-2]
    if w.endswith("ies"):
        return w[:-3] + "y"
    if w.endswith("ss"):
        return w
    if w.endswith("ing") and len(w) > 5:
        return w[:-3]
    if w.endswith("tion") and len(w) > 6:
        return w[:-4] + "t"
    if w.endswith("ly") and len(w) > 4:
        return w[:-2]
    if w.endswith("ed") and len(w) > 4:
        return w[:-2]
    if w.endswith("es") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
        return w[:-1]
    return w


def tokenize_and_preprocess(text: str, stem: bool = True) -> List[str]:
    """
    IR Tokenization Pipeline:
    1. Lowercase normalization
    2. Alphanumeric regex boundary tokenization
    3. Stopword removal
    4. Suffix stemming
    """
    if not text or not isinstance(text, str):
        return []

    tokens = re.findall(r"\b[a-z0-9\-_]{2,}\b", text.lower())
    processed = []
    for tok in tokens:
        if tok not in IR_STOPWORDS:
            stemmed = _simple_stem(tok) if stem else tok
            if stemmed and stemmed not in IR_STOPWORDS and len(stemmed) >= 2:
                processed.append(stemmed)
    return processed


# 5. Automotive Synset Query Expansion Engine
def expand_automotive_query(raw_query: str) -> Dict[str, Any]:
    """
    Expands vernacular mechanic complaints using domain synsets.
    Bridges the Vocabulary Mismatch Problem in Information Retrieval.
    
    Returns:
        {
            "original_query": str,
            "expanded_terms": List[str],
            "expanded_query": str,
            "synsets_triggered": List[Dict[str, Any]]
        }
    """
    if not raw_query or not raw_query.strip():
        return {
            "original_query": raw_query or "",
            "expanded_terms": [],
            "expanded_query": "",
            "synsets_triggered": []
        }

    text_lower = raw_query.lower()
    triggered: List[Dict[str, Any]] = []
    added_terms: List[str] = []

    # Sort synset phrases by length descending to match multi-word expressions first
    sorted_phrases = sorted(AUTOMOTIVE_SYNSET_THESAURUS.keys(), key=lambda s: len(s), reverse=True)

    matched_phrases = set()
    for phrase in sorted_phrases:
        if phrase in text_lower:
            # Prevent sub-phrase overlap duplication (e.g. "rotten eggs smell" vs "egg smell")
            if any(phrase in existing for existing in matched_phrases):
                continue
            matched_phrases.add(phrase)

            synonyms = AUTOMOTIVE_SYNSET_THESAURUS[phrase]
            triggered.append({
                "trigger_phrase": phrase,
                "synonyms": synonyms
            })
            for syn in synonyms:
                added_terms.append(syn)

    # Phase 2: Fuzzy Typo-Tolerant Slang Matching (RapidFuzz edit distance)
    if fuzz is not None:
        query_words = re.findall(r"\b[a-z]{4,}\b", text_lower)
        single_word_synsets = [k for k in AUTOMOTIVE_SYNSET_THESAURUS.keys() if " " not in k]

        for q_word in query_words:
            if any(q_word in mp for mp in matched_phrases) or q_word in IR_STOPWORDS:
                continue

            for target_slang in single_word_synsets:
                if target_slang in matched_phrases:
                    continue
                sim = fuzz.ratio(q_word, target_slang)
                if sim >= 84.0 and abs(len(q_word) - len(target_slang)) <= 2:
                    matched_phrases.add(target_slang)
                    synonyms = AUTOMOTIVE_SYNSET_THESAURUS[target_slang]
                    triggered.append({
                        "trigger_phrase": f"{q_word} (~{target_slang})",
                        "synonyms": synonyms,
                        "fuzzy_match": True,
                        "similarity": round(float(sim), 1)
                    })
                    for syn in synonyms:
                        added_terms.append(syn)
                    break

    # Synthesize canonical expanded query string
    if added_terms:
        expanded_query_str = f"{raw_query.strip()} {' '.join(added_terms)}"
    else:
        expanded_query_str = raw_query.strip()

    return {
        "original_query": raw_query.strip(),
        "expanded_terms": list(dict.fromkeys(added_terms)),  # Deduplicate while preserving order
        "expanded_query": expanded_query_str,
        "synsets_triggered": triggered
    }


# 6. Okapi BM25 Diagnostic Inverted Index
class BM25DiagnosticEngine:
    """
    In-Memory Inverted Index and Okapi BM25 Ranking Engine for Diagnostic Trouble Codes.
    
    Mathematical Formulation:
    - Inverted Postings: term -> {doc_id: term_frequency}
    - Robertson-Spärck Jones IDF: log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
    - Okapi BM25 RSV:
      score(D, Q) = sum_{t in Q} [ IDF(t) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (|D| / avgdl))) ]
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.doc_ids: List[str] = []
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.total_docs: int = 0
        
        # Inverted Index: term -> dict of (doc_id -> tf)
        self.inverted_index: Dict[str, Dict[str, int]] = {}
        # Document Frequencies: term -> df
        self.df: Dict[str, int] = {}
        # Precomputed IDFs: term -> idf
        self.idf: Dict[str, float] = {}

        # Build inverted index immediately from official DTC corpus
        self._build_index(OFFICIAL_DTC_CORPUS)

    def _build_index(self, corpus: List[Dict[str, Any]]):
        """Constructs the inverted index, document lengths, and Robertson-Spärck Jones IDF table."""
        self.documents.clear()
        self.doc_ids.clear()
        self.doc_lengths.clear()
        self.inverted_index.clear()
        self.df.clear()
        self.idf.clear()

        total_tokens = 0

        for doc in corpus:
            doc_id = doc["code"]
            self.documents[doc_id] = doc
            self.doc_ids.append(doc_id)

            # Consolidate rich text representation
            content_parts = [
                doc["code"],
                doc["title"],
                doc["system"],
                doc.get("subsystem", ""),
                " ".join(doc.get("symptoms", [])),
                " ".join(doc.get("causes", []))
            ]
            full_text = " ".join(content_parts)

            tokens = tokenize_and_preprocess(full_text)
            doc_len = len(tokens)
            self.doc_lengths[doc_id] = doc_len
            total_tokens += doc_len

            # Populate term frequencies and inverted posting list
            tf_map: Dict[str, int] = {}
            for tok in tokens:
                tf_map[tok] = tf_map.get(tok, 0) + 1

            for tok, freq in tf_map.items():
                if tok not in self.inverted_index:
                    self.inverted_index[tok] = {}
                self.inverted_index[tok][doc_id] = freq

        self.total_docs = len(self.doc_ids)
        self.avg_doc_length = total_tokens / self.total_docs if self.total_docs > 0 else 1.0

        # Precompute Robertson-Spärck Jones IDF for all vocabulary terms
        # Formula: IDF(t) = ln(1.0 + (N - df + 0.5) / (df + 0.5))
        for tok, postings in self.inverted_index.items():
            df_val = len(postings)
            self.df[tok] = df_val
            idf_val = math.log(1.0 + (self.total_docs - df_val + 0.5) / (df_val + 0.5))
            self.idf[tok] = max(0.05, idf_val)  # Floor to small positive to avoid negative IDFs

    def rank(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Calculates Okapi BM25 relevance scores for all candidate DTC documents against query.
        Returns explainable ranked documents with term contributions.
        """
        query_tokens = tokenize_and_preprocess(query)
        if not query_tokens:
            return []

        # Candidate accumulation and term attribution
        doc_scores: Dict[str, float] = {doc_id: 0.0 for doc_id in self.doc_ids}
        doc_matched_terms: Dict[str, Set[str]] = {doc_id: set() for doc_id in self.doc_ids}
        doc_term_contribs: Dict[str, Dict[str, float]] = {doc_id: {} for doc_id in self.doc_ids}

        # Query term frequency in query
        q_tf: Dict[str, int] = {}
        for qt in query_tokens:
            q_tf[qt] = q_tf.get(qt, 0) + 1

        for term, q_freq in q_tf.items():
            if term not in self.inverted_index:
                continue

            term_idf = self.idf[term]
            postings = self.inverted_index[term]

            for doc_id, tf in postings.items():
                doc_len = self.doc_lengths[doc_id]
                # Length normalization component
                len_norm = 1.0 - self.b + self.b * (doc_len / self.avg_doc_length)
                # BM25 term weight
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * len_norm
                term_score = term_idf * (numerator / denominator)

                doc_scores[doc_id] += term_score
                doc_matched_terms[doc_id].add(term)
                doc_term_contribs[doc_id][term] = round(term_score, 2)

        # Filter documents with score > 0 and sort descending
        ranked = [
            (doc_id, score) for doc_id, score in doc_scores.items() if score > 0.1
        ]
        ranked.sort(key=lambda x: x[1], reverse=True)

        max_score = ranked[0][1] if ranked else 1.0

        results: List[Dict[str, Any]] = []
        for doc_id, raw_score in ranked[:top_k]:
            doc_meta = self.documents[doc_id]
            norm_score = min(100.0, round((raw_score / max_score) * 100.0, 1))

            tier = "High Confidence" if norm_score >= 80 else ("Probable Candidate" if norm_score >= 50 else "Correlated")

            results.append({
                "dtc_code": doc_id,
                "title": doc_meta["title"],
                "system": doc_meta["system"],
                "subsystem": doc_meta.get("subsystem", ""),
                "bm25_score": round(raw_score, 3),
                "normalized_score": norm_score,
                "confidence_tier": tier,
                "matched_terms": sorted(list(doc_matched_terms[doc_id])),
                "term_contributions": doc_term_contribs[doc_id]
            })

        return results


# Global Singleton BM25 Index Instance
_GLOBAL_BM25_ENGINE: Optional[BM25DiagnosticEngine] = None


def get_bm25_engine() -> BM25DiagnosticEngine:
    global _GLOBAL_BM25_ENGINE
    if _GLOBAL_BM25_ENGINE is None:
        _GLOBAL_BM25_ENGINE = BM25DiagnosticEngine()
    return _GLOBAL_BM25_ENGINE


def search_dtc_bm25(query_text: str, top_k: int = 5, expand_synonyms: bool = True) -> Dict[str, Any]:
    """
    End-to-end Information Retrieval pipeline for diagnostic symptom matching:
    1. Automotive synset query expansion
    2. Okapi BM25 inverted index ranking
    3. Explainable term weight contribution breakdown
    """
    t0 = time.perf_counter()
    engine = get_bm25_engine()

    expansion_meta = expand_automotive_query(query_text) if expand_synonyms else {
        "original_query": query_text,
        "expanded_terms": [],
        "expanded_query": query_text,
        "synsets_triggered": []
    }

    effective_query = expansion_meta["expanded_query"]
    ranked_matches = engine.rank(effective_query, top_k=top_k)

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    # 4. Academic Evaluation: Lexical Overlap & Neural Fallback Assessment
    top_score = ranked_matches[0]["bm25_score"] if ranked_matches else 0.0
    if top_score >= 10.0:
        coverage_status = "HIGH_CONFIDENCE_LEXICAL_MATCH"
        coverage_note = "Strong lexical and synset intersection with official DTC diagnostic index."
    elif top_score >= 4.0:
        coverage_status = "MODERATE_LEXICAL_MATCH"
        coverage_note = "Moderate symptom overlap found in inverted index."
    else:
        coverage_status = "LOW_LEXICAL_OVERLAP_FALLBACK_RECOMMENDED"
        coverage_note = "Symptom vocabulary is novel or out-of-index. Delegated to Agent 2 Cognitive LLM for semantic reasoning."

    return {
        "query_expansion": expansion_meta,
        "top_matches": ranked_matches,
        "corpus_size": engine.total_docs,
        "avg_doc_length": round(engine.avg_doc_length, 2),
        "execution_time_ms": elapsed_ms,
        "coverage_status": coverage_status,
        "coverage_note": coverage_note,
        "method": "Okapi BM25 with Automotive Synset Query Expansion"
    }

