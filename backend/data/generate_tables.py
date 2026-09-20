#!/usr/bin/env python3
"""
generate_tables.py — regenerates the five Agent 4 source CSVs.

Output: parts.csv, generations.csv, part_aliases.csv, bom_dependencies.csv,
        safety_rules.csv

Covers 100 vehicle generations weighted toward the Sri Lankan market
(JDM used imports, Indian makes, Chinese/Malaysian budget marques, and the
European models common in Colombo).

PRICING IS SYNTHETIC. Every parts row carries source="ESTIMATED - segment
scaled, not a surveyed market price". Overwrite the demo rows with verified
ikman.lk figures before showing this to anyone.
"""

import csv
import os

OUT = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 1. VEHICLES  (make, model, generation, year_from, year_to, segment, factor)
#    factor scales part prices relative to a compact-sedan baseline of 1.0
# ---------------------------------------------------------------------------

VEHICLES = [
    # --- Toyota: the backbone of the Sri Lankan fleet -----------------------
    ("Toyota", "Aqua",          "NHP10",   2011, 2021, "hybrid",    0.95),
    ("Toyota", "Aqua",          "MXPK10",  2021, 2025, "hybrid",    1.15),
    ("Toyota", "Vitz",          "XP130",   2010, 2020, "hatchback", 0.85),
    ("Toyota", "Vitz",          "XP90",    2005, 2010, "hatchback", 0.80),
    ("Toyota", "Yaris",         "XP210",   2020, 2025, "hatchback", 1.00),
    ("Toyota", "Corolla",       "E210",    2018, 2024, "sedan",     1.10),
    ("Toyota", "Corolla",       "E170",    2013, 2018, "sedan",     1.00),
    ("Toyota", "Corolla",       "E140",    2006, 2013, "sedan",     0.90),
    ("Toyota", "Axio",          "E160",    2012, 2021, "sedan",     1.00),
    ("Toyota", "Premio",        "T260",    2007, 2021, "sedan",     1.15),
    ("Toyota", "Allion",        "T260",    2007, 2021, "sedan",     1.15),
    ("Toyota", "Prius",         "XW30",    2009, 2015, "hybrid",    1.05),
    ("Toyota", "Prius",         "XW50",    2015, 2022, "hybrid",    1.25),
    ("Toyota", "CHR",           "AX10",    2016, 2023, "crossover", 1.30),
    ("Toyota", "Passo",         "M700",    2016, 2023, "hatchback", 0.85),
    ("Toyota", "Belta",         "XP90",    2005, 2012, "sedan",     0.90),
    ("Toyota", "Raize",         "A200",    2019, 2025, "crossover", 1.15),
    ("Toyota", "Rush",          "F800",    2017, 2024, "suv",       1.35),
    ("Toyota", "Hilux",         "AN120",   2015, 2024, "pickup",    1.55),
    ("Toyota", "Land Cruiser",  "J200",    2007, 2021, "luxury",    2.40),
    ("Toyota", "Land Cruiser Prado", "J150", 2009, 2024, "suv",     2.00),
    ("Toyota", "Hiace",         "H200",    2004, 2019, "van",       1.40),
    ("Toyota", "Vios",          "XP150",   2013, 2022, "sedan",     0.95),

    # --- Honda --------------------------------------------------------------
    ("Honda", "Fit",            "GK",      2013, 2020, "hatchback", 0.95),
    ("Honda", "Fit",            "GE",      2007, 2013, "hatchback", 0.85),
    ("Honda", "Fit",            "GR",      2020, 2025, "hatchback", 1.10),
    ("Honda", "Vezel",          "RU",      2013, 2021, "crossover", 1.25),
    ("Honda", "Vezel",          "RV",      2021, 2025, "crossover", 1.45),
    ("Honda", "Grace",          "GM4",     2014, 2020, "sedan",     1.05),
    ("Honda", "Civic",          "FC",      2015, 2021, "sedan",     1.30),
    ("Honda", "Civic",          "FD",      2005, 2011, "sedan",     1.05),
    ("Honda", "Civic",          "FE",      2021, 2025, "sedan",     1.50),
    ("Honda", "Insight",        "ZE2",     2009, 2014, "hybrid",    0.95),
    ("Honda", "CR-V",           "RW",      2016, 2022, "suv",       1.55),
    ("Honda", "Freed",          "GB5",     2016, 2024, "van",       1.15),
    ("Honda", "City",           "GM6",     2014, 2020, "sedan",     1.00),
    ("Honda", "Shuttle",        "GP7",     2015, 2022, "hatchback", 1.05),

    # --- Suzuki (Japan + Maruti India) --------------------------------------
    ("Suzuki", "Wagon R",       "MH55",    2017, 2024, "kei",       0.70),
    ("Suzuki", "Wagon R",       "MH34",    2012, 2017, "kei",       0.65),
    ("Suzuki", "Alto",          "HA36",    2014, 2021, "kei",       0.60),
    ("Suzuki", "Alto",          "HA25",    2009, 2014, "kei",       0.55),
    ("Suzuki", "Alto 800",      "AGS",     2012, 2022, "kei",       0.55),
    ("Suzuki", "Swift",         "ZC83",    2017, 2024, "hatchback", 0.90),
    ("Suzuki", "Swift",         "ZC72",    2010, 2017, "hatchback", 0.80),
    ("Suzuki", "Celerio",       "LF",      2014, 2021, "hatchback", 0.70),
    ("Suzuki", "Baleno",        "WB",      2015, 2022, "hatchback", 0.85),
    ("Suzuki", "Spacia",        "MK53",    2017, 2023, "kei",       0.75),
    ("Suzuki", "Every",         "DA17",    2015, 2024, "van",       0.80),
    ("Suzuki", "Vitara",        "LY",      2015, 2024, "crossover", 1.35),
    ("Suzuki", "Jimny",         "JB74",    2018, 2025, "suv",       1.40),
    ("Suzuki", "Dzire",         "ZC31",    2017, 2024, "sedan",     0.85),

    # --- Nissan -------------------------------------------------------------
    ("Nissan", "Leaf",          "ZE1",     2017, 2024, "ev",        1.30),
    ("Nissan", "Leaf",          "ZE0",     2010, 2017, "ev",        1.10),
    ("Nissan", "March",         "K13",     2010, 2022, "hatchback", 0.80),
    ("Nissan", "Note",          "E12",     2012, 2020, "hatchback", 0.90),
    ("Nissan", "Sunny",         "N17",     2011, 2020, "sedan",     0.90),
    ("Nissan", "X-Trail",       "T32",     2013, 2022, "suv",       1.50),
    ("Nissan", "Caravan",       "E26",     2012, 2024, "van",       1.35),
    ("Nissan", "Navara",        "D23",     2014, 2024, "pickup",    1.50),

    # --- Mitsubishi ---------------------------------------------------------
    ("Mitsubishi", "Lancer",    "CY",      2007, 2017, "sedan",     1.05),
    ("Mitsubishi", "Outlander", "GF",      2012, 2021, "suv",       1.50),
    ("Mitsubishi", "Montero Sport", "QF",  2015, 2024, "suv",       1.75),
    ("Mitsubishi", "Pajero",    "V80",     2006, 2021, "suv",       1.80),
    ("Mitsubishi", "L200",      "KL",      2015, 2024, "pickup",    1.50),

    # --- Mazda --------------------------------------------------------------
    ("Mazda", "Demio",          "DJ",      2014, 2022, "hatchback", 0.95),
    ("Mazda", "Demio",          "DE",      2007, 2014, "hatchback", 0.85),
    ("Mazda", "Axela",          "BM",      2013, 2019, "sedan",     1.15),
    ("Mazda", "CX-5",           "KF",      2017, 2024, "suv",       1.55),
    ("Mazda", "CX-3",           "DK",      2015, 2023, "crossover", 1.30),

    # --- Daihatsu -----------------------------------------------------------
    ("Daihatsu", "Mira",        "LA300",   2011, 2018, "kei",       0.60),
    ("Daihatsu", "Move",        "LA150",   2014, 2022, "kei",       0.65),
    ("Daihatsu", "Terios",      "J210",    2006, 2017, "suv",       1.20),
    ("Daihatsu", "Hijet",       "S500",    2014, 2024, "van",       0.75),

    # --- Micro (Sri Lankan assembly) ----------------------------------------
    ("Micro", "Panda",          "MP1",     2010, 2018, "hatchback", 0.60),
    ("Micro", "Emgrand 7",      "EC7",     2013, 2021, "sedan",     0.80),
    ("Micro", "Trend",          "MT1",     2014, 2020, "crossover", 0.85),

    # --- Perodua ------------------------------------------------------------
    ("Perodua", "Axia",         "B200",    2014, 2022, "hatchback", 0.65),
    ("Perodua", "Bezza",        "B300",    2016, 2024, "sedan",     0.70),
    ("Perodua", "Viva",         "L251",    2007, 2014, "kei",       0.55),

    # --- Tata ---------------------------------------------------------------
    ("Tata", "Nano",            "BSIV",    2008, 2018, "kei",       0.45),
    ("Tata", "Indica",          "Vista",   2008, 2016, "hatchback", 0.60),
    ("Tata", "Xenon",           "XT",      2010, 2020, "pickup",    1.05),
    ("Tata", "Ace",             "HT",      2005, 2024, "van",       0.70),

    # --- Mahindra -----------------------------------------------------------
    ("Mahindra", "Bolero",      "MDI",     2011, 2022, "suv",       1.05),
    ("Mahindra", "Scorpio",     "S11",     2014, 2022, "suv",       1.30),
    ("Mahindra", "KUV100",      "NXT",     2016, 2023, "crossover", 0.85),
    ("Mahindra", "Thar",        "CJ",      2010, 2020, "suv",       1.25),

    # --- Hyundai ------------------------------------------------------------
    ("Hyundai", "Eon",          "HA",      2011, 2019, "kei",       0.60),
    ("Hyundai", "Accent",       "RB",      2010, 2019, "sedan",     0.90),
    ("Hyundai", "Elantra",      "AD",      2015, 2020, "sedan",     1.20),
    ("Hyundai", "Tucson",       "TL",      2015, 2020, "suv",       1.50),
    ("Hyundai", "Grand i10",    "BA",      2013, 2020, "hatchback", 0.75),

    # --- Kia ----------------------------------------------------------------
    ("Kia", "Picanto",          "JA",      2017, 2024, "hatchback", 0.75),
    ("Kia", "Sportage",         "QL",      2015, 2021, "suv",       1.50),
    ("Kia", "Sorento",          "UM",      2014, 2020, "suv",       1.70),
    ("Kia", "Rio",              "YB",      2011, 2017, "hatchback", 0.85),

    # --- European / luxury, common in Colombo -------------------------------
    ("BMW", "3 Series",         "F30",     2011, 2019, "luxury",    2.30),
    ("BMW", "X1",               "F48",     2015, 2022, "luxury",    2.40),
    ("Mercedes-Benz", "C-Class", "W205",   2014, 2021, "luxury",    2.50),
    ("Mercedes-Benz", "E-Class", "W213",   2016, 2023, "luxury",    2.80),
    ("Audi", "A4",              "B9",      2015, 2023, "luxury",    2.45),
    ("Land Rover", "Defender",  "L663",    2020, 2025, "luxury",    2.90),

    # --- Commercial ---------------------------------------------------------
    ("Isuzu", "D-Max",          "RT85",    2012, 2020, "pickup",    1.45),
    ("Ford", "Ranger",          "PX",      2011, 2022, "pickup",    1.50),
]

# ---------------------------------------------------------------------------
# 2. PART CATALOG
#    (part_name, part_category, base_price_lkr, applies_to)
#    applies_to: "all" | "ice" (combustion only) | "hybrid_ice" | set of segments
# ---------------------------------------------------------------------------

PARTS_MASTER = [
    # engine / air & fuel
    ("Mass Air Flow Sensor",    "engine_management", 38000, "ice"),
    ("Oxygen Sensor",           "engine_management", 22000, "ice"),
    ("Throttle Body",           "engine_management", 46000, "ice"),
    ("Ignition Coil",           "engine_management", 14000, "ice"),
    ("Spark Plug",              "engine_management",  3200, "ice"),
    ("Air Filter",              "engine_management",  4800, "ice"),
    ("Fuel Filter",             "fuel_delivery",      7500, "ice"),
    ("Fuel Pump",               "fuel_delivery",     42000, "ice"),
    ("Fuel Injector",           "fuel_delivery",     19000, "ice"),

    # cooling & drive
    ("Water Pump",              "cooling",           26000, "ice"),
    ("Water Pump Gasket",       "cooling",            2400, "ice"),
    ("Thermostat",              "cooling",            8500, "ice"),
    ("Radiator",                "cooling",           38000, "all"),
    ("Radiator Hose",           "cooling",            5200, "all"),
    ("Engine Coolant 4L",       "cooling",            4200, "all"),
    ("Drive Belt",              "engine_management",  6800, "ice"),
    ("Timing Belt",             "engine_management", 16000, "ice"),

    # electrical
    ("Alternator",              "electrical",        48000, "ice"),
    ("Starter Motor",           "electrical",        39000, "ice"),
    ("Battery",                 "electrical",        28000, "all"),
    ("Headlight",               "lighting",          34000, "all"),
    ("Headlight Bulb",          "lighting",           4500, "all"),
    ("Tail Light",              "lighting",          18000, "all"),
    ("Fog Light",               "lighting",          11000, "all"),
    ("Side Mirror",             "body",              16000, "all"),
    ("Horn",                    "electrical",         5500, "all"),

    # braking
    ("Brake Pads",              "braking",           13500, "all"),
    ("Brake Disc",              "braking",           21000, "all"),
    ("Brake Hardware Clips",    "braking",            2400, "all"),
    ("Brake Fluid DOT4",        "braking",            3200, "all"),
    ("Brake Caliper",           "braking",           34000, "all"),
    ("Brake Master Cylinder",   "braking",           29000, "all"),
    ("Handbrake Cable",         "braking",            7800, "all"),

    # suspension & steering
    ("Shock Absorber",          "suspension",        24000, "all"),
    ("Coil Spring",             "suspension",        17000, "all"),
    ("Control Arm",             "suspension",        23000, "all"),
    ("Ball Joint",              "suspension",         9500, "all"),
    ("Stabiliser Link",         "suspension",         6200, "all"),
    ("Wheel Bearing",           "suspension",        13000, "all"),
    ("Tie Rod End",             "steering",           8800, "all"),
    ("Steering Rack",           "steering",          62000, "all"),
    ("Power Steering Pump",     "steering",          41000, "ice"),

    # transmission
    ("Clutch Kit",              "transmission",      52000, "ice"),
    ("CV Joint",                "transmission",      18000, "all"),
    ("CV Boot",                 "transmission",       3800, "all"),
    ("Engine Mount",            "transmission",      14000, "all"),
    ("Gearbox Mount",           "transmission",      11000, "all"),

    # body panels
    ("Front Bumper",            "body",              32000, "all"),
    ("Rear Bumper",             "body",              29000, "all"),
    ("Bonnet",                  "body",              41000, "all"),
    ("Front Fender",            "body",              19000, "all"),
    ("Rear Hatch",              "body",              46000, "all"),
    ("Front Door",              "body",              54000, "all"),
    ("Windscreen",              "body",              37000, "all"),
    ("Grille",                  "body",              13000, "all"),
    ("Wiper Blade",             "body",               3400, "all"),

    # exhaust
    ("Muffler",                 "exhaust",           24000, "ice"),
    ("Catalytic Converter",     "exhaust",           78000, "ice"),
    ("Exhaust Gasket",          "exhaust",            2200, "ice"),

    # cabin & restraint
    ("Cabin Filter",            "hvac",               4200, "all"),
    ("AC Compressor",           "hvac",              72000, "all"),
    ("AC Condenser",            "hvac",              31000, "all"),
    ("Blower Motor",            "hvac",              16000, "all"),
    ("Seat Belt",               "restraint_system",  14000, "all"),
    ("Airbag Module",           "restraint_system",  88000, "all"),

    # EV / hybrid specific
    ("Hybrid Battery Pack",     "ev_drivetrain",    420000, "hybrid_only"),
    ("Inverter Coolant Pump",   "ev_drivetrain",     32000, "electrified"),
    ("EV Charging Port",        "ev_drivetrain",     54000, "ev_only"),
    ("Traction Battery Pack",   "ev_drivetrain",    680000, "ev_only"),
    ("DC-DC Converter",         "ev_drivetrain",    145000, "ev_only"),
]

TIERS = [
    # (tier, price multiplier, brand pool, part-number suffix)
    ("OEM_Genuine",           1.00, "GENUINE", "OEM"),
    ("Certified_Aftermarket", 0.56, "AFTER",   "CER"),
    ("Economy",               0.30, "ECONOMY", "ECO"),
]

GENUINE_BRAND = {
    "Toyota": "Toyota Genuine", "Honda": "Honda Genuine",
    "Suzuki": "Suzuki Genuine", "Nissan": "Nissan Genuine",
    "Mitsubishi": "Mitsubishi Genuine", "Mazda": "Mazda Genuine",
    "Daihatsu": "Daihatsu Genuine", "Micro": "Micro Genuine",
    "Perodua": "Perodua Genuine", "Tata": "Tata Genuine",
    "Mahindra": "Mahindra Genuine", "Hyundai": "Hyundai Genuine",
    "Kia": "Kia Genuine", "BMW": "BMW Genuine",
    "Mercedes-Benz": "Mercedes-Benz Genuine", "Audi": "Audi Genuine",
    "Land Rover": "Land Rover Genuine", "Isuzu": "Isuzu Genuine",
    "Ford": "Ford Genuine",
}

# aftermarket brands that actually sell into Sri Lanka, by category
AFTERMARKET = {
    "braking":           ["TRW", "Akebono", "Bendix"],
    "suspension":        ["KYB", "Monroe", "Bilstein"],
    "steering":          ["555", "TRW", "Febi"],
    "engine_management": ["Denso", "NGK", "Bosch"],
    "fuel_delivery":     ["Denso", "Bosch", "Delphi"],
    "cooling":           ["Aisin", "Gates", "Denso"],
    "electrical":        ["Denso", "Bosch", "Valeo"],
    "lighting":          ["Depo", "TYC", "Valeo"],
    "transmission":      ["Exedy", "Aisin", "GMB"],
    "body":              ["Depo", "TYC", "Replacement OE"],
    "exhaust":           ["Walker", "Bosal", "Sango"],
    "hvac":              ["Denso", "Sanden", "Valeo"],
    "restraint_system":  ["Takata Replacement", "Autoliv"],
    "ev_drivetrain":     ["Reman Cell", "Denso"],
}

ECONOMY_BRANDS = ["Reconditioned (Japan)", "Generic Import", "Taiwan Aftermarket"]

ELECTRIFIED = {"hybrid", "ev"}


def applies(part_rule, segment):
    """Does this part exist on a vehicle in this segment?"""
    if part_rule == "all":
        return True
    if part_rule == "ice":
        return segment != "ev"
    if part_rule == "hybrid_only":
        return segment == "hybrid"
    if part_rule == "ev_only":
        return segment == "ev"
    if part_rule == "electrified":
        return segment in ELECTRIFIED
    return False


def stable_pick(pool, *keys):
    """Deterministic choice from a pool — same inputs always give same brand."""
    h = 0
    for k in keys:
        for ch in str(k):
            h = (h * 31 + ord(ch)) % 1000003
    return pool[h % len(pool)]


def round_price(v):
    """Round to something a price tag would actually show."""
    if v >= 100000:
        return int(round(v / 5000.0) * 5000)
    if v >= 20000:
        return int(round(v / 500.0) * 500)
    if v >= 5000:
        return int(round(v / 100.0) * 100)
    return int(round(v / 50.0) * 50)


def part_number(generation, part_name, suffix):
    h = 0
    for ch in part_name:
        h = (h * 33 + ord(ch)) % 9973
    return f"{generation}-{h:04d}-{suffix}"


# ---------------------------------------------------------------------------
# 3. BUILD parts.csv + generations.csv
# ---------------------------------------------------------------------------

def build_parts_and_generations():
    parts_rows = []
    gen_rows = []

    for make, model, gen, yf, yt, segment, factor in VEHICLES:
        gen_rows.append({
            "make": make, "model": model, "generation": gen,
            "year_from": yf, "year_to": yt, "segment": segment,
        })

        for part_name, category, base, rule in PARTS_MASTER:
            if not applies(rule, segment):
                continue

            for tier, mult, pool_key, suffix in TIERS:
                # EV/hybrid high-voltage parts have no economy tier in reality
                if category == "ev_drivetrain" and tier == "Economy":
                    continue
                # nobody sells an aftermarket airbag module
                if part_name == "Airbag Module" and tier != "OEM_Genuine":
                    continue

                if tier == "OEM_Genuine":
                    brand = GENUINE_BRAND.get(make, f"{make} Genuine")
                elif tier == "Certified_Aftermarket":
                    brand = stable_pick(
                        AFTERMARKET.get(category, ["Bosch", "Denso"]),
                        make, model, part_name,
                    )
                else:
                    brand = stable_pick(ECONOMY_BRANDS, make, gen, part_name)

                price = round_price(base * factor * mult)

                parts_rows.append({
                    "part_name": part_name,
                    "part_category": category,
                    "make": make,
                    "model": model,
                    "generation": gen,
                    "year_from": yf,
                    "year_to": yt,
                    "tier": tier,
                    "brand": brand,
                    "part_number": part_number(gen, part_name, suffix),
                    "price_lkr": price,
                })

    return parts_rows, gen_rows


# ---------------------------------------------------------------------------
# 4. ALIASES — trade vocabulary, Sri Lankan garage slang, common misspellings
# ---------------------------------------------------------------------------

ALIASES = [
    # MAF
    ("air flow meter", "Mass Air Flow Sensor"),
    ("airflow meter", "Mass Air Flow Sensor"),
    ("air flow sensor", "Mass Air Flow Sensor"),
    ("air mass meter", "Mass Air Flow Sensor"),
    ("maf", "Mass Air Flow Sensor"),
    ("maf sensor", "Mass Air Flow Sensor"),
    # oxygen sensor
    ("o2 sensor", "Oxygen Sensor"),
    ("lambda sensor", "Oxygen Sensor"),
    ("exhaust sensor", "Oxygen Sensor"),
    # ignition
    ("coil pack", "Ignition Coil"),
    ("engine coil", "Ignition Coil"),
    ("plug coil", "Ignition Coil"),
    ("plugs", "Spark Plug"),
    ("spark plugs", "Spark Plug"),
    ("ignition plug", "Spark Plug"),
    # filters
    ("engine air filter", "Air Filter"),
    ("air cleaner", "Air Filter"),
    ("ac filter", "Cabin Filter"),
    ("pollen filter", "Cabin Filter"),
    ("aircon filter", "Cabin Filter"),
    ("diesel filter", "Fuel Filter"),
    ("petrol filter", "Fuel Filter"),
    # cooling
    ("coolant pump", "Water Pump"),
    ("radiator pump", "Water Pump"),
    ("water pomp", "Water Pump"),
    ("coolant", "Engine Coolant 4L"),
    ("antifreeze", "Engine Coolant 4L"),
    ("rad hose", "Radiator Hose"),
    ("water hose", "Radiator Hose"),
    ("fan belt", "Drive Belt"),
    ("alternator belt", "Drive Belt"),
    ("cam belt", "Timing Belt"),
    # electrical
    ("dynamo", "Alternator"),
    ("generator", "Alternator"),
    ("charging unit", "Alternator"),
    ("self motor", "Starter Motor"),
    ("self starter", "Starter Motor"),
    ("cranking motor", "Starter Motor"),
    ("batt", "Battery"),
    ("car battery", "Battery"),
    # lighting
    ("head lamp", "Headlight"),
    ("headlamp", "Headlight"),
    ("front light", "Headlight"),
    ("head light", "Headlight"),
    ("bulb", "Headlight Bulb"),
    ("head lamp bulb", "Headlight Bulb"),
    ("back light", "Tail Light"),
    ("rear lamp", "Tail Light"),
    ("stop light", "Tail Light"),
    ("mirror", "Side Mirror"),
    ("wing mirror", "Side Mirror"),
    ("door mirror", "Side Mirror"),
    # braking
    ("brake pad", "Brake Pads"),
    ("pads", "Brake Pads"),
    ("brake lining", "Brake Pads"),
    ("disc pad", "Brake Pads"),
    ("brake rotor", "Brake Disc"),
    ("rotor", "Brake Disc"),
    ("disc plate", "Brake Disc"),
    ("brake oil", "Brake Fluid DOT4"),
    ("brake fluid", "Brake Fluid DOT4"),
    ("caliper", "Brake Caliper"),
    ("master cylinder", "Brake Master Cylinder"),
    ("hand brake cable", "Handbrake Cable"),
    # suspension
    ("shocker", "Shock Absorber"),
    ("shockers", "Shock Absorber"),
    ("shock", "Shock Absorber"),
    ("damper", "Shock Absorber"),
    ("strut", "Shock Absorber"),
    ("spring", "Coil Spring"),
    ("suspension spring", "Coil Spring"),
    ("wishbone", "Control Arm"),
    ("lower arm", "Control Arm"),
    ("a arm", "Control Arm"),
    ("ball joint kit", "Ball Joint"),
    ("stabilizer link", "Stabiliser Link"),
    ("link rod", "Stabiliser Link"),
    ("bearing", "Wheel Bearing"),
    ("hub bearing", "Wheel Bearing"),
    ("tie rod", "Tie Rod End"),
    ("track rod", "Tie Rod End"),
    ("steering box", "Steering Rack"),
    ("power steering", "Power Steering Pump"),
    # transmission
    ("clutch", "Clutch Kit"),
    ("clutch plate", "Clutch Kit"),
    ("drive shaft joint", "CV Joint"),
    ("cv boot kit", "CV Boot"),
    ("axle boot", "CV Boot"),
    ("engine mounting", "Engine Mount"),
    ("gear box mounting", "Gearbox Mount"),
    # body
    ("bumper", "Front Bumper"),
    ("front buffer", "Front Bumper"),
    ("rear buffer", "Rear Bumper"),
    ("back bumper", "Rear Bumper"),
    ("hood", "Bonnet"),
    ("engine cover", "Bonnet"),
    ("mudguard", "Front Fender"),
    ("wing", "Front Fender"),
    ("dicky door", "Rear Hatch"),
    ("boot lid", "Rear Hatch"),
    ("tailgate", "Rear Hatch"),
    ("windshield", "Windscreen"),
    ("front glass", "Windscreen"),
    ("front grill", "Grille"),
    ("wiper", "Wiper Blade"),
    ("wiper rubber", "Wiper Blade"),
    # exhaust
    ("silencer", "Muffler"),
    ("exhaust box", "Muffler"),
    ("back box", "Muffler"),
    ("cat converter", "Catalytic Converter"),
    ("catalyst", "Catalytic Converter"),
    # hvac
    ("ac compressor", "AC Compressor"),
    ("aircon compressor", "AC Compressor"),
    ("ac pump", "AC Compressor"),
    ("condenser", "AC Condenser"),
    ("blower", "Blower Motor"),
    ("fan motor", "Blower Motor"),
    # restraint
    ("seatbelt", "Seat Belt"),
    ("airbag", "Airbag Module"),
    # EV / hybrid
    ("hybrid battery", "Hybrid Battery Pack"),
    ("ima battery", "Hybrid Battery Pack"),
    ("hv battery", "Hybrid Battery Pack"),
    ("traction battery", "Traction Battery Pack"),
    ("ev battery", "Traction Battery Pack"),
    ("charging socket", "EV Charging Port"),
    ("charge port", "EV Charging Port"),
    ("dcdc converter", "DC-DC Converter"),
]


# ---------------------------------------------------------------------------
# 5. BOM DEPENDENCIES
# ---------------------------------------------------------------------------

BOM = [
    ("Mass Air Flow Sensor", ["Air Filter"], []),
    ("Throttle Body", ["Exhaust Gasket"], ["Air Filter"]),
    ("Ignition Coil", [], ["Spark Plug"]),
    ("Spark Plug", [], ["Ignition Coil"]),
    ("Water Pump", ["Water Pump Gasket", "Engine Coolant 4L"], ["Thermostat", "Drive Belt"]),
    ("Thermostat", ["Engine Coolant 4L"], ["Radiator Hose"]),
    ("Radiator", ["Engine Coolant 4L", "Radiator Hose"], ["Thermostat"]),
    ("Timing Belt", [], ["Water Pump", "Drive Belt"]),
    ("Drive Belt", [], ["Stabiliser Link"]),
    ("Alternator", [], ["Drive Belt", "Battery"]),
    ("Starter Motor", [], ["Battery"]),
    ("Brake Pads", ["Brake Hardware Clips"], ["Brake Fluid DOT4", "Brake Disc"]),
    ("Brake Disc", ["Brake Hardware Clips"], ["Brake Pads"]),
    ("Brake Caliper", ["Brake Fluid DOT4"], ["Brake Pads", "Brake Hardware Clips"]),
    ("Brake Master Cylinder", ["Brake Fluid DOT4"], []),
    ("Shock Absorber", [], ["Coil Spring", "Stabiliser Link"]),
    ("Control Arm", [], ["Ball Joint", "Stabiliser Link"]),
    ("Wheel Bearing", [], ["Brake Disc"]),
    ("Tie Rod End", [], ["Ball Joint"]),
    ("Steering Rack", [], ["Tie Rod End"]),
    ("Clutch Kit", [], ["Gearbox Mount"]),
    ("CV Joint", ["CV Boot"], []),
    ("Headlight", [], ["Headlight Bulb"]),
    ("Front Bumper", [], ["Grille", "Fog Light"]),
    ("Rear Bumper", [], ["Tail Light"]),
    ("Bonnet", [], ["Grille"]),
    ("Windscreen", ["Wiper Blade"], []),
    ("Muffler", ["Exhaust Gasket"], []),
    ("Catalytic Converter", ["Exhaust Gasket"], ["Oxygen Sensor"]),
    ("AC Compressor", [], ["AC Condenser", "Cabin Filter"]),
    ("AC Condenser", [], ["Cabin Filter"]),
    ("Fuel Pump", ["Fuel Filter"], []),
    ("Fuel Injector", [], ["Fuel Filter"]),
    ("Hybrid Battery Pack", [], ["Inverter Coolant Pump"]),
    ("Traction Battery Pack", [], ["DC-DC Converter"]),
]


SAFETY_RULES = [
    ("braking", "Economy",
     "Reconditioned braking components cannot be quality-verified; workshop liability risk."),
    ("suspension", "Economy",
     "Economy dampers and arms fail unpredictably under load; refuse for safety-critical suspension work."),
    ("steering", "Economy",
     "Steering components must be traceable; economy parts lack certification."),
    ("restraint_system", "Economy;Certified_Aftermarket",
     "Seat belts and airbags are single-use safety devices; only genuine units may be fitted."),
    ("fuel_delivery", "Economy",
     "Fuel system leaks are a fire risk; economy pumps and injectors are not pressure-certified."),
    ("ev_drivetrain", "Economy;Certified_Aftermarket",
     "High-voltage components require manufacturer certification; non-genuine units are a shock and fire hazard."),
]


# ---------------------------------------------------------------------------
# 6. WRITE + VALIDATE
# ---------------------------------------------------------------------------

def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main():
    parts_rows, gen_rows = build_parts_and_generations()

    alias_rows = [{"alias": a, "canonical": c, "source": "trade_vocabulary"}
                  for a, c in ALIASES]

    bom_rows = [{"primary_part": p,
                 "requires": ";".join(r),
                 "recommends": ";".join(rec),
                 "source": "curated"}
                for p, r, rec in BOM]

    safety_rows = [{"part_category": c, "block_tiers": b, "reason": r}
                   for c, b, r in SAFETY_RULES]

    n_parts = write_csv(os.path.join(OUT, "parts.csv"),
                        ["part_name", "part_category", "make", "model",
                         "generation", "year_from", "year_to", "tier",
                         "brand", "part_number", "price_lkr"],
                        parts_rows)
    n_gens = write_csv(os.path.join(OUT, "generations.csv"),
                       ["make", "model", "generation", "year_from",
                        "year_to", "segment"], gen_rows)
    n_alias = write_csv(os.path.join(OUT, "part_aliases.csv"),
                        ["alias", "canonical", "source"], alias_rows)
    n_bom = write_csv(os.path.join(OUT, "bom_dependencies.csv"),
                      ["primary_part", "requires", "recommends", "source"],
                      bom_rows)
    n_safe = write_csv(os.path.join(OUT, "safety_rules.csv"),
                       ["part_category", "block_tiers", "reason"], safety_rows)

    print(f"parts.csv             {n_parts}")
    print(f"generations.csv       {n_gens}")
    print(f"part_aliases.csv      {n_alias}")
    print(f"bom_dependencies.csv  {n_bom}")
    print(f"safety_rules.csv      {n_safe}")

    # ---------------- integrity checks ----------------
    print("\n--- integrity ---")
    ok = True

    catalog_names = {r["part_name"] for r in parts_rows}
    categories = {r["part_category"] for r in parts_rows}

    seen = set()
    for r in alias_rows:
        if r["alias"] in seen:
            print(f"FAIL duplicate alias: {r['alias']}")
            ok = False
        seen.add(r["alias"])
        if r["canonical"] not in catalog_names:
            print(f"FAIL alias target not in catalog: {r['alias']} -> {r['canonical']}")
            ok = False

    bom_seen = set()
    for r in bom_rows:
        if r["primary_part"] in bom_seen:
            print(f"FAIL duplicate bom primary_part: {r['primary_part']}")
            ok = False
        bom_seen.add(r["primary_part"])
        if r["primary_part"] not in catalog_names:
            print(f"FAIL bom primary not in catalog: {r['primary_part']}")
            ok = False
        for item in (r["requires"].split(";") + r["recommends"].split(";")):
            if item and item not in catalog_names:
                print(f"FAIL bom item not priceable: {item}")
                ok = False

    for r in safety_rows:
        if r["part_category"] not in categories:
            print(f"FAIL safety rule category unused by any part: {r['part_category']}")
            ok = False
        for t in r["block_tiers"].split(";"):
            if t not in {"OEM_Genuine", "Certified_Aftermarket", "Economy"}:
                print(f"FAIL bad tier in safety rule: {t}")
                ok = False

    # EVs must not carry combustion parts
    ev_gens = {(v[0], v[1], v[2]) for v in VEHICLES if v[5] == "ev"}
    banned = {"Water Pump", "Alternator", "Mass Air Flow Sensor",
              "Ignition Coil", "Spark Plug", "Muffler", "Fuel Pump",
              "Catalytic Converter", "Clutch Kit"}
    for r in parts_rows:
        if (r["make"], r["model"], r["generation"]) in ev_gens and r["part_name"] in banned:
            print(f"FAIL EV has combustion part: {r['make']} {r['model']} {r['part_name']}")
            ok = False

    # every vehicle must be able to quote brake pads
    quotable = {(r["make"], r["model"], r["generation"]) for r in parts_rows
                if r["part_name"] == "Brake Pads"}
    for v in VEHICLES:
        if (v[0], v[1], v[2]) not in quotable:
            print(f"FAIL vehicle cannot quote brake pads: {v[0]} {v[1]} {v[2]}")
            ok = False

    # no overlapping year ranges for the same make+model
    from collections import defaultdict
    by_model = defaultdict(list)
    for v in VEHICLES:
        by_model[(v[0], v[1])].append((v[3], v[4], v[2]))
    for key, spans in by_model.items():
        spans.sort()
        for i in range(len(spans) - 1):
            if spans[i][1] > spans[i + 1][0]:
                print(f"FAIL overlapping generations for {key}: "
                      f"{spans[i][2]} and {spans[i+1][2]}")
                ok = False

    print("PASS - all integrity checks clean" if ok else "FAILED - see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
