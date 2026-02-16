
import os
import shutil
import uuid
from core.vector_store import VectorStore
from core.loader import load_file_with_structure, load_file
from core.advanced_chunker import DynamicChunker
from core.chunker import chunk_text

UPLOAD_DIR = "uploads"
IMAGE_DIR = os.path.join("static", "images")
CHROMA_DIR = "chroma_data"

def upgrade_embeddings():
    print("Beginning Embedding Model Upgrade to text-embedding-004 (768 dims)...")
    
    # 1. Clear Vector DB
    if os.path.exists(CHROMA_DIR):
        print(f"Removing old vector database at {CHROMA_DIR}...")
        try:
            shutil.rmtree(CHROMA_DIR)
            print("Database cleared.")
        except Exception as e:
            print(f"Error removing Chroma directory: {e}")
            return # Stop if we can't clear, otherwise we corrupt DB
    else:
        print("No existing database found.")

    # 2. Re-initialize Vector Store (will recreate empty DB with new dims)
    print("Initializing new Vector Store...")
    vs = VectorStore()
    chunker = DynamicChunker()
    
    # 3. Process Uploads
    if not os.path.exists(UPLOAD_DIR):
        print("No uploads directory found. Nothing to re-index.")
        return

    files = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
    print(f"Found {len(files)} files to re-index.")
    
    for filename in files:
        filepath = os.path.join(UPLOAD_DIR, filename)
        print(f"Processing: {filename}...")
        
        try:
            # Deterministic ID prefix
            file_id_prefix = filename.split('_')[0]
            
            # Load Content
            if filename.lower().endswith(('.doc', '.docx')):
                content = load_file_with_structure(filepath, output_image_dir=IMAGE_DIR)
            else:
                content = load_file(filepath)
            
            # Chunk
            chunks = chunker.chunk(content)
            if not chunks:
                chunks = chunk_text(content)
                
            if not chunks:
                print(f"Skipping {filename}: No text extracted.")
                continue
                
            print(f" - Generated {len(chunks)} chunks.")
            
            # Determine Category
            category = "product" if "manual" in filename.lower() or "guide" in filename.lower() else "hr"
            
            # Index
            vs.add_documents(
                documents=chunks,
                metadatas=[{"source": filename, "category": category} for _ in chunks],
                ids=[f"{file_id_prefix}_{i}_{uuid.uuid4().hex[:6]}" for i in range(len(chunks))]
            )
            print(" - Indexed successfully.")
            
        except Exception as e:
            print(f"Failed to index {filename}: {e}")

    print("\nUpgrade Complete! Database is now using text-embedding-004.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    upgrade_embeddings()
