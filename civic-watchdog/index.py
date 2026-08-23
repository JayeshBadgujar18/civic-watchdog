import os
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models
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

    docs = [chunk["text"] for chunk in chunks] #[cite: 1]
    metadata = [{"start": chunk["start_time"]} for chunk in chunks] #[cite: 1]

    print(f"Indexing {len(docs)} chunks into Qdrant...")

    embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
    embeddings = list(embedding_model.embed(docs))
    if not embeddings:
        return client

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=len(embeddings[0]),
                distance=models.Distance.COSINE,
            ),
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={**metadata[point_id], "document": docs[point_id]},
            )
            for point_id, embedding in enumerate(embeddings)
        ],
    )
    
    print("Indexing complete!")
    return client