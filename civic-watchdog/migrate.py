import os
from index import get_qdrant_client, COLLECTION_NAME

def migrate_legacy_data():
    print("Starting migration...")
    client = get_qdrant_client()
    
    if not client.collection_exists(COLLECTION_NAME):
        print("Collection doesn't exist. Nothing to migrate.")
        return
        
    # Scroll and update points without a session_id
    offset = None
    migrated_count = 0
    
    while True:
        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        points_to_update = []
        for point in points:
            if "session_id" not in point.payload or point.payload["session_id"] is None:
                point.payload["session_id"] = "legacy"
                points_to_update.append(point)
                
        if points_to_update:
            client.set_payload(
                collection_name=COLLECTION_NAME,
                payload={"session_id": "legacy"},
                points=[p.id for p in points_to_update]
            )
            migrated_count += len(points_to_update)
            
        offset = next_offset
        if offset is None:
            break
            
    print(f"Migration complete. Updated {migrated_count} points to have session_id='legacy'.")

if __name__ == "__main__":
    migrate_legacy_data()
