import os
from fastembed import SparseTextEmbedding, TextEmbedding
from google import genai
from google.genai import types
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client.http import models
from config import RERANKER_MODEL, LLM_MODEL, GEMINI_API_KEY
from index import get_qdrant_client, COLLECTION_NAME
from config import EMBEDDING_MODEL, SPARSE_MODEL

# Load the reranker (runs locally, very accurate)
reranker = TextCrossEncoder(model_name=RERANKER_MODEL) 
dense_embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
sparse_embedding_model = SparseTextEmbedding(model_name=SPARSE_MODEL)
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def retrieve_and_rerank(query: str):
    """
    Executes a 2-stage retrieval: Fast hybrid search followed by deep cross-encoder reranking.
    """
    client = get_qdrant_client()
    
    dense_query = next(dense_embedding_model.embed([query])).tolist()
    sparse_query = next(sparse_embedding_model.embed([query]))

    # STAGE 1: retrieve with both dense meaning and sparse keyword signals.
    candidates = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(query=dense_query, using="dense", limit=20),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_query.indices.tolist(),
                    values=sparse_query.values.tolist(),
                ),
                using="sparse",
                limit=20,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=20,
    ).points
    
    valid_candidates = [
        hit for hit in candidates
        if hit.payload and hit.payload.get("document") is not None
    ]
    candidate_texts = [hit.payload["document"] for hit in valid_candidates]
    candidate_metadata = [
        {
            "start": hit.payload.get("start", 0),
            "end": hit.payload.get("end"),
            "source": hit.payload.get("source", "Unknown source"),
        }
        for hit in valid_candidates
    ]
    
    # STAGE 2: Deep Cross-Encoder Reranking
    scores = list(reranker.rerank(query, candidate_texts))
    
    # Sort candidates by their reranker score in descending order
    scored_candidates = sorted(
        zip(scores, candidate_texts, candidate_metadata),
        key=lambda item: item[0],
        reverse=True,
    )
    
    # Extract the absolute best 3 chunks
    top_3 = scored_candidates[:3]
    return top_3

def ask_gemini(query: str, context_chunks):
    """
    Passes the strict top-3 context chunks to the Gemini API using the modern SDK.
    """
    context_string = "\n\n".join(
        [
            f"[Source: {chunk[2]['source']} | Timestamp: {chunk[2]['start']}s] {chunk[1]}"
            for chunk in context_chunks
        ]
    )
    
    system_prompt = (
        "You are a municipal policy analyst. Answer the user's question "
        "based ONLY on the provided meeting transcripts. If the answer is not "
        "in the transcripts, state that you do not know. Always cite the timestamp."
    ) 
    
    # Initialize the modern GenAI client
    if gemini_client is None:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    
    # Generate content using the proper new syntax
    response = gemini_client.models.generate_content(
        model=LLM_MODEL,
        contents=f"Context:\n{context_string}\n\nQuestion: {query}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        )
    )
    
    return response.text