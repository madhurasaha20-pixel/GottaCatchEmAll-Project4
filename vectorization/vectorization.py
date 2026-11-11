from pathlib import Path

from langchain_core import documents
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from sentence_transformers import SentenceTransformer


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma"

# Embedding configuration
MODEL_NAME = "all-MiniLM-L6-v2"

# Vector database collection
COLLECTION_NAME = "pokemon_documentation"

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
                "path": document["path"]
            })

    return chunks

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
            "path": " > ".join(chunk["path"])
        })

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

def run_vectorization(chunks):
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