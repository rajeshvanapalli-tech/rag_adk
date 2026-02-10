# Backend Server Startup Guide

## 🚀 How to Run Backend Server

### **Method 1: Using Python (Recommended)**

```powershell
# Navigate to backend directory
cd backend

# Start the server
python main.py
```

**Benefits:**
- ✅ Simple and reliable
- ✅ Auto-syncs documents on startup
- ✅ Runs on port 8000 by default
- ✅ Easy to stop (Ctrl+C)

---

### **Method 2: Using Uvicorn (Advanced)**

```powershell
# Navigate to backend directory
cd backend

# Start with auto-reload
uvicorn main:app --port 8000 --reload

# OR for production (no auto-reload)
uvicorn main:app --port 8000
```

**Benefits:**
- ✅ Auto-reloads on code changes (with --reload flag)
- ⚠️ May have issues with database initialization

---

## 🏥 Health Check Endpoints

Your backend already has health monitoring built-in!

### **1. Root Endpoint (Basic Health)**
```bash
GET http://127.0.0.1:8000/
```

**Response:**
```json
{
  "message": "RITE AI Backend is online",
  "mode": "Unified"
}
```

---

### **2. LLM Test Endpoint**
```bash
GET http://127.0.0.1:8000/test_llm
```

**Response:**
```json
{
  "status": "success",
  "response": "Hello from RITE AI Router!",
  "model": "gemini-flash-lite-latest"
}
```

This tells you:
- ✅ Backend is running
- ✅ LLM is connected
- ✅ Which model is active

---

### **3. Test in Browser**

Simply open in your browser:
```
http://127.0.0.1:8000/
```

You should see:
```json
{"message":"RITE AI Backend is online","mode":"Unified"}
```

---

### **4. Test with PowerShell**

```powershell
# Test root endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method GET

# Test LLM endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:8000/test_llm" -Method GET
```

---

## 📊 Startup Checklist

When you run `python main.py`, you should see:

```
✅ INFO:     Started server process [xxxxx]
✅ INFO:     Waiting for application startup.
✅ Starting Smart Sync for google...  ← Your LLM provider
✅ Knowledge Base is already up-to-date.  ← Documents indexed
✅ INFO:     Application startup complete.
✅ INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## ⚠️ Common Issues & Solutions

### **Issue 1: Error 429 - Rate Limit Exceeded**

**What you saw:**
```
429, 'message': 'You exceeded your quota'
```

**Solution:**
- Your Gemini API has rate limits
- Wait a few minutes
- Or switch to OpenAI (see LLM_SWITCHING_GUIDE.md)

---

### **Issue 2: Port Already in Use**

**Error:**
```
Address already in use
```

**Solution:**
```powershell
# Kill all Python processes
taskkill /F /IM python.exe

# Then restart
python main.py
```

---

### **Issue 3: ChromaDB Corrupted**

**Symptoms:**
- Server crashes immediately
- "panic" errors

**Solution:**
```powershell
# Stop server
Ctrl+C

# Delete database
Remove-Item -Path "chroma_data" -Recurse -Force

# Restart server (will re-index)
python main.py
```

---

## 🔄 Complete Startup Flow

### **Full Clean Start:**

```powershell
# 1. Kill all servers
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# 2. Navigate to backend
cd backend

# 3. (Optional) Clear database for fresh start
Remove-Item -Path "chroma_data" -Recurse -Force

# 4. Start backend
python main.py

# Wait for: "Application startup complete"

# 5. In NEW terminal, navigate to frontend
cd frontend

# 6. Start frontend
npm run dev
```

---

## ✅ Verify Everything is Working

1. **Backend Health:**
   - Open: http://127.0.0.1:8000/
   - Should see: `{"message":"RITE AI Backend is online","mode":"Unified"}`

2. **LLM Health:**
   - Open: http://127.0.0.1:8000/test_llm
   - Should see: `{"status":"success","response":"...","model":"..."}`

3. **Frontend:**
   - Open: http://localhost:5173
   - Should see your chat interface

4. **End-to-End Test:**
   - Ask a question in the chat
   - Should get streaming response
   - Links should be clickable

---

## 🎯 Production-Ready Command

For production (no auto-reload, more stable):

```powershell
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

**Note:** Use `--workers 1` to avoid ChromaDB conflicts.

---

## 📝 Quick Reference

| Command | Purpose |
|---------|---------|
| `python main.py` | Start backend (recommended) |
| `uvicorn main:app --port 8000 --reload` | Start backend with auto-reload |
| `Ctrl+C` | Stop server gracefully |
| `taskkill /F /IM python.exe` | Force kill all Python processes |
| `http://127.0.0.1:8000/` | Health check |
| `http://127.0.0.1:8000/test_llm` | LLM test |

---

## 🚨 Current Issue (429 Error)

You just encountered a **Gemini API rate limit**. This means:
- ❌ Too many requests to Gemini API
- ⏳ Need to wait ~1 minute
- 🔄 Or switch to OpenAI

**Wait 1 minute, then your backend should work fine!**
