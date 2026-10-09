import os
import re
import glob
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANUALS_DIR = os.path.join(BASE_DIR, "manuals")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "oem_manuals"

# Procedures are short, so they normally stay as one chunk. Only unusually long
# ones are split, and every sub-chunk gets the vehicle/component header back.
MAX_CHUNK_CHARS = 3000

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=MAX_CHUNK_CHARS,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " "],
)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def parse_block(block: str):
    """Parse one '---' separated procedure block into (header, body, metadata)."""
    vehicle = re.search(r"^\[Vehicle:\s*(.+?)\]\s*$", block, re.M)
    source = re.search(r"^\[Source:\s*(.+?)\]\s*$", block, re.M)
    component = re.search(r"^Component:\s*(.+?)\s*$", block, re.M)
    if not (vehicle and component):
        return None

    dtc = re.search(r"^\[DTC:\s*(.+?)\]\s*$", block, re.M)

    vehicle_name = vehicle.group(1)
    if vehicle_name.lower().startswith("generic"):
        # Vehicle-independent content (e.g. OBD-II code diagnostics)
        year, make, model = "", "generic", ""
    else:
        parts = vehicle_name.split(None, 2)  # "2019 Honda Civic" -> year, make, model
        year, make, model = parts[0], parts[1], parts[2] if len(parts) > 2 else ""

    header_lines = [
        f"[Vehicle: {vehicle_name}]",
        f"[Source: {source.group(1)}]" if source else None,
        f"[DTC: {dtc.group(1)}]" if dtc else None,
        f"Component: {component.group(1)}",
    ]
    header = "\n".join(line for line in header_lines if line)
    body = "\n".join(
        line for line in block.splitlines()
        if not re.match(r"^(\[Vehicle:|\[Source:|\[DTC:|Component:)", line)
    ).strip()

    metadata = {
        "vehicle": vehicle_name,
        "year": year,
        "make": make.lower(),
        "model": model.lower(),
        "component": component.group(1),
        "source": source.group(1) if source else "",
        "dtc": dtc.group(1) if dtc else "",
    }
    if dtc:
        # One boolean flag per code so retrieval can match a code exactly (e.g. dtc_P0300),
        # not as a substring of text that merely mentions it.
        for code in re.findall(r"[PCBU][0-3][0-9A-F]{3}", dtc.group(1).upper()):
            metadata[f"dtc_{code}"] = True
    return header, body, metadata


def load_chunks():
    ids, documents, metadatas = [], [], []
    files = sorted(glob.glob(os.path.join(MANUALS_DIR, "*.txt")))
    if not files:
        raise SystemExit(f"No manual files found in {MANUALS_DIR}")

    for path in files:
        file_slug = slugify(os.path.splitext(os.path.basename(path))[0])
        with open(path, encoding="utf-8") as f:
            content = f.read()

        for block_no, block in enumerate(re.split(r"^---\s*$", content, flags=re.M)):
            block = block.strip()
            if not block:
                continue
            parsed = parse_block(block)
            if parsed is None:
                print(f"  WARNING: skipping block {block_no} in {os.path.basename(path)} "
                      f"(missing [Vehicle: ...] or Component: line)")
                continue
            header, body, metadata = parsed

            pieces = [body] if len(header) + len(body) <= MAX_CHUNK_CHARS else text_splitter.split_text(body)
            for piece_no, piece in enumerate(pieces):
                ids.append(f"{file_slug}_{slugify(metadata['component'])}_{block_no}_{piece_no}")
                documents.append(f"{header}\n{piece}")
                metadatas.append(metadata)
        print(f"Loaded {os.path.basename(path)}")
    return ids, documents, metadatas


def build_vector_database():
    print(f"Reading manuals from {MANUALS_DIR}")
    ids, documents, metadatas = load_chunks()
    if len(set(ids)) != len(ids):
        raise SystemExit("Duplicate chunk ids detected - check for repeated components in a manual file.")
    print(f"Prepared {len(documents)} chunks.")

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Rebuild from scratch so removed/edited manuals never leave stale chunks behind
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(name=COLLECTION_NAME)

    print("Embedding chunks into ChromaDB...")
    collection.add(ids=ids, documents=documents, metadatas=metadatas)

    print(f"Success! Vector database ready at {CHROMA_DIR} ({collection.count()} chunks).")


if __name__ == "__main__":
    build_vector_database()
