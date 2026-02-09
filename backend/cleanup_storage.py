import os
import shutil
import subprocess
from core.vector_store import VectorStore

def kill_word():
    print("Closing any open Excel or Word processes...")
    try:
        subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE", "/T"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "EXCEL.EXE", "/T"], capture_output=True)
    except:
        pass

def cleanup():
    # 0. Kill processes that might lock files
    kill_word()
    
    # 1. Clear Uploads
    upload_dir = "uploads"
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Bypassing locked file: {file_path}")

    # 2. Clear Static Images
    static_images = os.path.join("static", "images")
    if os.path.exists(static_images):
        for filename in os.listdir(static_images):
            file_path = os.path.join(static_images, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"Deleted image: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

    # 3. Reset Vector Database
    try:
        vs = VectorStore()
        vs.reset_database()
        print("Vector database reset successfully.")
    except Exception as e:
        print(f"Failed to reset vector database: {e}")

    # 4. Clear Metadata JSONs
    metadata_files = ["conversations.json", "sessions.json"]
    for file in metadata_files:
        if os.path.exists(file):
            try:
                with open(file, "w") as f:
                    if file == "conversations.json":
                        f.write("[]")
                    else:
                        f.write("{}")
                print(f"Reset: {file}")
            except Exception as e:
                print(f"Failed to reset {file}: {e}")

if __name__ == "__main__":
    cleanup()
