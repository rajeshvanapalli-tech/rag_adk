
import chromadb
import sys
import os
from dotenv import load_dotenv

# Load env from root
load_dotenv(".env")
# Also try backend .env
load_dotenv("backend/.env")

# Adjust path to import backend modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from core.llm import get_llm
    from core.vector_store import UniversalEmbeddingFunction
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def debug_rag():
    print("Initializing Chroma Client...")
    try:
        client = chromadb.PersistentClient(path="./backend/chroma_data")
        
        # Check collections
        collections = client.list_collections()
        for col in collections:
            print(f"Collection: {col.name}, Count: {col.count()}")
            
        # target_collection
        col_name = "rag_docs_google" # or openai, need to check
        # Let's check both
        target_col = None
        for name in ["rag_docs_google", "rag_docs_openai"]:
            try:
                c = client.get_collection(name)
                if c.count() > 0:
                    target_col = c
                    col_name = name
                    break
            except:
                pass
        
        if not target_col:
            print("No populated RAG collection found!")
            return

        print(f"Targeting Collection: {col_name} with {target_col.count()} docs")
        
        # Inspect first doc
        data = target_col.peek(1)
        print(f"Sample Metadata: {data['metadatas'][0]}")
        
        # Try Query
        query = "tell about convertrite"
        print(f"\nTesting Query: '{query}'")
        
        # Setup embedding function
        llm = get_llm()
        
        provider = "unknown"
        if hasattr(llm, 'provider'):
            provider = llm.provider
        elif hasattr(llm, 'primary') and hasattr(llm.primary, 'provider'): 
            provider = llm.primary.provider
            
        print(f"LLM Provider: {provider}")
        
        # Instantiate embedding function 
        # UniversalEmbeddingFunction handles batching internally using llm.get_embedding
        class Wrapper:
            def __init__(self, llm): self.llm = llm
            def __call__(self, input): return self.llm.get_embedding(input, task_type="retrieval_query")
            
        embed_fn = Wrapper(llm)
        
        # Get query embedding
        q_emb = embed_fn([query])
        
        # Query
        results = target_col.query(
            query_embeddings=q_emb,
            n_results=3,
            # include=["documents", "metadatas", "distances"]
        )
        
        print("\n--- Search Results ---")
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            dist = results['distances'][0][i] if 'distances' in results else "N/A"
            print(f"\nResult {i+1} (Dist: {dist}):")
            print(f"Metadata: {meta}")
            print(f"Snippet: {doc[:150]}...")
            
    except Exception as e:
        print(f"Debug Panic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rag()
