import argparse
import sys
from transcribe import transcribe_meeting
from chunk import create_overlapping_chunks
from index import index_documents
from answer import retrieve_and_rerank, ask_gemini
from evaluate import run_evaluation

def main():
    parser = argparse.ArgumentParser(description="Civic Watchdog: Hybrid RAG Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: Ingest a video/audio file
    ingest_parser = subparsers.add_parser("ingest", help="Transcribe and index a municipal meeting file")
    ingest_parser.add_argument("filepath", type=str, help="Path to the video/audio file")

    # Command: Ask a question
    ask_parser = subparsers.add_parser("ask", help="Ask a question against the indexed transcripts")
    ask_parser.add_argument("query", type=str, help="Your question (e.g., 'What was the decision on Ordinance 45B?')")

    # Command: Evaluate the pipeline
    subparsers.add_parser("evaluate", help="Run the evaluation script to calculate retrieval accuracy")

    args = parser.parse_args()

    if args.command == "ingest":
        print(f"--- Starting Ingestion Pipeline for {args.filepath} ---")
        segments = transcribe_meeting(args.filepath)
        chunks = create_overlapping_chunks(segments)
        index_documents(chunks)
        print("--- Ingestion Complete! ---")

    elif args.command == "ask":
        print(f"Query: {args.query}\nSearching database...")
        # Retrieve the mathematically optimized chunks using the 2-stage reranker
        best_chunks = retrieve_and_rerank(args.query) 
        
        print("Generating answer via Gemini...")
        # Pass the strict top-3 context chunks to the LLM
        answer = ask_gemini(args.query, best_chunks)
        
        print("\n--- Final Answer ---")
        print(answer)

    elif args.command == "evaluate":
        print("--- Running Evaluation Suite ---")
        run_evaluation()

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()