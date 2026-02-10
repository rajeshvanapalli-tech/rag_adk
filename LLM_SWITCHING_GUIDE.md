# LLM Auto-Switching Guide

## 🔄 How Auto-Switching Works

Your backend **automatically** detects which LLM to use based on the `.env` file:

**Priority Order:**
1. **OpenAI** (if valid key exists) 
2. **Gemini** (if valid key exists)
3. **No LLM** (fallback with error message)

---

## 🎯 How to Switch Between LLMs

### **Option 1: Use Google Gemini** ✅ (Current Setup)

In `backend/.env`:
```env
# Google Gemini - ACTIVE
GEMINI_API_KEY=AIzaSyASe_QwS3mZA24Hp3sdGXl6760vO6sNMYk
GEMINI_MODEL=gemini-flash-lite-latest

# OpenAI - DISABLED (commented out)
# OPENAI_API_KEY=sk-your-key-here
# OPENAI_MODEL=gpt-4o-mini
```

**Restart**: `Ctrl+C` then `python main.py`

---

### **Option 2: Switch to OpenAI**

In `backend/.env`:
```env
# Google Gemini - DISABLED (commented out)
# GEMINI_API_KEY=AIzaSyASe_QwS3mZA24Hp3sdGXl6760vO6sNMYk
# GEMINI_MODEL=gemini-flash-lite-latest

# OpenAI - ACTIVE
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

**Restart**: `Ctrl+C` then `python main.py`

---

### **Option 3: Use Both (OpenAI Takes Priority)**

In `backend/.env`:
```env
# Both enabled - OpenAI will be used (higher priority)
GEMINI_API_KEY=AIzaSyASe_QwS3mZA24Hp3sdGXl6760vO6sNMYk
GEMINI_MODEL=gemini-flash-lite-latest

OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

**Result**: OpenAI will be used because it has higher priority.

---

## 🔧 Important Notes

### **To "Disable" an LLM:**
- **Comment it out** with `#` at the start of the line
- **OR** delete the line entirely

### **After Changing .env:**
1. Go to backend terminal
2. Press `Ctrl+C` to stop the server
3. Run `python main.py` to start with new config

### **Check Which LLM is Active:**
Look for this in the startup logs:
```
Starting Smart Sync for google...   ← Using Gemini
Starting Smart Sync for openai...   ← Using OpenAI
```

---

## 📋 Quick Commands

### Start Backend:
```powershell
cd backend
python main.py
```

### Start Frontend:
```powershell
cd frontend
npm run dev
```

### Kill All Servers:
```powershell
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

---

## ✅ System Already Does This!

Your backend **already** auto-switches! You just need to:
1. Edit `.env` file
2. Comment out (#) the LLM you don't want
3. Restart backend

That's it! 🎉
