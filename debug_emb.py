
import chromadb
import sys
import os
import numpy as np
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv("backend/.env")

sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from core.llm import get_llm
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def debug_embeddings():
    print("Checking Embeddings...")
    llm = get_llm()
    print(f"LLM Loaded: {type(llm)}")
    
    # Generate two different embeddings
    text1 = "What is ConvertRite?"
    text2 = "How to configure Oracle Cloud?"
    
    emb1 = llm.get_embedding(text1, task_type="retrieval_query")
    emb2 = llm.get_embedding(text2, task_type="retrieval_query")
    
    print(f"Embedding 1 (first 5): {emb1[:5]}")
    print(f"Embedding 2 (first 5): {emb2[:5]}")
    
    # Calculate distance
    vec1 = np.array(emb1)
    vec2 = np.array(emb2)
    dist = np.linalg.norm(vec1 - vec2)
    print(f"Euclidean Distance between different texts: {dist}")
    
    if dist < 0.001:
        print("CRITICAL: Embeddings are identical! Model is failing to differentiate text.")
    else:
        print("Embeddings look distinct.")

    # Inspect Chroma Content
    client = chromadb.PersistentClient(path="./backend/chroma_data")
    try:
        col = client.get_collection("rag_docs_google")
        print(f"\nCollection rag_docs_google has {col.count()} docs.")
        
        # Peek one with embeddings explicitly included
        res = col.get(limit=1, include=["embeddings", "documents", "metadatas"])
        
        if res['embeddings'] is not None and len(res['embeddings']) > 0:
            stored_emb = res['embeddings'][0]
            print(f"Stored Embedding (first 5): {stored_emb[:5]}")
            
            # Distance from query
            # stored_emb might be list or array
            dist_q = np.linalg.norm(vec1 - np.array(stored_emb))
            print(f"Distance between Query and Stored Doc 1: {dist_q}")
            
        # Search
            
        # Search
        print("\nSearching for 'ConvertRite overview'...")
        qm = llm.get_embedding("ConvertRite overview", task_type="retrieval_query")
        results = col.query(query_embeddings=[qm], n_results=3)
        
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            d = results['distances'][0][i] if results['distances'] else "?"
            print(f"\n[Hit {i+1}] Dist: {d}")
            print(f"Meta: {meta}")
            print(f"Text: {doc[:100]}...")

    except Exception as e:
        print(f"Chroma inspection failed: {e}")

if __name__ == "__main__":
    debug_embeddings()
