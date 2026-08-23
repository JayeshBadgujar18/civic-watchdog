

# reset_db.py
from index import get_qdrant_client
from seed_mock import mock_chunks, index_documents
from config import COLLECTION_NAME

def reset_and_seed():
    client = get_qdrant_client()
    
    print("Wiping duplicate data from cloud cluster...")
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        
    print("Re-indexing clean mock data...")
    index_documents(mock_chunks)
    print("Database reset successfully!")

if __name__ == "__main__":
    reset_and_seed()