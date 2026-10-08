import chromadb

import os
client = chromadb.PersistentClient(
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents", "agent3_rag", "chroma_db")
)
collection = client.get_collection(name="oem_manuals")

# Pull all documents and their tags
results = collection.get()

from collections import Counter
print("Chunks per vehicle:", dict(Counter(m["vehicle"] for m in results["metadatas"])))

for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"]), start=1):
    print(f"=== Chunk {i} ===")
    print(f"Metadata: {meta}")
    print(f"Text:\n{doc}\n")