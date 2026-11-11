from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from sentence_transformers import SentenceTransformer
from functools import lru_cache
import json


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma"

# Embedding configuration
MODEL_NAME = "all-MiniLM-L6-v2"

# Vector database collection
COLLECTION_NAME = "pokemon_documentation"

def load_documents():
    raw_dir = BASE_DIR / "data" / "raw"
    documents = []

    for file_path in sorted(raw_dir.glob("*.json")):
        with file_path.open(encoding="utf-8") as file:
            record = json.load(file)

        for section in record.get("sections", []):
            documents.append({
                "pokemon": record["name"],
                "heading": section["heading"],
                "path": section["path"],
                "text": section["text"],
                "source_url": record.get("source_url", "")
            })

    return documents

# Chunking configuration
def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = []

    for document in documents:
        text = document.get("text", "").strip()
        if not text:
            continue

        for chunk_text in splitter.split_text(text):
            chunks.append({
                "text": chunk_text,
                "pokemon": document["pokemon"],
                "heading": document["heading"],
                "path": document["path"],
                "source_url": document.get("source_url", "")
            })

    return chunks

@lru_cache(maxsize=1)
def load_embedding_model():
    model = SentenceTransformer(
        MODEL_NAME,
        device="cpu"
    )

    return model

def generate_embeddings(chunks, model):
    texts = []

    for chunk in chunks:
        text = chunk.get("text", "").strip()

        if not text:
            raise ValueError(
                "A chunk contains empty documentation text."
            )

        texts.append(text)

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    return embeddings

# create or get a collection in ChromaDB
def initialize_chroma():
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine",
                "embedding_model": MODEL_NAME
            }
        )

    return collection

def store_chunks(chunks, embeddings, collection):
    ids = []
    documents = []
    metadatas = []

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks must match number of embeddings."
        )

    for index, chunk in enumerate(chunks):
        ids.append(
            f"{chunk['pokemon'].lower()}-{index}"
        )

        documents.append(chunk["text"])

        metadatas.append({
            "pokemon": chunk["pokemon"],
            "heading": chunk["heading"],
            "path": " > ".join(chunk["path"]),
            "source_url": chunk.get("source_url", "")
        })

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

def retrieve_chunks(question, top_k=5):
    print("Loading embedding model...")
    model = load_embedding_model()

    print("Embedding question...")
    question_embedding = model.encode(
        question,
        convert_to_numpy=True
    )

    print("Searching ChromaDB...")
    collection = initialize_chroma()

    results = collection.query(
        query_embeddings=[
            question_embedding.tolist()
        ],
        n_results=top_k
    )

    retrieved_chunks = []

    for index in range(len(results["ids"][0])):
        retrieved_chunks.append({
            "id": results["ids"][0][index],
            "text": results["documents"][0][index],
            "metadata": results["metadatas"][0][index],
            "distance": results["distances"][0][index]
        })

    return retrieved_chunks

def run_vectorization(documents):
    chunks = chunk_documents(documents)

    if not chunks:
        print("No chunks provided.")
        return None
    print("Loading embedding model...")
    model = load_embedding_model()

    print("Generating embeddings...")
    embeddings = generate_embeddings(chunks, model)

    print("Connecting to ChromaDB...")
    collection = initialize_chroma()

    print("Storing vectors...")
    store_chunks(chunks, embeddings, collection)

    print("Vectorization complete!")
    print(f"Stored {len(chunks)} chunks.")

    return collection

if __name__ == "__main__":
    documents = load_documents()
    run_vectorization(documents)