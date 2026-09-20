# Agent 4 — Procurement & Pricing

Turns Agent 2's root-cause component into a priced, tiered bill of materials for a
specific vehicle, sourced entirely from a MongoDB parts catalog.

> **Core rule: the LLM may propose, only the database may price.**
> No price and no part number in Agent 4's output ever originates from a model.

**Current catalog:** 24,233 documents · 70 part names · 109 make/model pairs ·
124 generations · 20 makes · 3 quality tiers.

---

## Contents

1. [Quick start](#quick-start)
2. [The handoff from Agent 2](#the-handoff-from-agent-2)
3. [API reference](#api-reference)
4. [File map](#file-map)
5. [Data model](#data-model)
6. [The workflow](#the-workflow)
7. [The part name resolver](#the-part-name-resolver)
8. [The core rule, and how it is enforced](#the-core-rule-and-how-it-is-enforced)
9. [Testing](#testing)
10. [Evaluation](#evaluation)
11. [Design decisions and why](#design-decisions-and-why)
12. [Limitations](#limitations)
13. [Troubleshooting](#troubleshooting)
14. [Current state](#current-state)

---

## Quick start

```bash
# from the repo root, with .venv active
pip install -r backend/requirements.txt

# 1. generate the CSVs (only needed if you changed generate_tables.py)
python backend/data/generate_tables.py

# 2. load them into MongoDB — DESTRUCTIVE, drops all five collections
python backend/seed_agent4.py

# 3. verify
pytest backend/test_agent4_resolver.py backend/test_agent4_procurement.py
```

Requires `MONGO_URI` and `MONGO_DB` in `backend/.env`:

```ini
MONGO_URI=mongodb://localhost:27017        # or an Atlas mongodb+srv:// string
MONGO_DB=auto_triage
GROQ_API_KEY=...                           # only for the LLM fallback path
GROQ_MODEL=openai/gpt-oss-120b
```

`backend/.env` is gitignored and has never been committed. Use `.env.example` as a template.

---

## The handoff from Agent 2

**This is the most important thing to understand, and it is not obvious from the payload.**

Agent 2 emits a `DiagnosticResult`. It names the failed component and describes the
risk, but carries **no vehicle identity at all** — and parts are priced per vehicle
generation, so a component name on its own cannot be priced.

```jsonc
// Agent 2 output — models.py :: DiagnosticResult
{
  "root_cause_component": "Brake Pads",      // → Agent 4 (the only field resolved)
  "failure_mode": "Friction material worn",  // → deliberately DROPPED
  "severity": "High",                        // → Agent 4 (passed through untouched)
  "safety_warning": "Support on axle stands" // → Agent 4 (passed through untouched)
}
```

The missing `make`, `model` and `year` come from **Agent 1**, which verified them
against NHTSA vPIC several steps earlier.

```
[Agent 1] ──── make, model, year (int) ──────────────────┐
    │                                                    │
    └──► [Agent 2] ── component, severity, warning ──► [Agent 4]
```

`failure_mode` is dropped on purpose: feeding symptom prose to the resolver floods
the lexical match with non-part words and degrades the lookup.

> **Nothing in the codebase currently joins these two branches.** The endpoint works;
> no orchestrator, route or frontend code assembles the request. See
> [Current state](#current-state).

### Why `year` must be an integer

The generation lookup compares `year_from <= year <= year_to` against BSON integers.
A string year compares lexicographically and the query returns nothing — silently,
with no error. Agent 3 accepts a concatenated `"2020 Toyota Corolla"` string;
Agent 4 deliberately does not.

---

## API reference

### `POST /api/v1/procure`

**Request** (`models.py :: ProcurementRequest`)

```json
{
  "session_id": "sess_abc123",
  "root_cause_component": "Brake Pads",
  "make": "Toyota",
  "model": "Corolla",
  "year": 2020,
  "severity": "High",
  "safety_warning": "Support the vehicle on axle stands."
}
```

`severity` defaults to `"Medium"`, `safety_warning` to `""`. Both pass through untouched.

**Response** (`models.py :: ProcurementResponse`)

```json
{
  "resolved_part": "Brake Pads",
  "match_method": "exact",
  "match_confidence": 1.0,
  "bill_of_materials": ["Brake Pads", "Brake Hardware Clips", "Brake Fluid DOT4", "Brake Disc"],
  "unpriced_items": [],
  "tiers": {
    "OEM_Genuine": {
      "tier_total_lkr": 44050,
      "complete": true,
      "parts": [
        {"part_name": "Brake Pads", "brand": "Toyota Genuine",
         "part_number": "E210-8074-OEM", "price_lkr": 14900, "role": "primary"}
      ]
    },
    "Certified_Aftermarket": { "tier_total_lkr": 24650, "complete": true, "parts": [] }
  },
  "suppressed_tiers": ["Economy"],
  "severity": "High",
  "safety_warning": "Support the vehicle on axle stands.",
  "warnings": ["Economy suppressed for braking: Reconditioned braking components cannot be quality-verified; workshop liability risk."],
  "candidates": []
}
```

### Status codes

| Condition | Status | Behaviour |
|---|---|---|
| Unknown part name | `200` | `resolved_part: null`, warning, `candidates` populated |
| Vehicle not in catalog | `200` | Warning naming the vehicle, empty tiers |
| Part not stocked for that generation | `200` | Warning, `complete: false` |
| Year matches two generations | `200` | Quotes newer, warns, advises VIN check |
| LLM unreachable / no API key | `200` | Warning appended, quote proceeds with primary part only |
| LLM proposes an unknown name | `200` | Goes to `unpriced_items`, never priced |
| Malformed payload | `422` | Pydantic, before the handler runs |
| Agent 4 import failed | `503` | Guarded import left the symbol `None` |
| Groq API error | `502` | Only if it escapes `_build_bom`'s own catch |
| MongoDB down | `500` | Genuine infrastructure fault |

**An unknown part or an unlisted vehicle is a normal result, not an error.** The only
hard failure is a malformed payload.

---

## File map

### Request path — runs on every quote

| File | Lines | Owns |
|---|---|---|
| `backend/agent4_procurement.py` | 366 | The six-step workflow, LLM fallback, tier maths. Entry: `get_procurement_quote()` (line 176) |
| `backend/agent4_resolver.py` | 316 | `PartResolver` and its five matching stages. Knows nothing about prices or vehicles |
| `backend/db.py` | 17 | Reads `.env`, exposes `MongoClient` + `get_db()`. Generic — Agents 1–3 can reuse it |
| `backend/models.py` | shared | `ProcurementRequest` (156), `QuotedPart` (187), `TierQuote` (196), `ProcurementResponse` (203) |
| `backend/main.py` | shared | `POST /api/v1/procure` (167), handler `run_procurement()` (172), guarded import (22) |

### Offline — never runs during a request

| File | Owns |
|---|---|
| `backend/data/generate_tables.py` | **The source of truth.** Generates all five CSVs from Python lists + integrity checks |
| `backend/seed_agent4.py` | CSV → MongoDB. Drops, casts integers, splits BOM lists, builds indexes |
| `backend/test_agent4_resolver.py` | 10 pytest cases for the resolver |
| `backend/test_agent4_procurement.py` | 27 pytest cases for the pipeline |
| `eval/run_eval.py` | Retrieval harness — Precision@1, Recall@3, MRR with ablation flags |

### The dependency rule

`agent4_resolver.py` **never** imports `agent4_procurement.py`. The dependency runs
one way only. That is what lets the resolver be tested and evaluated without a
pricing context.

---

## Data model

All four satellite collections key on a field of `parts`. Nothing joins to anything else.

```
        generations                         part_aliases
   (make, model, generation)              (canonical = part_name)
              │                                    │
              └──────────────►  parts  ◄───────────┘
                          ▲             ▲
              ┌───────────┘             └───────────┐
       bom_dependencies                       safety_rules
   (primary_part = part_name)            (part_category = part_category)
```

| Collection | Rows | Key columns | Role | Index |
|---|---:|---|---|---|
| `parts` | 23,787 | `part_name, part_category, make, model, generation, year_from, year_to, tier, brand, part_number, price_lkr` | The only source of prices and part numbers | `{make, model, generation, part_name}` |
| `generations` | 124 | `make, model, generation, year_from, year_to, segment` | Model year → generation code | `{make, model, year_from, year_to}` |
| `part_aliases` | 273 | `alias, canonical, source` | Trade vocabulary → catalog name | `{alias}` unique |
| `bom_dependencies` | 35 | `primary_part, requires[], recommends[], source` | Curated companion parts | `{primary_part}` unique |
| `safety_rules` | 14 | `part_category, block_tiers, reason` | Withholds tiers per category | — |

`generations` is the only collection resolved by a range comparison. Everything else
is an equality lookup on an indexed field.

### Why prices are per generation

A 2013 Corolla (`E170`) and a 2020 Corolla (`E210`) take different brake discs at
different prices. Storing 23,787 rows rather than 70 is what makes a quote specific
to the car in the bay. The cost is that a vehicle outside the 109 known make/model
pairs cannot be quoted at all.

### BOM = Bill of Materials

The complete list of parts needed to finish a job, in two grades:

| | Meaning | Water Pump example |
|---|---|---|
| `requires` | Cannot complete the job without it | `Water Pump Gasket`, `Engine Coolant 4L` — the old gasket can't be reused, and you drained the coolant to get there |
| `recommends` | Sensible while you're already in there | `Thermostat`, `Drive Belt` — labour is already paid for |

### ⚠ The CSVs are build artefacts, not source

`backend/data/*.csv` are **generated**. Editing `parts.csv` by hand is lost the
moment anyone runs `generate_tables.py`. Additions go in that file's Python lists:

| Add | To |
|---|---|
| A vehicle | `VEHICLES` |
| A trade term | `ALIASES` |
| A companion part | `BOM` |
| A tier restriction | `SAFETY_RULES` |
| A part | `PARTS_MASTER` |

Then regenerate, then re-seed. The generator runs its own integrity checks:
duplicate aliases, BOM items that aren't priceable, safety rules for unused
categories, EVs carrying combustion parts, overlapping year ranges, and every
vehicle being able to quote brake pads.

### Alias table policy

**Real words mechanics say, never misspellings.** A typo (`altenator`, `radaitor`)
is the fuzzy stage's job — putting it in the alias table trades a genuine capability
for a lookup-table entry and makes the evaluation circular. `water pomp` predates
this rule.

Multi-word terms are preferred over bare single tokens: the alias n-gram pre-pass
matches any window of a longer query, so a short generic alias fires inside
sentences that were never about that part.

### What `seed_agent4.py` does that a plain import would not

- **Parses and validates all five CSVs before dropping anything**, so a malformed
  file aborts with the database intact.
- **Casts integers explicitly** — `year_from`, `year_to`, `price_lkr`. String years
  compare lexicographically and make `$lte`/`$gte` return nothing, silently.
- **Splits `;`-delimited BOM cells into arrays**, with an empty cell becoming `[]`
  rather than `['']`.
- **Detects duplicate keys in Python first**, printing the offending alias by name,
  because the unique indexes would otherwise fail mid-insert.
- Inserts in batches of 1000 and builds the four indexes afterwards.

---

## The workflow

Six steps, strictly ordered.

### 1 · Resolve the component

Only `root_cause_component` is resolved — never the failure-mode prose. Five staged
attempts (see below). **On failure** it returns immediately with `resolved_part: null`,
a warning and a `candidates` list. No pricing is attempted and nothing is guessed.

### 2 · Identify the generation

```python
db.generations.find({"make": make, "model": model,
                     "year_from": {"$lte": year}, "year_to": {"$gte": year}})
```

**Boundary case:** generation ranges touch — a 2018 Corolla matches both `E170`
(2013–2018) and `E210` (2018–2024). Agent 4 sorts by `year_from` descending, quotes
the newer generation, and warns naming both with a VIN recommendation.

### 3 · Assemble the bill of materials

Look up `bom_dependencies` by `primary_part` **first**. On a hit the function
returns from that branch — the LLM is not called, not in parallel, not to supplement.

Only when the part is absent does the LLM propose companions. Every proposed name is
re-resolved in **strict mode**; accepted items may be priced, everything else goes to
`unpriced_items` with no price. Each list is capped at 3 in code, not just in the prompt.

### 4 · Fetch every price in one query

A single indexed `find` on `parts` filtering `make`, `model`, `generation` and
`part_name: {$in: [...]}`. One round trip covers all tiers and all BOM items.

### 5 · Apply safety rules

Keyed on the **primary** part's `part_category` — not whichever row came back first.
A Brake Pads quote pulls in items from other categories, and none of those may
trigger or suppress a rule.

`block_tiers` is `;`-separated; `restraint_system` and `ev_drivetrain` each block two
tiers. Blocked tiers are dropped from `tiers`, listed in `suppressed_tiers`, and the
reason is appended to `warnings`.

Of the 14 rules, **6 are restrictive and 8 are explicit no-restriction records**
(empty `block_tiers`). An empty rule means "reviewed, all tiers may be sold" —
which is not the same as no rule at all. Two are marked `REVIEW:` in their reason
text as candidates for future restriction: economy catalytic converters
(emissions certification) and economy headlamps (beam pattern and glare).

### 6 · Build the tier baskets

For each surviving tier, take the cheapest row **per item**, sum into
`tier_total_lkr`, and set `complete: false` if any item has no row at that tier.

A tier basket is a price floor, not a purchase order — the Certified basket for
brake pads spans Bendix, Akebono and TRW.

> `complete: false` is a normal outcome, not an error. 122 vehicle/part groups
> genuinely stock fewer than three tiers. It means "no row at this tier", which is
> **not** the same as "this tier was withheld" — that is `suppressed_tiers`. A UI
> that conflates them will mislead.

### Cost of a typical request

3 MongoDB round trips (generations, bom_dependencies, parts) plus a small
`safety_rules` lookup. **0 network calls, 0 LLM calls** on a curated part. The
resolver runs entirely in memory against an index built once at process start.

---

## The part name resolver

A mechanic types `dynamo`, `shockers`, `dicky door`, `MAF senser`. A plain lookup
finds none of them. Each stage is cheaper and more certain than the one below, and
only runs when everything above has missed.

| # | Stage | Accepts at | Method | Catches |
|---|---|---|---|---|
| 1 | **Exact** | 1.0 | `exact` / `alias_exact` | Whole string is a catalog name or alias |
| 2 | **Alias n-gram** | 0.9 | `alias_partial` | A known term inside a longer phrase |
| 3 | **BM25** | ≥ 0.45 | `bm25` | Word overlap, any order |
| 4 | **Fuzzy** | ≥ 80 | `fuzzy` | Misspellings |
| — | **Honest failure** | 0.0 | `none` | Returns top-3 candidates, never a guess |

### How each stage works

**Alias n-gram.** An n-gram is a run of N consecutive words. `"dynamo not charging"`
generates `dynamo not charging` / `dynamo not` / `not charging` / `dynamo` / `not` /
`charging`. Each window is checked against the 283 alias keys + 70 catalog names,
**longest first**, so `dicky door` beats `door`. Zero approximation — a window either
is a known term or it isn't. Returns `None` when two different parts are named at the
same length, rather than guessing.

**BM25.** The classic information-retrieval ranking function. Each of the 70 part
names is a tiny document; the query is scored against all of them.

```
query "sensor mass air"  →  Mass Air Flow Sensor  7.307
                            Air Filter            3.342
                            Oxygen Sensor         3.342
                            AC Compressor         0.000
```

Two ideas make it work. **Rare words count more** (IDF): `mass` appears in 1 name so
it nearly proves the match; `sensor` appears in 2 so it's ambiguous; `brake` appears
in 6 so it's nearly worthless alone. And **word order is irrelevant** — `"sensor mass
air"` scores identically to `"mass air sensor"`.

Raw BM25 scores are unbounded, so they're normalised by dividing by the score the
winning name achieves against itself, giving a 0–1 ratio to threshold on.

**Fuzzy.** `rapidfuzz`'s `token_sort_ratio` — character-level edit distance as a
0–100 score, with words sorted first so order is neutralised. This is the only stage
that survives a typo:

```
'altenator' → BM25 best score        0.000   (no shared token — helpless)
'altenator' → fuzzy vs 'alternator'   94.7   (one missing 'r')
```

It is also the most expensive (353 string comparisons), which is why it sits last.

### Strict mode

`resolve(raw, allow_partial=False)` disables the n-gram stage and requires a BM25
match to be built only from words the part owns. Used **only** for LLM-proposed
names. See [Design decisions](#3--the-09-vs-07-pricing-collision).

### Two deliberate subtleties

**Position words are stripped for ranking, not for exact lookup.** `normalize()`
drops `front / rear / left / right / side` so "front brake pad" cannot rank Front
Bumper above Brake Pads. But six catalog names *are* position-qualified (Front
Bumper, Rear Bumper, Front Door, Front Fender, Rear Hatch, Side Mirror), so exact
lookups run against the punctuation-stripped form first.

**Ambiguous reductions are refused, not resolved.** `front lamp`→Headlight and
`tail lamp`→Tail Light both reduce to `lamp`; `front buffer` and `rear buffer` both
reduce to `buffer`. Rather than let dictionary insertion order pick a winner, those
keys are excluded from the exact map and fall through to ranking. The constructor
reports them on startup.

---

## The core rule, and how it is enforced

An LLM is consulted for exactly one thing — which companion parts a repair also
needs — and only when `bom_dependencies` has no entry for the part. It proposes
**names**. Every name is re-resolved against the catalog, and every price and part
number is read from MongoDB.

Enforcement, not assertion:

- The LLM lives in one function, `_propose_bom_via_llm()`, so it can be mocked wholesale.
- A module-level `LLM_CALL_COUNT` increments **inside that function only** — a mocked
  call cannot inflate it, so "zero calls on the curated path" is measurable rather
  than claimed.
- The curated branch `return`s before the LLM branch is reachable. It is not a
  preference; the code path does not exist after a hit.
- Temperature is 0, and the prompt forbids prices, part numbers and brands.
- `test_curated_part_never_calls_the_llm` patches the function to **raise**, so eight
  curated parts pricing with `LLM_CALL_COUNT == 0` proves the branch is unreachable.
- Fed a poisoned proposal — `"Brake Fluid DOT4 - LKR 9999 - PN FAKE-123"` — neither
  `9999` nor `FAKE` reaches the output.

**35 of 70 parts use the LLM path**, by design. Keeping the fallback live is a
deliberate product decision, not an oversight.

---

## Testing

```bash
pytest backend/test_agent4_resolver.py backend/test_agent4_procurement.py -v
# 37 passed
```

No test makes a real LLM call — every test exercising the uncurated path patches
`_propose_bom_via_llm`.

| File | Tests | Covers |
|---|---:|---|
| `test_agent4_resolver.py` | 10 | Each matching stage, honest failure, the `Rear Bumper` precedence regression, embedded aliases, longest-n-gram-wins, ambiguity refusal |
| `test_agent4_procurement.py` | 27 | Core rule (adversarially), poisoned-output containment, LLM degradation, strict-mode acceptance and rejection, safety-rule keying, tier arithmetic verified row-by-row against the DB, graceful failure, response contract |

### Running individual pieces

| Command | What it does |
|---|---|
| `python backend/data/generate_tables.py` | Rebuild CSVs + integrity checks |
| `python backend/seed_agent4.py` | Drop and reload MongoDB |
| `python backend/agent4_resolver.py` | Resolver self-test, one probe per stage |
| `python backend/agent4_procurement.py` | Five end-to-end quotes with live LLM-call counts |
| `python eval/run_eval.py` | Retrieval metrics |

---

## Evaluation

`eval/run_eval.py` scores `eval/testset.csv` (40 queries) for Precision@1, Recall@3
and MRR, with per-stage ablation.

| Config | Flags | P@1 | R@3 | MRR |
|---|---|---:|---:|---:|
| exact only | `--no-bm25 --no-fuzzy --no-alias-ngram` | 0.125 | 0.125 | 0.125 |
| exact + BM25 + fuzzy | `--no-alias-ngram` | 0.650 | 0.825 | 0.729 |
| full pipeline | — | **1.000** | **1.000** | **1.000** |

The harness validates that every `expected` label exists in
`db.parts.distinct("part_name")` before scoring, since a bad label can never be
scored correctly and would silently drag the numbers.

### ⚠ Do not quote the 1.000 as a retrieval result

The n-gram stage **alone**, with BM25 and fuzzy both disabled, also scores 1.000.
Every one of the 40 queries contains a verbatim surface form from `part_aliases.csv`
or the catalog — 30 from the alias table, 10 from catalog names. Even the apparent
typo-robustness is pre-enumerated: `water pomp` and `maf` are themselves alias keys.

**The benchmark measures alias-table coverage, not retrieval quality.** The test set
and the alias table appear to have been authored from the same vocabulary source,
which makes the evaluation circular. It also can no longer discriminate BM25 from
fuzzy, since the pre-pass short-circuits both.

**Honest held-out figure: Precision@1 ≈ 0.625** on 8 trade terms deliberately absent
from the alias table (up from 0.500 before the vocabulary expansion). Treat it as
indicative only — it is 8 queries.

**To make the number defensible:** build a held-out test set whose trade vocabulary is
disjoint from `part_aliases.csv`. Then `--no-alias-ngram` measures generalisation and
the full config measures production behaviour, and the gap between them is the honest
cost of relying on a curated table.

---

## Design decisions and why

Each of these is a real bug that was caught and fixed. They are documented because
the reasoning is not obvious from the code alone.

### 1 · `"Rear Bumper"` returned Front Bumper at confidence 1.0

`bumper` is a real alias for Front Bumper. The first implementation normalised the
query before *every* exact lookup, so `"Rear Bumper"` reduced to `"bumper"` and hit
the alias map before its own literal catalog-name match was tried — a confidently
wrong part.

**Fix:** strict per-form precedence. The full punctuation-stripped string is tried
against aliases *and* names before the stopword-stripped form is tried against
either. Locked in by `test_rear_bumper_does_not_resolve_to_front_bumper`.

### 2 · Fuzzy matching was case-sensitive

`token_sort_ratio` is case-sensitive by default, and the choice list mixed
capitalised catalog names with lowercase alias keys. Every catalog name lost ~10
points on every comparison:

```
'altenator' vs 'Alternator'   84.2
'altenator' vs 'alternator'   94.7
```

Typos were rejected purely for capitalisation — `radaitor` scored 75.0 as-is
(rejected) but 87.5 lowercased. **Fix:** both sides go through `squash()`, with a
`_fuzzy_canonical` map back.

### 3 · The 0.9 vs 0.7 pricing collision

`alias_partial` returned 0.9 and Agent 4 priced any LLM proposal at ≥ 0.7, so
`"whatever pads they use"` became a priced set of Brake Pads.

Lowering `ALIAS_PARTIAL_CONFIDENCE` would have been wrong — for a mechanic's query an
embedded alias genuinely *is* strong evidence. The asymmetry is in the caller: a
mechanic writes symptoms around the part name; a model asked for catalog names has no
such excuse.

**Raising the threshold would have changed nothing.** Four vague proposals scored
exactly **1.000** through BM25, because the normalisation divides by the winning
name's self-score — any query containing `horn` scores a perfect 1.0 against the
one-token name `Horn`. `"maybe a horn"` was arithmetically indistinguishable from
`"Horn"`. No threshold can separate those.

**Fix:** strict mode for machine proposals — skip the n-gram stage, and require the
proposal to be built only from words the part owns (its name plus its aliases).

| | before | after |
|---|---:|---:|
| vague proposals priced | 4 of 8 | **0 of 8** |
| clean proposals priced | 15 of 16 | **15 of 16** |

Reordering still passes (`"Coolant Engine"`); padding does not (`"possibly the radiator"`).

**Known residual:** `"Engine Coolant"` scores 0.633 and lands in `unpriced_items`,
because the catalog name is `Engine Coolant 4L`. Containment passes; the 0.7 floor
rejects it. That is a conservative, *visible* failure. Lowering `LLM_RESOLVE_ACCEPT`
to 0.6 would admit it — an open tuning decision, deliberately not made unilaterally.

### 4 · BM25 candidates were meaningless on a total miss

When a query shares no token with any name, every BM25 score ties at 0 and "top 3"
is just the first three names in index order. `"flux capacitor"` was returning
`AC Compressor, AC Condenser, Air Filter`. **Fix:** fall back to fuzzy ranking for
candidates when no BM25 score exceeds zero.

### 5 · The resolver is a lazy singleton, not built at import

Building at true module scope would make importing `agent4_procurement` require a
live MongoDB, breaking `main.py` startup and making the module untestable offline.
Built once on first use instead; `id()` is stable.

### 6 · Parse-then-drop in the seed script

`seed_agent4.py` reads and validates all five CSVs *before* dropping anything. The
drop still precedes every insert, but a malformed CSV or duplicate alias now aborts
with the database intact rather than wiping it and then failing.

---

## Limitations

Measured, not estimated.

1. **Half the catalog has no curated BOM.** 35 of 70 part names reach the LLM path.
   This is now a deliberate product decision, but it means half of all quotes depend
   on a network call and a model's judgement.
2. **The evaluation is circular** — see [Evaluation](#evaluation). Held-out P@1 ≈ 0.625.
3. **`alias_partial` has no notion of negation or recency.**
   `"replaced pads already, now disc is scored"` resolves to **Brake Pads** — the one
   part already done. `"screen washer arm worn"` resolves to **Control Arm** via the
   embedded alias `arm`. Both at 0.9. This affects user queries; strict mode only
   protects the LLM path.
4. **Generation boundaries overlap.** Ranges touch rather than abut, so a 2018 Corolla
   matches two generations. Agent 4 picks the newer and warns, but without a VIN it
   cannot know.
5. **Prices are static and undated.** No effective date, no currency field, no
   supplier, no stock level. For a market with imported parts and a moving exchange
   rate, this is the shortest-lived part of the data. Every price is synthetic
   (segment-scaled), not a surveyed market figure.
6. **It is a parts quote, not a job quote.** No labour hours, shop rate, or tax.
7. **Fitment stops at the generation.** No trim, engine variant or drivetrain. Two
   E210 Corollas with different engines get an identical MAF quote.
8. **Coverage is 109 make/model pairs across 20 makes.** Anything else returns a
   valid response whose only content is a warning.
9. **Incomplete tiers are easy to misread** — see step 6 above.
10. **Only 13 of 124 generations are reachable end-to-end** through the NLP intake
    path, because Agent 1's vocabulary is US-market. See `docs/OTHER-AGENTS.md`.

### Improvement backlog

| Priority | Change | Why |
|---|---|---|
| High | Decide `LLM_RESOLVE_ACCEPT` 0.7 → 0.6 | Admits legitimate partial names like `"Engine Coolant"` |
| High | Held-out test set disjoint from `part_aliases.csv` | Turns the eval from a coverage check into a generalisation measure |
| Med | Put alias surface forms in the BM25 corpus | The architectural fix the n-gram pre-pass approximates; makes the ablation meaningful again |
| Med | Negation/recency handling in the n-gram pre-pass | Detect "not the X", "already replaced X" and suppress that match |
| Med | `price_updated`, `currency`, `supplier` on `parts` | Lets the UI flag a stale quote |
| Med | Resolve the two `REVIEW:` safety rules | Economy catalytic converters and headlamps |
| Later | `labour_hours` per part → a job quote | The number a customer actually wants |
| Later | VIN-based generation disambiguation | Agent 1 already talks to vPIC, which decodes VINs |

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `PermissionError` on `parts.csv` | The CSV is open in Excel, which holds an exclusive lock. Close it. |
| `ModuleNotFoundError` for pymongo/rank_bm25 | Wrong virtualenv. `.venv` at the repo root has the Agent 4 dependencies; `backend/venv` contains only pip. |
| Quote returns nothing for a valid vehicle | Check `year` is an `int`, not a string. String years make the range query return nothing silently. |
| `uvicorn main:app` fails at import | `main.py:4` imports `agent3_rag`, which needs `chromadb`. Not an Agent 4 problem. |
| Seed wiped the wrong database | `seed_agent4.py` is destructive against whatever `MONGO_DB` points at. `.env` may point at the shared Atlas cluster, not localhost. |
| `alias_partial` matched the wrong part | Expected for negated phrasing — see limitation 3. |

---

## Current state

**Working and verified:** 37 tests pass, generator integrity clean, 24,233 documents
seeded, all five resolver stages route correctly, route returns 200/422/500 correctly,
core rule holds adversarially.

**Not done:**

1. **Nothing assembles the procurement request.** Agent 4 needs Agent 1's vehicle
   *and* Agent 2's diagnosis in one object. No orchestrator, route or frontend code
   holds both and calls `/api/v1/procure`.
2. **The frontend is not wired.** `App.jsx` describes the MongoDB catalog in prose
   and renders an Agent 4 panel, but contains no call to the endpoint.
3. **The route has never run under uvicorn.** `main.py` fails to import without
   `chromadb`. Agent 4's route was verified through stubbed Agent 1/3 modules.
4. **Two virtualenvs exist** — `.venv` (correct) and `backend/venv` (pip only).
   Worth deleting the latter.

---

*Figures current as of the latest regeneration: 24,233 documents, 70 part names,
109 make/model pairs, 283 resolver alias keys, 37 passing tests.*
