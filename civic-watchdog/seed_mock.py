# seed_mock.py
from index import index_documents

mock_chunks = [
    {
        "text": "Councilmember Adams opened discussion on Ordinance 45B regarding commercial zoning updates.",
        "start_time": 120.0
    },
    {
        "text": "The public hearing for Ordinance 45B concluded with strong support from local business owners.",
        "start_time": 340.0
    },
    {
        "text": "Mayor Miller called for a vote on Ordinance 45B. The council passed Ordinance 45B unanimously.",
        "start_time": 1250.0
    },
    {
        "text": "The council moved to the next agenda item: allocating $2M for downtown stormwater infrastructure.",
        "start_time": 1400.0
    }
]

if __name__ == "__main__":
    print("Indexing mock council data...")
    index_documents(mock_chunks)
    print("Mock data loaded into Qdrant successfully!")