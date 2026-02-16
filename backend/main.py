import os
import shutil
import uuid
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from core.persistent_session_service import PersistentSessionService
from google.adk.sessions import Session
from google.genai import types

from core.loader import load_file, load_file_with_structure
from core.chunker import chunk_text
from core.advanced_chunker import StructureAwareChunker, TaskBasedChunker, ProceduralChunker, DynamicChunker
from core.image_processor import image_processor
from core.vector_store import VectorStore
from core.session_manager import SessionManager
from agents.master_agent import master_agent
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    import asyncio
    asyncio.create_task(sync_vector_store())
    yield
    # Shutdown logic (if any)
    pass

app = FastAPI(title="RITE AI Unified Platform", lifespan=lifespan)

load_dotenv(override=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Single Active Agent (Master Agent)
print("[Main] Importing MasterAgent...")
from agents.master_agent import master_agent
agent = master_agent

# Reuse VectorStore from Agent to avoid double initialization
print("[Main] Linking VectorStore...")
vector_store = agent.vector_store

print("[Main] Initializing PersistentSessionService...")
session_service = PersistentSessionService(storage_path="sessions.json")
session_manager = SessionManager()
print("[Main] Components Initialized.")

# Initialize Unified Mastery Runner
# Set app_name to 'agents' to match the directory structure and avoid ADK mismatch
rite_runner = Runner(
    app_name="agents",
    agent=agent,
    session_service=session_service,
    auto_create_session=True
)

UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
IMAGES_DIR = os.path.join(STATIC_DIR, "images")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

async def sync_vector_store():
    """Background task to sync disk files with current LLM index."""
    # Simplified sync task
    pass

class ChatRequest(BaseModel):
    query: str
    image: str | None = None
    mime_type: str | None = None
    user_id: str = "user_1"
    conversation_id: str = None

@app.get("/")
async def root():
    return {"message": "RITE AI Backend is online", "mode": "Unified"}

@app.get("/test_llm")
async def test_llm():
    try:
        from core.llm import get_llm
        llm = get_llm(provider="openai") 
        response = llm.generate_content("Hello from RITE AI Router!")
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
    
    # Initialize intelligent chunker
    dynamic_chunker = DynamicChunker()
    
    import re
    image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')

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
                
                # PROCESS IMAGES: Detect, Describe, Replace
                # Find all markdown images: ![description](path)
                matches = image_pattern.findall(text_content)
                
                if matches and (category == 'product' or 'step' in text_content.lower()):
                    import asyncio
                    print(f"Found {len(matches)} images in {filename}. Generating descriptions concurrently...")
                    
                    tasks = []
                    valid_matches = []
                    
                    # Prepare tasks
                    for alt_text, img_rel_path in matches:
                        # Resolve absolute path
                        if img_rel_path.startswith('/static/'):
                            clean_path = img_rel_path.replace('/static/', '', 1) 
                            full_img_path = os.path.join(STATIC_DIR, clean_path)
                        else:
                            full_img_path = img_rel_path
                        
                        if os.path.exists(full_img_path):
                            tasks.append(image_processor.generate_description_async(full_img_path))
                            valid_matches.append((alt_text, img_rel_path))
                    
                    if tasks:
                        # Run all descriptions in parallel, return exceptions instead of failing
                        descriptions_or_errors = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        processed_descriptions = []
                        for result in descriptions_or_errors:
                            if isinstance(result, Exception):
                                print(f"Image processing error: {result}")
                                processed_descriptions.append("Image description unavailable due to error.")
                            else:
                                processed_descriptions.append(result)
                        
                        # Replace in content
                        for (alt_text, img_rel_path), description in zip(valid_matches, processed_descriptions):
                            original_md = f"![{alt_text}]({img_rel_path})"
                            new_md = f"![Image: {description}]({img_rel_path})"
                            text_content = text_content.replace(original_md, new_md)
                            
                    print(f"Processed {len(tasks)} images concurrently.")
                        
            else:
                text_content = load_file(filepath)
            
            # Dynamic chunking - Pass explicit category
            chunks = dynamic_chunker.chunk(text_content, category=category)
            
            if not chunks:
                # Ultimate fallback
                chunks = chunk_text(text_content)
            
            if not chunks:
                 results.append({"filename": file.filename, "status": "failed", "error": "No text content found or chunking failed."})
                 continue

            try:
                print(f"Indexing {len(chunks)} chunks for {file.filename} using {category} category...")
                # Add explicit category metadata for retrieval filtering
                metadatas = [{"source": filename, "category": category} for _ in chunks]
                
                vector_store.add_documents(
                    documents=chunks, 
                    metadatas=metadatas, 
                    ids=[f"{file_id}_{i}" for i in range(len(chunks))]
                )
                print(f"Successfully generated embeddings and indexed {file.filename}")
                
                # Verification
                count = vector_store.get_document_count()
                print(f"Total documents in Vector Store: {count}")
                
            except Exception as e:
                print(f"Index error for {file.filename}: {e}")
                results.append({"filename": file.filename, "status": "failed", "error": f"Indexing failed: {str(e)}"})
                continue
            
            results.append({"filename": file.filename, "status": "success", "chunks": len(chunks)})
        except Exception as e:
            import traceback
            traceback.print_exc()
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})
    
    return {"files": results}


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
            # Record in chat history (Optional, as ADK runner also manages it)
            vector_store.add_chat_history(user_id, "user", query, time.time(), conversation_id)
            
            # Using proper ADK Content/Part types
            new_msg_obj = types.Content(role='user', parts=[types.Part(text=query)])
            
            # CALL via REAL ADK Runner
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

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming endpoint for real-time chat responses."""
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate():
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
            
            # Send conversation metadata first
            yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': conversation_id, 'title': conversation['title']})}\n\n"
            
            # Record user message
            vector_store.add_chat_history(user_id, "user", query, time.time(), conversation_id)
            
            # Create proper ADK message object
            # Create proper ADK message object with optional image
            import base64
            parts = [types.Part(text=query)]
            
            if request.image and request.mime_type:
                try:
                    # Clean base64 string if it contains header (e.g. "data:image/png;base64,")
                    base64_data = request.image
                    if "," in base64_data:
                        base64_data = base64_data.split(",")[1]
                        
                    parts.append(types.Part(
                        inline_data=types.Blob(
                            mime_type=request.mime_type,
                            data=base64.b64decode(base64_data)
                        )
                    ))
                    print(f"[Chat] Added image attachment ({request.mime_type})")
                except Exception as img_err:
                    print(f"[Chat] Error processing image: {img_err}")

            new_msg_obj = types.Content(role='user', parts=parts)
            
            full_response = ""
            # CALL via REAL ADK Runner
            async for event in rite_runner.run_async(
                user_id=user_id,
                session_id=conversation_id,
                new_message=new_msg_obj
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            full_response += part.text
                            yield f"data: {json.dumps({'type': 'content', 'text': part.text})}\n\n"
            
            if not full_response:
                full_response = "I processed your request but couldn't generate a specific response."
                yield f"data: {json.dumps({'type': 'content', 'text': full_response})}\n\n"
            
            # Save to history
            vector_store.add_chat_history(user_id, "assistant", full_response, time.time(), conversation_id)
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"Error: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

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

