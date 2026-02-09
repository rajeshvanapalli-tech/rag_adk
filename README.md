# RAG ADK - AI-Powered Knowledge Base System

Intelligent RAG (Retrieval-Augmented Generation) system with dynamic chunking strategies for HR policies and product manuals.

## Features

- **Dynamic Chunking**: Auto-detects document type and applies optimal chunking strategy
  - **HR Documents**: Paragraph-based semantic chunking
  - **Product Manuals**: Step-aware + image-anchored procedural chunking
- **Multi-Agent System**: Unified master agent handling both HR and Product queries
- **Image Processing**: Automatically extracts and preserves images from documents
- **Vector Search**: ChromaDB with task-specific embeddings
- **Modern UI**: React-based frontend with real-time chat

## Tech Stack

**Backend:**
- FastAPI
- LangChain
- ChromaDB
- OpenAI / Google Gemini
- pypdf, python-docx

**Frontend:**
- Next.js / React
- Axios

## Setup

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001
```

### Frontend
```bash
cd frontend
npm install
npm run dev -- --port 3002
```

## API Endpoints

- `POST /upload` - Upload documents (auto-detects category)
- `POST /chat` - Chat with the AI
- `GET /files` - List uploaded files
- `DELETE /files/category/{category}` - Delete by category
- `GET /conversations` - List conversations

## Environment Variables

Create `.env` in backend:
```
OPENAI_API_KEY=your_key_here
MODEL_PROVIDER=openai
```

## License

MIT
