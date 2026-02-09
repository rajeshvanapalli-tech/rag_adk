import os
import shutil
import uuid
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google.adk.runners import Runner
from core.persistent_session_service import PersistentSessionService
from google.adk.sessions import Session
import google.generativeai as genai

from core.loader import load_file, load_file_with_structure
from core.chunker import chunk_text
from core.advanced_chunker import StructureAwareChunker, TaskBasedChunker, ProceduralChunker, DynamicChunker
from core.vector_store import VectorStore
from core.session_manager import SessionManager
from agents.master_agent import master_agent
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="RITE AI Unified Platform")

load_dotenv(override=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Components
vector_store = VectorStore()
session_service = PersistentSessionService(storage_path="sessions.json")
session_manager = SessionManager()

# Initialize Unified Mastery Runner
rite_runner = Runner(
    app_name="rite_unified",
    agent=master_agent,
    session_service=session_service,
    auto_create_session=True
)

UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
IMAGES_DIR = os.path.join(STATIC_DIR, "images")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ChatRequest(BaseModel):
    query: str
    user_id: str = "user_1"
    conversation_id: str = None

@app.get("/")
async def root():
    return {"message": "RITE AI Backend is online", "mode": "Unified"}

@app.get("/test_llm")
async def test_llm():
    try:
        from core.llm import get_llm
        llm = get_llm()
        response = llm.generate_content("Hello, can you hear me?")
        # Handle the fact that OpenAILLM might not have .model.model_name in the same way
        model_name = getattr(llm, 'model_name', 'unknown')
        return {"status": "success", "response": response, "model": model_name}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/upload")
async def upload_document(
    files: list[UploadFile] = File(...), 
    category: str = Form(..., pattern="^(hr|product)$")
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    
    # Initialize intelligent chunker (auto-detects HR vs Product)
    dynamic_chunker = DynamicChunker()
    
    for file in files:
        try:
            file_id = str(uuid.uuid4())
            filename = f"{file_id}_{file.filename}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Load text with structure if possible
            if filename.lower().endswith(('.doc', '.docx')):
                text_content = load_file_with_structure(filepath, output_image_dir=IMAGES_DIR)
            else:
                text_content = load_file(filepath)
            
            # Dynamic chunking - auto-detects document type
            chunks = dynamic_chunker.chunk(text_content)
            
            if not chunks:
                # Ultimate fallback
                chunks = chunk_text(text_content)
            
            if not chunks:
                 results.append({"filename": file.filename, "status": "failed", "error": "No text content found or chunking failed."})
                 continue

            vector_store.add_documents(
                documents=chunks, 
                metadatas=[{"source": filename, "category": category} for _ in chunks], 
                ids=[f"{file_id}_{i}" for i in range(len(chunks))]
            )
            
            results.append({"filename": file.filename, "status": "success", "chunks": len(chunks)})
        except Exception as e:
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})
    
    return {"files": results}

class SimplePart:
    def __init__(self, text):
        self.text = text

class SimpleContent:
    def __init__(self, role, parts):
        self.role = role
        self.parts = parts

@app.post("/chat")
async def chat_unified(request: ChatRequest):
    try:
        user_id = request.user_id
        query = request.query
        conversation_id = request.conversation_id
        
        if not conversation_id or conversation_id == "new":
            title = query[:50] + "..." if len(query) > 50 else query
            conversation = session_manager.create_conversation(user_id, title)
            conversation_id = conversation["id"]
        else:
            conversation = session_manager.get_conversation(conversation_id)
            if not conversation:
                conversation = session_manager.create_conversation(user_id, query[:50])
                conversation_id = conversation["id"]

        session_manager.update_timestamp(conversation_id)
        full_response = ""
        try:
            vector_store.add_chat_history(user_id, "user", query, time.time(), conversation_id)
            
            # Using conversation_id string as session_id for the runner
            # WRAP new_message in Object, do NOT use dict
            new_msg_obj = SimpleContent(role='user', parts=[SimplePart(text=query)])
            
            provider = os.getenv("MODEL_PROVIDER", "google").lower()
            
            if provider == "openai":
                # Direct call to OpenAIAgent
                async for event in master_agent.run_async(
                    user_id=user_id,
                    session_id=conversation_id,
                    new_message=new_msg_obj
                ):
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                full_response += part.text
            else:
                # Use ADK Runner for Gemini
                async for event in rite_runner.run_async(
                    user_id=user_id,
                    session_id=conversation_id,
                    new_message=new_msg_obj
                ):
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                full_response += part.text
        except Exception as ai_err:
            print(f"CHAT/AI ERROR: {ai_err}")
            full_response = f"Agent Error: {str(ai_err)}"

        if not full_response:
             full_response = "I processed your request but couldn't generate a specific response."

        vector_store.add_chat_history(user_id, "assistant", full_response, time.time(), conversation_id)

        return {
            "response": full_response,
            "agent": "RITE Intelligence",
            "conversation_id": conversation_id,
            "title": conversation["title"]
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"System Error: {str(e)}")

@app.get("/conversations")
async def list_conversations(user_id: str = "user_1"):
    return {"conversations": session_manager.get_user_conversations(user_id)}

@app.get("/conversations/{conversation_id}")
async def get_conversation_details(conversation_id: str):
    conv = session_manager.get_conversation(conversation_id)
    if not conv:
         raise HTTPException(status_code=404, detail="Conversation not found")
    messages = vector_store.get_conversation_history(conversation_id)
    return {"conversation": conv, "messages": messages}

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    session_manager.delete_conversation(conversation_id)
    vector_store.delete_conversation_history(conversation_id)
    await session_service.clear_session("user_1", conversation_id)
    return {"message": "Deleted"}

@app.get("/history")
async def get_history(user_id: str = "user_1", query: str = ""):
    if not query: return {"history": []} 
    return {"history": vector_store.search_chat_history(user_id, query, n_results=10)}

@app.get("/files")
async def list_files():
    """Lists all uploaded files."""
    try:
        files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                filepath = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    # We store files with uuid prefix: uuid_filename.ext
                    # Try to separate them for clearer display
                    parts = filename.split('_', 1)
                    display_name = parts[1] if len(parts) > 1 else filename
                    files.append({
                        "id": filename,
                        "name": display_name,
                        "size": os.path.getsize(filepath),
                        "timestamp": os.path.getmtime(filepath)
                    })
        return {"files": sorted(files, key=lambda x: x['timestamp'], reverse=True)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """Deletes a specific uploaded file and its vector store entries."""
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        # 1. Delete from Vector Store
        vector_store.delete_documents_by_source(filename)
        
        # 2. Delete from Disk
        os.remove(filepath)
        
        return {"message": f"Successfully deleted {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files")
async def clear_all_files():
    """Deletes all uploaded files and clears the RAG vector store."""
    try:
        # 1. Clear Vector Store
        vector_store.clear_all_documents()
        
        # 2. Delete files from disk
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                filepath = os.path.join(UPLOAD_DIR, filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")
        
        # 3. Also clear images if any
        if os.path.exists(IMAGES_DIR):
            for filename in os.listdir(IMAGES_DIR):
                 filepath = os.path.join(IMAGES_DIR, filename)
                 try:
                     if os.path.isfile(filepath):
                         os.remove(filepath)
                 except Exception as e:
                    print(f"Error deleting image {filename}: {e}")

        return {"message": "All files and vector store cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
 
 