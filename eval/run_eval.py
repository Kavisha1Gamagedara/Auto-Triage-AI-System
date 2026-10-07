"""Retrieval evaluation for the Agent 4 part name resolver.

Reports two things over a test set (eval/testset_heldout.csv by default,
or --testset PATH):

  * Production path - what resolve() actually answers, which is what gets
    priced. Each query is correct, wrong (a different part was accepted) or
    unresolved. A row with an empty 'expected' names no catalog part, so
    the correct answer for it is to stay unresolved.
  * Ranked retrieval - Precision@1, Recall@3 and MRR over resolve_ranked,
    which applies no acceptance thresholds. It shows whether the right name
    is in reach, not whether it would be quoted.

The --no-bm25 / --no-fuzzy flags give the three-way ablation of the ranked
metrics:

    python eval/run_eval.py --no-bm25 --no-fuzzy    # exact only
    python eval/run_eval.py --no-fuzzy              # exact + BM25
    python eval/run_eval.py                         # full pipeline

This harness only measures. It never modifies the resolver, its thresholds
or the alias table - a query that fails is a result to report, not a bug to
tune away.
"""

import argparse
import csv
import os
import sys

# Allow running as `python eval/run_eval.py` from the repo root.
BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from agent4_resolver import PartResolver  # noqa: E402
from db import get_db  # noqa: E402

TESTSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testset_heldout.csv")

K = 3


def load_testset(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [
            {
                "query": r["query"].strip(),
                "expected": (r.get("expected") or "").strip(),
                "category": (r.get("category") or "").strip() or "-",
            }
            for r in csv.DictReader(f)
            if (r.get("query") or "").strip()
        ]
    if not rows:
        sys.exit(f"No rows in {path}")
    return rows


def reciprocal_rank(ranked: list[str], expected: str) -> float:
    """1/rank of the expected name, or 0.0 if it is absent.

    An empty ranked list - which resolve_ranked returns for a true miss
    rather than padding to k - falls through to 0.0 here, scoring as a miss.
    """
    for i, name in enumerate(ranked, start=1):
        if name == expected:
            return 1.0 / i
    return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the Agent 4 resolver.")
    parser.add_argument("--no-bm25", action="store_true", help="skip the BM25 stage")
    parser.add_argument("--no-fuzzy", action="store_true", help="skip the fuzzy stage")
    parser.add_argument("--no-alias-ngram", action="store_true",
                        help="skip the alias n-gram pre-pass (reproduces the Run 1 baseline)")
    parser.add_argument("--testset", default=TESTSET, help="CSV with query, expected and optional category")
    parser.add_argument("--quiet", action="store_true", help="metrics only")
    args = parser.parse_args()

    use_bm25 = not args.no_bm25
    use_fuzzy = not args.no_fuzzy
    use_ngram = not args.no_alias_ngram
    config = (
        "exact"
        + (" + n-gram" if use_ngram else "")
        + (" + BM25" if use_bm25 else "")
        + (" + fuzzy" if use_fuzzy else "")
    )

    rows = load_testset(args.testset)
    db = get_db()
    resolver = PartResolver(db)

    # --- label validation -------------------------------------------------
    # An expected value that is not a real part_name can never be returned by
    # the resolver, so it would score as a permanent miss and quietly depress
    # every metric. Surface those before scoring anything.
    catalog = set(db.parts.distinct("part_name"))
    bad_labels = sorted({r["expected"] for r in rows if r["expected"] and r["expected"] not in catalog})

    print(f"Config     : {config}")
    print(f"Test set   : {args.testset} ({len(rows)} queries)")
    print(f"Catalog    : {len(catalog)} distinct part names")

    if bad_labels:
        print(f"\n!! {len(bad_labels)} expected label(s) are NOT in the catalog and can never be scored correctly:")
        for label in bad_labels:
            print(f"     {label!r}")
        print("   These are counted as misses below. Fix the labels, not the resolver.")
    else:
        print("Labels     : all expected values exist in the catalog")

    # --- scoring ----------------------------------------------------------
    results = []
    for row in rows:
        ranked = resolver.resolve_ranked(
            row["query"], k=K, use_bm25=use_bm25, use_fuzzy=use_fuzzy, use_alias_ngram=use_ngram
        )
        # resolve() is the production single-answer path and has no ablation
        # flags by design. Its method is reported here to explain WHY a query
        # is lost under an ablation, not to score it.
        answer = resolver.resolve(row["query"])
        method = answer["method"]
        if answer["canonical"] == (row["expected"] or None):
            outcome = "correct"
        elif answer["canonical"] is None:
            outcome = "unresolved"
        else:
            outcome = "wrong"

        top = ranked[0] if ranked else None
        results.append(
            {
                "query": row["query"],
                "expected": row["expected"],
                "category": row["category"],
                "answer": answer["canonical"],
                "outcome": outcome,
                "returned": top,
                "ranked": ranked,
                "method": method,
                "p1": 1.0 if top == row["expected"] else 0.0,
                "r3": 1.0 if row["expected"] in ranked[:K] else 0.0,
                "rr": reciprocal_rank(ranked[:K], row["expected"]),
            }
        )

    # --- production path --------------------------------------------------
    n = len(results)
    print()
    if not args.quiet:
        print(f"{'query':<44} {'expected':<22} {'resolve() answered':<22} {'method':<13} outcome")
        print("-" * 112)
        for r in results:
            print(
                f"{r['query'][:43]:<44} {(r['expected'] or '(none)')[:21]:<22} "
                f"{(r['answer'] or '-')[:21]:<22} {r['method']:<13} {r['outcome']}"
            )
        print()

    def tally(subset: list[dict]) -> str:
        counts = {o: sum(1 for r in subset if r["outcome"] == o) for o in ("correct", "wrong", "unresolved")}
        answered = counts["correct"] + counts["wrong"] - sum(
            1 for r in subset if r["outcome"] == "correct" and not r["expected"]
        )
        return (
            f"correct {counts['correct']:>3}/{len(subset):<3} wrong {counts['wrong']:>3}  "
            f"unresolved {counts['unresolved']:>3}  (parts answered: {answered})"
        )

    print("Production path, via resolve():")
    print(f"  {'all':<12} {tally(results)}")
    for category in sorted({r["category"] for r in results}):
        if category != "-":
            print(f"  {category:<12} {tally([r for r in results if r['category'] == category])}")

    # --- ranked retrieval -------------------------------------------------
    # Rows that expect no part cannot be ranked, so they are left out here.
    labelled = [r for r in results if r["expected"]]
    m = len(labelled)
    if m:
        precision_at_1 = sum(r["p1"] for r in labelled) / m
        recall_at_3 = sum(r["r3"] for r in labelled) / m
        mrr = sum(r["rr"] for r in labelled) / m

        print(f"\nRanked retrieval, via resolve_ranked() [{config}], {m} labelled queries:")
        print(f"  Precision@1 : {precision_at_1:.3f}  ({int(sum(r['p1'] for r in labelled))}/{m})")
        print(f"  Recall@{K}    : {recall_at_3:.3f}  ({int(sum(r['r3'] for r in labelled))}/{m})")
        print(f"  MRR         : {mrr:.3f}")

    # --- method breakdown -------------------------------------------------
    print("\nResolved by stage (full pipeline, via resolve()):")
    for stage in ["exact", "alias_exact", "alias_partial", "bm25", "fuzzy", "none"]:
        count = sum(1 for r in results if r["method"] == stage)
        print(f"  {stage:<12} {count:>3}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
