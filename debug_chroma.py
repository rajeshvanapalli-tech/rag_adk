
import chromadb
import sys
import os

# Adjust path to import backend modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def inspect_chroma():
    try:
        client = chromadb.PersistentClient(path="./backend/chroma_data")
        
        # List collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collections: {[c.name for c in collections]}")
        
        for col in collections:
            print(f"\n--- Inspecting Collection: {col.name} ---")
            count = col.count()
            print(f"Total Documents: {count}")
            
            if count > 0:
                # Peek at the data
                data = col.peek(limit=5)
                print("Sample Metadatas:")
                for meta in data['metadatas']:
                    print(meta)
                    
                print("\nSample Documents (First 100 chars):")
                for doc in data['documents']:
                    print(doc[:100].replace('\n', ' ') + "...")

    except Exception as e:
        print(f"Error inspecting Chroma: {e}")

if __name__ == "__main__":
    inspect_chroma()
