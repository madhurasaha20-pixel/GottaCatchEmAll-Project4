import json
import re
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter


from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma"

# Embedding configuration
MODEL_NAME = "all-MiniLM-L6-v2"

# Vector database collection
COLLECTION_NAME = "pokemon_documentation"

#=Chunking configuration
RAW_DIR = BASE_DIR / "data" / "raw"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


#=Split raw text, then give every chunk a unique ID
def chunk_text(text, source_id, pokemon, dex_number, heading, path):
    text = text.strip()
    if not text:
        return []

    pieces = splitter.split_text(text)

    chunks = []
    for i, piece in enumerate(pieces):
        chunks.append({
            "id": f"{source_id}_chunk_{i}",
            "pokemon": pokemon,
            "dex_number": dex_number,
            "heading": heading,
            "path": path,   # list, joined into a string later in store_chunks
            # Prefix tells the embedding model where this text came from
            "text": f"{pokemon} - {' > '.join(path)}\n{piece}",
        })
    return chunks


#=Turn ONE Pokémon JSON record into chunks
def chunk_record(record):
    pokemon = record["name"]
    dex = record["dex_number"]
    base_id = f"{dex:04d}-{slugify(pokemon)}"
    chunks = []

    #=Main page sections vectorizaton.oy fi
    for s, section in enumerate(record.get("sections", [])):
        heading = section.get("heading", "Overview")
        path = section.get("path") or [heading]
        chunks += chunk_text(section.get("text", ""), f"{base_id}_s{s}",
                             pokemon, dex, heading, path)

    # Pokédex flavor text: [{"game": ..., "text": ...}]
    for j, entry in enumerate(record.get("pokedex_entries", [])):
        game = entry.get("game", "Unknown")
        chunks += chunk_text(entry.get("text", ""), f"{base_id}_dex{j}",
                             pokemon, dex, "Pokedex entries", ["Pokedex entries", game])

    # Evolution summary
    chunks += chunk_text(record.get("evolution", {}).get("text", ""), f"{base_id}_evo",
                         pokemon, dex, "Evolution", ["Evolution"])

    return chunks


#=Read every JSON record on disk and return one flat list of chunks
def load_chunks(raw_dir=RAW_DIR):
    chunks = []
    for path in sorted(Path(raw_dir).glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        chunks.extend(chunk_record(record))
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
            chunk["id"]  # CHANGED: was f"{chunk['pokemon'].lower()}-{index}"
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