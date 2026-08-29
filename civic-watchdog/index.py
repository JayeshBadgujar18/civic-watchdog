import os
import uuid
from fastembed import SparseTextEmbedding, TextEmbedding
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

def index_documents(chunks, source_name="Unknown source"):
    """
    Embeds and indexes documents using hybrid search (Dense + Sparse/BM25).
    """
    client = get_qdrant_client()

    docs = [chunk["text"] for chunk in chunks]
    metadata = [
        {"start": chunk["start_time"], "end": chunk.get("end_time"), "source": source_name}
        for chunk in chunks
    ]
    if not docs:
        return client

    print(f"Indexing {len(docs)} chunks into Qdrant...")

    dense_embeddings = list(TextEmbedding(model_name=EMBEDDING_MODEL).embed(docs))
    sparse_embeddings = list(SparseTextEmbedding(model_name=SPARSE_MODEL).embed(docs))

    if client.collection_exists(COLLECTION_NAME):
        collection = client.get_collection(COLLECTION_NAME)
        vectors = collection.config.params.vectors
        sparse_vectors = collection.config.params.sparse_vectors
        is_hybrid = (
            isinstance(vectors, dict)
            and "dense" in vectors
            and sparse_vectors is not None
            and "sparse" in sparse_vectors
        )
        if not is_hybrid:
            client.delete_collection(COLLECTION_NAME)

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": models.VectorParams(
                    size=len(dense_embeddings[0]),
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense": dense_embedding.tolist(),
                    "sparse": models.SparseVector(
                        indices=sparse_embedding.indices.tolist(),
                        values=sparse_embedding.values.tolist(),
                    ),
                },
                payload={**metadata[point_id], "document": docs[point_id]},
            )
            for point_id, (dense_embedding, sparse_embedding)
            in enumerate(zip(dense_embeddings, sparse_embeddings))
        ],
    )

    print("Indexing complete!")
    return client