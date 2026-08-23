from answer import retrieve_and_rerank

# A simple test dataset of questions where you already know the timestamp of the answer
EVAL_DATASET = [
    {"query": "What was the final decision on Ordinance 45B?", "expected_time": 1250},
    {"query": "Who proposed the new zoning laws?", "expected_time": 340},
    # Add up to 10-20 questions here for a robust evaluation
]

def run_evaluation():
    """
    Tests the RAG pipeline against a dataset of known queries and timestamps.
    Proves retrieval accuracy for your resume.
    """
    passes = 0
    total = len(EVAL_DATASET)
    
    print(f"Running evaluation on {total} questions...")
    
    for item in EVAL_DATASET:
        query = item["query"]
        expected_time = item["expected_time"]
        
        top_chunks = retrieve_and_rerank(query)
        
        # Check if the expected timestamp is within the retrieved chunks (60s margin)
        passed = False
        for _, _, meta in top_chunks:
            retrieved_time = meta["start"]
            if abs(retrieved_time - expected_time) <= 60: #[cite: 1]
                passed = True
                break
                
        if passed:
            passes += 1
            print(f"✅ Pass: {query}")
        else:
            print(f"❌ Fail: {query}")
            
    accuracy = (passes / total) * 100
    print(f"\nFinal Retrieval Accuracy: {accuracy:.1f}%")
    return accuracy

if __name__ == "__main__":
    run_evaluation()