import os
import shutil
from core.vector_store import VectorStore

def reset_environment():
    print("Resetting Environment...")
    
    # 1. Clear Uploads
    upload_dir = "uploads"
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            path = os.path.join(upload_dir, f)
            try:
                if os.path.isfile(path): os.remove(path)
                elif os.path.isdir(path): shutil.rmtree(path)
            except Exception as e:
                print(f"Error deleting {path}: {e}")
        print("Uploads directory cleared.")
        
    # 2. Clear Static Images
    static_images = "static/images"
    if os.path.exists(static_images):
        for f in os.listdir(static_images):
            path = os.path.join(static_images, f)
            try:
                if os.path.isfile(path): os.remove(path)
            except Exception as e:
                 print(f"Error deleting {path}: {e}")
        print("Static images cleared.")

    # 3. Clear Metadata and Sessions
    files_to_delete = ["conversations.json", "sessions.json", "backend/conversations.json"]
    dirs_to_delete = ["conversation_db", "chroma_db"]
    
    for f in files_to_delete:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"Deleted {f}")
            except Exception as e:
                print(f"Error deleteing {f}: {e}")

    for d in dirs_to_delete:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"Deleted directory {d}")
            except Exception as e:
                 print(f"Error deleting {d}: {e}")

    # 4. Reset Vector DB (via method if available, though folder delete handles it mostly)
    try:
        vs = VectorStore()
        if hasattr(vs, 'reset_database'):
            vs.reset_database()
        print("Vector Database reset via API.")
    except Exception as e:
        print(f"Error resetting DB via API (might be expected if folder gone): {e}")

if __name__ == "__main__":
    reset_environment()
