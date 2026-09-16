import chromadb
import json
import asyncio
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

async def get_repair_procedure(target_component: str, vehicle_model: str) -> dict:
    print(f"Searching manuals for: {target_component}...")
    
    # 1. Connect to your local ChromaDB
    db_client = chromadb.PersistentClient(path="./chroma_db")
    collection = db_client.get_collection(name="oem_manuals")

    # 2. Execute Vector Search
    query_text = f"{vehicle_model} {target_component} replacement procedure"
    results = collection.query(
        query_texts=[query_text],
        n_results=1 
    )
    
    retrieved_context = "\n".join(results['documents'][0])
    print("\n--- Retrieved Context ---")
    print(retrieved_context)
    print("-------------------------\n")

    # 3. Strict RAG Prompt to prevent hallucination
    prompt = f"""
    You are a Master Automotive Technician. 
    Extract a step-by-step repair guide for a {vehicle_model} {target_component}.
    
    STRICT RULES:
    1. ONLY use the context provided below. Do not guess.
    2. Preserve exact torque specifications.
    
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