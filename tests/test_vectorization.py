import pytest
pytest.importorskip('chromadb')
pytest.importorskip('sentence_transformers')
import numpy as np
from vectorization.vectorization import generate_embeddings, store_chunks

def test_reject_empty_chunk_text_before_encoding():
    with pytest.raises(ValueError,match='empty documentation'):generate_embeddings([{'text':' '}],None)

def test_reject_mismatched_chunk_embedding_counts():
    with pytest.raises(ValueError,match='match'):store_chunks([{'pokemon':'Pikachu','text':'a'}],np.zeros((0,3)),None)

def test_store_vectors_in_real_ephemeral_chroma():
    import chromadb
    collection=chromadb.EphemeralClient().get_or_create_collection('pokemon_test_collection')
    chunks=[{'pokemon':'Pikachu','heading':'Biology','path':['Pikachu','Biology'],'text':'Electric mouse'}]
    store_chunks(chunks,np.array([[0.1,0.2,0.3]],dtype=np.float32),collection)
    saved=collection.get(ids=['pikachu-0'],include=['documents','metadatas'])
    assert saved['documents']==['Electric mouse']
    assert saved['metadatas'][0]['path']=='Pikachu > Biology'
