# Server Restart Guide - Step by Step

## 🔴 How to Kill All Servers and Restart

### **Method 1: Kill All Servers (Quick & Clean)**

Open **PowerShell** in the project directory and run these commands:

```powershell
# Step 1: Kill all Python processes (Backend)
taskkill /F /IM python.exe

# Step 2: Kill all Node.js processes (Frontend)
taskkill /F /IM node.exe
```

**Result:** All servers stopped. ✅

---

### **Method 2: Graceful Stop (If servers are in terminals)**

**In Backend Terminal:**
```
Press Ctrl+C
```

**In Frontend Terminal:**
```
Press Ctrl+C
```

---

## 🟢 How to Restart Servers

### **Step 1: Start Backend**

**In PowerShell (in project root):**

```powershell
# Navigate to backend directory
cd backend

# Start backend server
python main.py
```

**Wait for this message:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**✅ Backend is running!**

---

### **Step 2: Start Frontend (In a NEW Terminal)**

**Open a NEW PowerShell window:**

```powershell
# Navigate to project root
cd C:\Users\VanapalliRajesh\OneDrive - RITE\rag_adk

# Navigate to frontend directory
cd frontend

# Start frontend dev server
npm run dev
```

**Wait for this message:**
```
  ➜  Local:   http://localhost:5173/
```

**✅ Frontend is running!**

---

## 📋 Complete Restart Flow (Copy-Paste Ready)

### **Terminal 1 (Backend):**

```powershell
# Kill all servers first
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Wait 2 seconds
Start-Sleep -Seconds 2

# Navigate to backend
cd C:\Users\VanapalliRajesh\OneDrive - RITE\rag_adk\backend

# Start backend
python main.py
```

### **Terminal 2 (Frontend) - Run AFTER backend starts:**

```powershell
# Navigate to frontend
cd C:\Users\VanapalliRajesh\OneDrive - RITE\rag_adk\frontend

# Start frontend
npm run dev
```

---

## 🧹 Clean Restart (With Database Reset)

If you want to **completely reset everything**:

### **Terminal 1 (Backend):**

```powershell
# Kill all servers
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Navigate to backend
cd C:\Users\VanapalliRajesh\OneDrive - RITE\rag_adk\backend

# Delete database (optional - only if having issues)
Remove-Item -Path "chroma_data" -Recurse -Force

# Start backend (will re-index documents)
python main.py
```

### **Terminal 2 (Frontend):**

```powershell
# Navigate to frontend
cd C:\Users\VanapalliRajesh\OneDrive - RITE\rag_adk\frontend

# Start frontend
npm run dev
```

---

## ✅ Verification Checklist

After restarting, verify everything is working:

### **1. Check Backend:**
- Open: http://127.0.0.1:8000/
- Should see: `{"message":"RITE AI Backend is online","mode":"Unified"}`

### **2. Check Frontend:**
- Open: http://localhost:5173
- Should see: Your chat interface

### **3. Test End-to-End:**
- Ask a question in the chat
- Should get a streaming response
- Links should be clickable

---

## ⚡ Quick Commands Reference

| Action | Command |
|--------|---------|
| Kill all Python (Backend) | `taskkill /F /IM python.exe` |
| Kill all Node (Frontend) | `taskkill /F /IM node.exe` |
| Kill both servers | `taskkill /F /IM python.exe; taskkill /F /IM node.exe` |
| Start Backend | `cd backend` then `python main.py` |
| Start Frontend | `cd frontend` then `npm run dev` |
| Clear Database | `Remove-Item -Path "chroma_data" -Recurse -Force` |
| Stop gracefully | Press `Ctrl+C` in terminal |

---

## 🔧 Troubleshooting

### **Issue: "Port already in use"**
```powershell
# Kill all Python processes
taskkill /F /IM python.exe

# Wait a moment
Start-Sleep -Seconds 2

# Try starting again
python main.py
```

### **Issue: "Database corrupted"**
```powershell
# Navigate to backend
cd backend

# Delete database
Remove-Item -Path "chroma_data" -Recurse -Force

# Restart backend (will rebuild database)
python main.py
```

### **Issue: "Frontend can't connect to backend"**
**Check:**
1. Backend is running: http://127.0.0.1:8000/
2. Frontend `.env` has: `VITE_API_URL=http://127.0.0.1:8000`
3. Refresh frontend page

---

## 📝 One-Command Full Restart

**Single Command (Backend + Frontend in same terminal):**

```powershell
# Kill all
taskkill /F /IM python.exe; taskkill /F /IM node.exe; Start-Sleep -Seconds 2; cd backend; Start-Process powershell -ArgumentList "python main.py"; Start-Sleep -Seconds 10; cd ..\frontend; npm run dev
```

⚠️ **Note:** This is complex. Better to use separate terminals for clarity.

---

## 🎯 Recommended Workflow

**Always use 2 separate PowerShell windows:**

**Window 1:** Backend only
```powershell
cd backend
python main.py
```

**Window 2:** Frontend only
```powershell
cd frontend
npm run dev
```

This makes it easy to:
- See backend logs separately
- See frontend logs separately
- Restart one without affecting the other
- Use `Ctrl+C` to stop gracefully

---

**That's it! You're all set!** 🎉
