import os
from qdrant_client import QdrantClient
from config import COLLECTION_NAME, EMBEDDING_MODEL, SPARSE_MODEL, QDRANT_PATH

def get_qdrant_client():
    """
    Initializes Qdrant. Uses cloud if keys are in .env, otherwise defaults to local.
    """
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if qdrant_url and qdrant_api_key:
        print("Connecting to Hosted Qdrant Cluster...")
        return QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    
    print("Connecting to Local Qdrant Database...")
    return QdrantClient(path=QDRANT_PATH)

def index_documents(chunks):
    """
    Embeds and indexes documents using hybrid search (Dense + Sparse/BM25).
    """
    client = get_qdrant_client()
    
    # 1. Set the meaning model (Dense)
    client.set_model(EMBEDDING_MODEL) #
    
    # 2. Set the exact-keyword model (Sparse/BM25)
    client.set_sparse_model(SPARSE_MODEL) #[cite: 1]
    
    # Format data for Qdrant
    docs = [chunk["text"] for chunk in chunks] #[cite: 1]
    metadata = [{"start": chunk["start_time"]} for chunk in chunks] #[cite: 1]
    
    print(f"Indexing {len(docs)} chunks into Qdrant...")
    
    # Qdrant handles embedding both dense and sparse types automatically
    client.add(
        collection_name=COLLECTION_NAME,
        documents=docs,
        metadata=metadata
    ) #[cite: 1]
    
    print("Indexing complete!")
    return client