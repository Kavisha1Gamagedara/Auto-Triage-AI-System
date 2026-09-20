# Improvement Plan — Agents 1, 2 and 3

Findings from auditing Agents 1–3 against the working Agent 4 implementation.
Everything here was measured against the live codebase and catalog, not estimated.

**Written for whoever owns Agents 1–3.** Agent 4's own documentation is in
[`AGENT4.md`](./AGENT4.md).

---

## Summary

| Agent | State | Headline problem |
|---|---|---|
| **1 — Ingestion** | Works, wrong market | Can extract only **10 of 20** makes Agent 4 prices |
| **2 — Diagnosis** | Healthy | Debug prints in production; no JSON repair; unconstrained output vocabulary |
| **3 — Repair RAG** | **Cannot run** | No vector DB, and the entire corpus is 490 bytes covering one part |

> **The single highest-value fix:** only **13 of 124 vehicle generations (10%)** are
> reachable end to end through the NLP intake path. Fixing Agent 1's vocabulary
> unlocks the other 90% of a catalog that already exists.

---

## 0 · Before anything else

Two agents are **silently degraded** because dependencies are missing:

```bash
pip install -r backend/requirements.txt
python -m spacy download en_core_web_sm
```

- `en_core_web_sm` is not installed, so `nlp_extractor.py` falls back to
  `spacy.blank("en")`. **There is no NER at all** — only dictionary matching. The
  warning scrolls past on startup and is easy to miss.
- `chromadb` is not installed, so `main.py` fails at line 4 and **the whole API
  cannot start**.

---

## 1 · The systemic problem: Agent 1 and Agent 4 target different countries

Agent 1's vocabulary is US-market. Agent 4's catalog is Sri Lankan.

| | Agent 1 knows | Agent 4 prices | Overlap |
|---|---:|---:|---:|
| Makes | 27 | 20 | **10** |
| Models | 47 | 109 | **9** |
| Generations reachable end-to-end | | | **13 / 124** |

**Agent 4 prices but Agent 1 cannot extract:**
`Suzuki`, `Mitsubishi`, `Daihatsu`, `Isuzu`, `Micro`, `Perodua`, `Tata`,
`Mahindra`, `Land Rover`, `BYD`

**Agent 1 extracts but Agent 4 cannot price:**
`Acura`, `Buick`, `Cadillac`, `Chevrolet`, `Chrysler`, `Dodge`, `GMC`, `Infiniti`,
`Jeep`, `Lexus`, `Lincoln`, `Porsche`, `Ram`, `Subaru`, `Tesla`, `Volkswagen`, `Volvo`

Only 9 of Agent 4's 109 models are extractable: `CR-V`, `CX-5`, `Civic`, `Corolla`,
`Elantra`, `Santa Fe`, `Sorento`, `Sportage`, `Tucson`. Missing are the backbone of
the Sri Lankan fleet — `Aqua`, `Vitz`, `Axio`, `Premio`, `Allion`, `Wagon R`,
`Alto`, `Vezel`, `Fit`, `Noah`, `Voxy`, and 89 others.

### It compounds: the validation gate

`nhtsa_validator.py` queries **NHTSA vPIC, a US government database**. A Micro Panda
or Perodua Axia does not exist there, so even if Agent 1 could extract them,
[`main.py:112`](../backend/main.py#L112) rejects the request with a **400**.

The offline fallback in `nhtsa_validator.py:67` allow-lists 28 makes — all US-market,
same assumption.

**The validation gate structurally excludes the fleet Agent 4 was built for.**

### What to do

1. **Extend `AUTOMOTIVE_MAKES` and `POPULAR_MODELS`** in `nlp_extractor.py` to match
   Agent 4's catalog. The authoritative lists are one query away:
   ```python
   from db import get_db
   makes  = get_db().generations.distinct("make")    # 20
   models = get_db().generations.distinct("model")   # 109
   ```
   Better still, **generate the vocabulary from the catalog** at startup so the two
   agents cannot drift apart again.

2. **Decide what NHTSA verification is for.** Three defensible options:
   - Make it advisory — set `is_verified: false` and continue, rather than 400.
   - Skip it when the make is in the Agent 4 catalog (a vehicle we can price is a
     vehicle we accept).
   - Replace it with a local check against `generations`, and keep vPIC only for
     VIN decoding.

   The current behaviour — hard-rejecting vehicles the system can fully service — is
   the one option that cannot be right.

3. **Align the component vocabulary.** 14 of Agent 1's 73 `AUTOMOTIVE_COMPONENTS`
   do not resolve against Agent 4's catalog:
   ```
   axle · intercooler · quarter panel · rocker panel · spoiler · sway bar
   taillight · taillights · tire · tires · trunk · turbo · turbocharger · window
   ```
   Split these two ways:
   - **Cheap alias additions on the Agent 4 side** — `taillight`/`taillights` →
     Tail Light, `trunk` → Rear Hatch, `sway bar` → Stabiliser Link. These are real
     trade terms and should be in `part_aliases`.
   - **Genuinely absent from the catalog** — `tire`, `turbo`, `intercooler`,
     `window`, `spoiler`, `axle`. Either add them to `PARTS_MASTER` in
     `generate_tables.py`, or drop them from Agent 1 so it stops extracting parts
     nothing downstream can price.

---

## 2 · Agent 3 (Repair RAG) — cannot run

This is the weakest component by a wide margin. It is a demo stub, not a working agent.

### 2.1 · The vector database does not exist

`chroma_db/` is absent from the repo and `ingest_manuals.py` has never been run in
this checkout. `get_collection("oem_manuals")` at
[`agent3_rag.py:24`](../backend/agent3_rag.py#L24) raises on the first call.

**Fix:** run `python backend/ingest_manuals.py` as a documented setup step, and add
`chroma_db/` to `.gitignore` if it isn't already.

### 2.2 · The entire corpus is 490 bytes

`manual_data.txt` contains **one procedure** — MAF sensor replacement on a 2018
Toyota Corolla. That is the whole knowledge base.

Combined with `n_results=1` at [`agent3_rag.py:30`](../backend/agent3_rag.py#L30),
**every query for every part on every vehicle retrieves the same MAF passage.**
Agent 3 will confidently return MAF sensor instructions for a brake job, complete
with a citation.

**Fix, in order:**
1. Raise `n_results` to 3–5 so retrieval has something to rank.
2. Expand the corpus. For parity with Agent 4 it needs procedures for at least the
   35 parts that have curated BOM entries.
3. Add a relevance floor — if the best chunk scores below a threshold, return
   "no procedure found" rather than the nearest unrelated passage. **Agent 4's
   honest-failure pattern is directly reusable here:** return a valid response with
   `steps: []` and a warning, never a fabricated procedure.
4. Store `make`/`model`/`part` as chunk metadata and filter the query by them, so a
   Corolla query cannot retrieve a Vitz procedure.

### 2.3 · Errors are swallowed into a 200

[`main.py`](../backend/main.py) `/api/v1/repair` wraps everything in
`try/except` and returns `{"status": "error", "message": str(e)}` with **HTTP 200**.
The frontend cannot distinguish success from failure without parsing the body.

**Fix:** mirror `/api/v1/diagnose` and `/api/v1/procure` — raise `HTTPException` with
a real status code. A missing manual is a 200 with an empty result and a warning; a
dead ChromaDB is a 503.

### 2.4 · Inconsistent with the rest of the codebase

| | Agent 2 | Agent 3 |
|---|---|---|
| Client | sync `Groq()` | `AsyncOpenAI` pointed at Groq's compat endpoint |
| Model | `os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")` | hardcoded `"openai/gpt-oss-20b"` |
| Vehicle input | structured fields | concatenated `"2018 Toyota Corolla"` string |

Three different conventions for the same three things. The model is hardcoded to a
**smaller** model than Agent 2 uses, which is probably unintentional.

**Fix:** use the sync `Groq` client and read `GROQ_MODEL` from the environment, as
Agent 2 and Agent 4 both do. Accept `make`/`model`/`year` as separate fields —
a concatenated string cannot be filtered on.

### 2.5 · `chroma_db` path is relative to the working directory

`chromadb.PersistentClient(path="./chroma_db")` resolves against the process CWD, so
Agent 3 silently creates or misses the database depending on where uvicorn was
started. Agent 4's `seed_agent4.py` resolves its data directory from `__file__` for
exactly this reason — copy that pattern.

---

## 3 · Agent 2 (Diagnostic Reasoning) — in the best shape

No structural problems. Three refinements:

### 3.1 · Debug output on every call

[`agent2_logic.py:53-55`](../backend/agent2_logic.py#L53-L55) prints the model name,
the raw LLM output and the finish reason on every request. The comment says "remove
once everything works."

This is noisy in a demo and writes raw model output to stdout in production. Replace
with `logging.debug()`.

### 3.2 · No recovery from malformed JSON

`json.loads(raw)` then `DiagnosticResult.model_validate(...)` raises straight to a
500 if the model returns anything unparseable. `response_format={"type":"json_object"}`
makes this rare, not impossible.

**Fix:** one retry with the validation error fed back, or a fallback that returns a
low-confidence result rather than failing the whole pipeline.

### 3.3 · Output vocabulary is unconstrained

Nothing ties `root_cause_component` to Agent 4's 70 catalog names. Agent 2 can emit
"Mass Airflow Sensor Assembly" and Agent 4 has to recover it through fuzzy matching.

**Fix:** pass the catalog names into the system prompt and instruct the model to
choose from them. This makes the handoff near-lossless and turns Agent 4's resolver
into a safety net rather than a load-bearing component:

```python
from db import get_db
names = get_db().parts.distinct("part_name")   # 70 names, ~700 tokens
```

Agent 4's resolver still handles mechanic free-text, which is its real job.

---

## 4 · Cross-cutting

### 4.1 · The README describes a system that does not exist

The root `README.md` says the workflow is "orchestrated with **LangGraph**". There is
no LangGraph anywhere in the codebase — every agent is a plain function called
directly from a FastAPI route. The repository layout section is also missing
`agent2_logic.py`, `agent3_rag.py`, `db.py`, `agent4_*.py`, `data/` and `eval/`.

### 4.2 · Nothing orchestrates the fork-join

The README's diagram shows Agent 2 forking into Agents 3 and 4 and joining into a
final report. **No code does this.** Each agent has its own endpoint and the client
would have to call them in sequence itself. In particular, nothing assembles the
Agent 4 request, which needs Agent 1's vehicle *and* Agent 2's diagnosis together.

This is the missing piece that turns four working endpoints into a pipeline.

### 4.3 · The frontend is not wired to Agents 3 or 4

`App.jsx` renders panels describing the ChromaDB manual lookup and the MongoDB parts
catalog, but contains no call to `/api/v1/procure`. The UI currently describes
capabilities it does not reach.

### 4.4 · Test coverage is uneven

| Agent | Tests |
|---|---|
| 1 | `test_pipeline.py` — smoke tests |
| 2 | `test_agent2.py` |
| 3 | **none** |
| 4 | 37 (`test_agent4_resolver.py`, `test_agent4_procurement.py`) |

Agent 3 has no tests at all, which is part of why its corpus problem went unnoticed.

### 4.5 · Two virtualenvs

`.venv` at the repo root has the full dependency set; `backend/venv` contains only
pip. Activating the wrong one produces confusing `ModuleNotFoundError`s. Delete
`backend/venv`.

---

## Suggested sequence

1. **Install the missing dependencies.** Two agents are silently degraded and the
   API cannot start.
2. **Align Agent 1's vocabulary with Agent 4's catalog, and decide the NHTSA
   question.** Unlocks 90% of the fleet. Highest value per hour of work on this list.
3. **Give Agent 3 a real corpus, `n_results > 1`, metadata filtering and a relevance
   floor.** It currently answers every question with the same passage.
4. **Fix `/api/v1/repair`'s error swallowing** and align Agent 3's client and model
   with the rest of the codebase.
5. **Build the orchestrator** that joins Agent 1 + Agent 2 into an Agent 4 request
   and runs the fork-join the README already promises.
6. **Agent 2 polish** — logging, JSON retry, constrained vocabulary.
7. **Update the root README** to describe the system as built.

---

*Measured against the live codebase and the `auto_triage` catalog: 20 makes,
109 make/model pairs, 124 generations, 70 part names.*
