import google.generativeai as genai
from fastembed.rerank.cross_encoder import TextCrossEncoder
from config import RERANKER_MODEL, LLM_MODEL
from index import get_qdrant_client, COLLECTION_NAME

# Load the reranker (runs locally, very accurate)
reranker = TextCrossEncoder(model_name=RERANKER_MODEL) #

def retrieve_and_rerank(query: str):
    """
    Executes a 2-stage retrieval: Fast hybrid search followed by deep cross-encoder reranking.
    """
    client = get_qdrant_client()
    
    # STAGE 1: Fast Hybrid Search (gets top 20 candidates)
    candidates = client.query(
        collection_name=COLLECTION_NAME,
        query_text=query,
        limit=20
    ) #
    
    candidate_texts = [hit.document for hit in candidates] #
    candidate_metadata = [hit.metadata for hit in candidates]
    
    # STAGE 2: Deep Cross-Encoder Reranking
    scores = list(reranker.rerank(query, candidate_texts))
    
    # Sort candidates by their reranker score in descending order
    scored_candidates = sorted(zip(scores, candidate_texts, candidate_metadata), reverse=True)
    
    # Extract the absolute best 3 chunks
    top_3 = scored_candidates[:3]
    return top_3

def ask_gemini(query: str, context_chunks):
    """
    Passes the strict top-3 context chunks to the Gemini API.
    """
    context_string = "\n\n".join(
        [f"[Timestamp: {chunk[2]['start']}s] {chunk[1]}" for chunk in context_chunks]
    )
    
    system_prompt = (
        "You are a municipal policy analyst. Answer the user's question "
        "based ONLY on the provided meeting transcripts. If the answer is not "
        "in the transcripts, state that you do not know. Always cite the timestamp."
    ) #[cite: 1]
    
    model = genai.GenerativeModel(
        model_name=LLM_MODEL,
        system_instruction=system_prompt
    )
    
    response = model.generate_content(f"Context:\n{context_string}\n\nQuestion: {query}")
    return response.text