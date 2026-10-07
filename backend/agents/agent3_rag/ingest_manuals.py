import os
import chromadb
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def build_vector_database():
    # 1. Load the manual text from the file you just created
    print("Loading manual_data.txt...")
    loader = TextLoader("manual_data.txt")
    docs = loader.load()

    # 2. Chunk the text intelligently
    # RecursiveCharacterTextSplitter ensures we don't cut sentences or torque specs in half
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300, 
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Split document into {len(chunks)} manageable chunks.")

    # 3. Initialize ChromaDB
    # This will create a new folder named 'chroma_db' in your backend directory
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create a collection (think of this like a table in a database)
    collection = client.get_or_create_collection(name="oem_manuals")

    # 4. Insert chunks into the database
    print("Embedding chunks into ChromaDB...")
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk.page_content],
            ids=[f"chunk_{i}"]
        )
        
    print("Success! Vector database is ready.")

if __name__ == "__main__":
    build_vector_database()