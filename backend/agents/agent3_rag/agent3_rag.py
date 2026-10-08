import chromadb
import json
import asyncio
import re
from openai import AsyncOpenAI 
import os
from dotenv import load_dotenv

# Load the secret key from your .env file
load_dotenv()

from openai import AsyncOpenAI

# Ensure you have your OPENAI_API_KEY set in your environment or a .env file later
client = AsyncOpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
) 

GENERIC_VEHICLE = "Generic OBD-II"


def _matching_vehicles(collection, vehicle_model: str) -> list:
    """Vehicles in the DB whose make and model appear in the requested vehicle string.
    Prefers an exact-year match, falls back to the same make/model in other years."""
    wanted = vehicle_model.lower()
    known = {}
    for meta in collection.get(include=["metadatas"])["metadatas"]:
        if meta and meta.get("make") and meta.get("model"):
            known[meta["vehicle"]] = meta
    matches = [m for m in known.values() if m["make"] in wanted and m["model"] in wanted]
    exact = [m for m in matches if m["year"] in wanted]
    return sorted({m["vehicle"] for m in (exact or matches)})


DTC_PATTERN = re.compile(r"\b[PCBU][0-3][0-9A-F]{3}\b", re.I)


def retrieve_chunks(collection, target_component: str, vehicle_model: str, dtc_codes=None) -> dict:
    """Search the requested vehicle's manual plus the generic OBD-II diagnostics, vehicle-specific
    chunks first. Embeddings handle bare OBD codes (e.g. "P0300") poorly, so any codes in the query
    are first matched exactly against the per-code metadata flags (dtc_P0300), falling back to plain
    semantic search if nothing carries that code. The vehicle is deliberately left out of the query
    text; the metadata filter already restricts it. `dtc_codes` are the codes Agent 1 found; Agent 2's
    root-cause text is plain language ("Intake vacuum system ...") that rarely matches a manual title,
    so the codes are what reliably find the diagnostic entry."""
    query_text = [f"{target_component} repair diagnosis procedure"]
    found = DTC_PATTERN.findall(target_component) + [c for c in (dtc_codes or []) if DTC_PATTERN.fullmatch(c.strip())]
    codes = list(dict.fromkeys(c.strip().upper() for c in found))
    code_flags = [{f"dtc_{c}": True} for c in codes]
    vehicles = _matching_vehicles(collection, vehicle_model)

    def search(vehicle_names, n, use_codes):
        if not vehicle_names:
            return [], []
        where = {"vehicle": {"$in": vehicle_names}}
        if use_codes:
            where = {"$and": [where, code_flags[0] if len(code_flags) == 1 else {"$or": code_flags}]}
        res = collection.query(query_texts=query_text, n_results=n, where=where)
        return res["documents"][0], res["metadatas"][0]

    for use_codes in ([True, False] if codes else [False]):
        specific = search(vehicles, 2, use_codes)
        generic = search([GENERIC_VEHICLE], max(2, len(codes)), use_codes)
        documents, metadatas = specific[0] + generic[0], specific[1] + generic[1]
        if documents:
            break
    # code_matched: every chunk carries one of the reported codes (exact lookup, not a guess)
    return {"documents": [documents], "metadatas": [metadatas], "code_matched": bool(documents and codes and use_codes)}


async def get_repair_procedure(target_component: str, vehicle_model: str, dtc_codes=None) -> dict:
    print(f"Searching manuals for: {target_component}...")
    
    # 1. Connect to local ChromaDB (agent directory with fallback to root)
    chroma_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
    if not os.path.exists(chroma_dir):
        chroma_dir = os.path.abspath("./chroma_db")
    db_client = chromadb.PersistentClient(path=chroma_dir)
    collection = db_client.get_collection(name="oem_manuals")

    # 2. Execute Vector Search, restricted to the requested vehicle's manual (plus generic OBD-II content)
    results = retrieve_chunks(collection, target_component, vehicle_model, dtc_codes)

    if not results['documents'][0]:
        return {"steps": [], "torque_specs": "", "citation": "",
                "error": f"No manual found for {vehicle_model}"}
    retrieved_context = "\n\n".join(results['documents'][0])
    print("\n--- Retrieved Context ---")
    print(retrieved_context)
    print("-------------------------\n")

    # 3. Strict RAG Prompt to prevent hallucination
    if results.get("code_matched"):
        # The match was made by exact OBD-code lookup in code, so don't let the model second-guess it
        # because Agent 2's component wording differs from the manual's title.
        match_note = (
            "The CONTEXT sections below were matched to the reported OBD-II code(s) by exact code lookup, "
            "so they ARE the correct manual for this job. Do NOT return the 'No matching manual' error. "
            f"Treat '{target_component}' as the suspected component: put the checks that involve it first, "
            "then the remaining steps from the section."
        )
    else:
        match_note = ""
    prompt = f"""
    You are a Master Automotive Technician. 
    Extract a step-by-step repair guide for a {vehicle_model} {target_component}.
    Reported OBD-II codes: {', '.join(dtc_codes) if dtc_codes else 'none'}.
    {match_note}

    STRICT RULES:
    1. ONLY use the context provided below. Do not guess.
    2. Preserve exact torque specifications.
    3. If the context says the torque is "NOT VERIFIED", torque_specs MUST begin with
       "UNVERIFIED - confirm in OEM service manual: " followed by any value given.
       If no torque value is given, set torque_specs to "Not available - consult OEM service manual".
    4. ONLY use context sections whose [Vehicle: ...] matches the {vehicle_model}, or is
       "Generic OBD-II" (code diagnostics that apply to any vehicle). Prefer the vehicle-specific
       section when both exist. If no section matches that vehicle and component/code, return
       {{"steps": [], "torque_specs": "", "citation": "", "error": "No matching manual"}}.
    
    CONTEXT:
    {retrieved_context}
    
    Return ONLY valid JSON in this format:
    {{"steps": ["step 1", "step 2"], "torque_specs": "...", "citation": "..."}}
    """

    # 4. Generate Synthesized Output
    print("Synthesizing repair steps via LLM...")
    response = await client.chat.completions.create(
        model="openai/gpt-oss-20b",
        response_format={ "type": "json_object" },
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0 
    )

    return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    # Test the agent directly
    result = asyncio.run(get_repair_procedure("Mass Air Flow Sensor", "2018 Toyota Corolla"))
    print("\nFINAL AGENT 3 JSON PAYLOAD:")
    print(json.dumps(result, indent=2))