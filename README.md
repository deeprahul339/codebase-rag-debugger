# Codebase RAG Debugger

Point it at a public GitHub repo. Ask questions like "what calls this
function" or "trace how auth flows through this codebase" and get answers
grounded with real `file:line` citations — not a generic text-splitter RAG demo.

## Why this is different from a typical RAG project

Most "chat with your docs" RAG tutorials split text into fixed-size windows.
This project chunks code by **function/class boundary** (see
`backend/src/ingestion/code_chunker.py`), so retrieved context is always a
complete, coherent unit — a whole function, not half of one. That's the
detail worth explaining in an interview.

## Architecture

```
GitHub repo URL
      │
      ▼
 file_scanner.py   → walks the repo, filters to source files
      │
      ▼
 code_chunker.py   → splits by function/class boundary (not fixed windows)
      │
      ▼
 indexer.py        → embeds chunks, stores in a local embedded Chroma index
      │              (chromadb.PersistentClient — writes to a local folder,
      │               no server process, no Docker)
      ▼
 retriever.py      → vector search over the local index per question
      │
      ▼
 model.py          → Groq LLM answers, grounded in retrieved chunks,
                       citing file:line inline
      │
      ▼
   Chat.tsx        → frontend renders answer + SourceCard citations
```

## Getting started (Python backend, no Docker required)

### 1. Prerequisites
- Python 3.10+
- Node.js 20+ (frontend only)
- A Groq API key (free tier) — https://console.groq.com/
- A Voyage AI API key (free tier) — https://www.voyageai.com/
  (Groq doesn't offer embeddings, so this project uses Voyage's
  `voyage-code-3` model, which is tuned for source code)

### 2. Environment setup

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

Edit `backend/.env` and fill in:
```
GROQ_API_KEY=your_key_here
VOYAGE_API_KEY=your_key_here
```

### 3. Install and run — two terminals, no Docker

This project supports either `uv` (recommended — faster installs, no manual
venv activation needed) or plain `pip`.

**Using `uv`:**
```bash
# terminal 1 - backend
cd backend
uv sync
uv run python server.py
# → http://localhost:4000  (check /health)

# terminal 2 - frontend
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

**Using `pip`:**
```bash
# terminal 1 - backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py
# → http://localhost:4000  (check /health)

# terminal 2 - frontend
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

Visit `http://localhost:3000`, paste a public GitHub repo URL, and start
asking questions. Indexed data is stored locally in `backend/.chroma/`
(the embedded Chroma index) and `backend/.workspace/` (the cloned repo) —
delete those folders any time to reset.

## Suggested 2–3 day build order

**Day 1 — ingestion pipeline works end-to-end**
- `file_scanner.py` → `code_chunker.py` → `indexer.py`
- Confirm your Voyage AI key works and chunks land in the local Chroma index

**Day 2 — retrieval + LLM answers**
- `retriever.py` returning relevant chunks for a test query
- `model.py` answering with citations via Groq
- Test against a real repo end-to-end via curl/Postman before touching the UI

**Day 3 — frontend + polish**
- Wire up `UploadRepo` → `Chat` → citation rendering
- Pick 5-10 good demo questions on a well-known repo (e.g. something with
  clear auth/data flow) so you have a smooth interview demo
- Write up the AST-vs-naive-chunking tradeoff in your README/portfolio —
  that's the story that gets you hired, not the UI

## Known stubs / TODOs left on purpose

- `code_chunker.py` uses regex boundary detection, not true AST parsing —
  swapping in `tree-sitter` for real AST-based chunking is a great
  "what would you improve" answer for an interview
- Indexing is synchronous — fine for a demo, mention background task
  queues (Celery, FastAPI `BackgroundTasks`) as the production fix
- The embedded Chroma index is fine at demo scale (a few thousand
  chunks); for a larger index or multi-user deployment, swap in a hosted
  vector DB (Pinecone, Qdrant Cloud, Chroma Cloud) — `retriever.py` is
  designed so that swap doesn't touch any other file
- No auth, no persistence beyond the local index — intentionally out of
  scope for a 2-3 day build
