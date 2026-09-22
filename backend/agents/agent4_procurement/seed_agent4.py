"""Seed the Agent 4 parts catalog into MongoDB from the CSVs in backend/data/.

Run from anywhere:  python backend/seed_agent4.py
This is destructive - all five collections are dropped and rebuilt.
"""

import csv
import os
import sys
from collections import Counter

from pymongo import ASCENDING

from db import get_db, MONGO_DB, MONGO_URI

# Resolve data/ from this file's location so the script works from any cwd.
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

COLLECTIONS = ["parts", "generations", "part_aliases", "bom_dependencies", "safety_rules"]

BATCH_SIZE = 1000


def read_csv(name: str) -> list[dict]:
    """Read data/<name>.csv into a list of dicts, stripping whitespace."""
    path = os.path.join(DATA_DIR, f"{name}.csv")
    if not os.path.exists(path):
        sys.exit(f"FAIL: missing CSV {path}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]

    if not rows:
        sys.exit(f"FAIL: {name}.csv has no data rows")
    return rows


def to_int(value: str, field: str, collection: str, row_num: int) -> int:
    """Cast a CSV cell to int, or abort.

    These casts are not cosmetic: the year-range queries use $lte/$gte, and
    string years compare lexicographically, so a missed cast makes the query
    return nothing at all rather than raising.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        sys.exit(
            f"FAIL: {collection}.csv row {row_num}: {field}={value!r} is not an integer"
        )


def split_list(value: str) -> list[str]:
    """Split a ';'-delimited cell into a list. An empty cell becomes []."""
    return [item.strip() for item in value.split(";") if item.strip()]


def build_parts(rows: list[dict]) -> list[dict]:
    docs = []
    for i, row in enumerate(rows, start=2):  # start=2 -> header is line 1
        docs.append(
            {
                "part_name": row["part_name"],
                "part_category": row["part_category"],
                "make": row["make"],
                "model": row["model"],
                "generation": row["generation"],
                "year_from": to_int(row["year_from"], "year_from", "parts", i),
                "year_to": to_int(row["year_to"], "year_to", "parts", i),
                "tier": row["tier"],
                "brand": row["brand"],
                "part_number": row["part_number"],
                "price_lkr": to_int(row["price_lkr"], "price_lkr", "parts", i),
            }
        )
    return docs


def build_generations(rows: list[dict]) -> list[dict]:
    docs = []
    for i, row in enumerate(rows, start=2):
        docs.append(
            {
                "make": row["make"],
                "model": row["model"],
                "generation": row["generation"],
                "year_from": to_int(row["year_from"], "year_from", "generations", i),
                "year_to": to_int(row["year_to"], "year_to", "generations", i),
                "segment": row["segment"],
            }
        )
    return docs


def build_part_aliases(rows: list[dict]) -> list[dict]:
    docs = [
        {"alias": row["alias"], "canonical": row["canonical"], "source": row["source"]}
        for row in rows
    ]

    # The alias index is unique, so a duplicate would blow up mid-insert and
    # leave the DB half-loaded. Catch it here, before anything is dropped.
    duplicates = [alias for alias, n in Counter(d["alias"] for d in docs).items() if n > 1]
    if duplicates:
        print("FAIL: duplicate alias keys in part_aliases.csv:", file=sys.stderr)
        for alias in sorted(duplicates):
            print(f"  - {alias!r}", file=sys.stderr)
        sys.exit(1)

    return docs


def build_bom_dependencies(rows: list[dict]) -> list[dict]:
    docs = [
        {
            "primary_part": row["primary_part"],
            "requires": split_list(row["requires"]),
            "recommends": split_list(row["recommends"]),
            "source": row["source"],
        }
        for row in rows
    ]

    duplicates = [
        part for part, n in Counter(d["primary_part"] for d in docs).items() if n > 1
    ]
    if duplicates:
        print("FAIL: duplicate primary_part keys in bom_dependencies.csv:", file=sys.stderr)
        for part in sorted(duplicates):
            print(f"  - {part!r}", file=sys.stderr)
        sys.exit(1)

    return docs


def build_safety_rules(rows: list[dict]) -> list[dict]:
    return [
        {
            "part_category": row["part_category"],
            "block_tiers": row["block_tiers"],
            "reason": row["reason"],
        }
        for row in rows
    ]


BUILDERS = {
    "parts": build_parts,
    "generations": build_generations,
    "part_aliases": build_part_aliases,
    "bom_dependencies": build_bom_dependencies,
    "safety_rules": build_safety_rules,
}


def insert_batched(collection, docs: list[dict]) -> None:
    for start in range(0, len(docs), BATCH_SIZE):
        collection.insert_many(docs[start : start + BATCH_SIZE], ordered=True)


def create_indexes(db) -> None:
    db.parts.create_index(
        [("make", ASCENDING), ("model", ASCENDING), ("generation", ASCENDING), ("part_name", ASCENDING)]
    )
    db.generations.create_index(
        [("make", ASCENDING), ("model", ASCENDING), ("year_from", ASCENDING), ("year_to", ASCENDING)]
    )
    db.part_aliases.create_index([("alias", ASCENDING)], unique=True)
    db.bom_dependencies.create_index([("primary_part", ASCENDING)], unique=True)


def verify(db) -> bool:
    """Spot-check that a known part resolves. Must return exactly 3 documents."""
    query = {
        "make": "Toyota",
        "model": "Corolla",
        "generation": "E210",
        "part_name": "Brake Pads",
    }
    found = list(db.parts.find(query))

    print("\nVerification query: Toyota Corolla E210 Brake Pads")
    print(f"  expected 3 documents, got {len(found)}")
    for doc in found:
        print(f"    {doc['tier']:<22} {doc['brand']:<18} {doc['part_number']:<22} LKR {doc['price_lkr']:,}")

    if len(found) == 3:
        print("\nPASS")
        return True
    print("\nFAIL")
    return False


def main() -> int:
    print(f"Database: {MONGO_DB} @ {MONGO_URI.split('@')[-1]}")
    print(f"Data dir: {DATA_DIR}\n")

    # Read and transform everything up front. Nothing touches the database
    # until all five files have parsed and validated cleanly.
    built = {}
    for name in COLLECTIONS:
        built[name] = BUILDERS[name](read_csv(name))
        print(f"  parsed {name:<18} {len(built[name]):>6} rows")

    db = get_db()

    # Drop all five first, so a failure partway through the inserts leaves an
    # obviously empty database rather than a half-loaded one.
    print()
    for name in COLLECTIONS:
        db[name].drop()
    print(f"Dropped {len(COLLECTIONS)} collections\n")

    for name in COLLECTIONS:
        insert_batched(db[name], built[name])
        print(f"  inserted {name:<18} {db[name].count_documents({}):>6} documents")

    create_indexes(db)
    print("\nIndexes created")

    return 0 if verify(db) else 1


if __name__ == "__main__":
    sys.exit(main())
