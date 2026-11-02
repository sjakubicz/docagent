# docagent

Sample RAG agent over PDF documents: FastAPI, PostgreSQL + pgvector, hybrid search
(BM25 + vectors), a LangGraph tool-use agent, retrieval evaluation, Docker and CI.

Runs fully locally on a laptop GPU through Ollama, and can switch to any OpenAI-compatible hosted provider (e.g. Novita) by changing three environment variables.

## Architecture

```
React 19 + Chakra UI ──(typed client generated from OpenAPI)──► FastAPI
                                                                  │
          ┌───────────────────────────────┬───────────────────────┤
          ▼                               ▼                       ▼
   PDF ingest                     Hybrid search             LangGraph agent
   pdfplumber text layer          BM25 (bm25s, in memory)   tools: search_documents,
   + Tesseract OCR fallback       + pgvector cosine (HNSW)         list_documents,
   → chunks → embeddings          fused with RRF                   read_page
          │                               │                       │
          └──────────► PostgreSQL + pgvector ◄────────────────────┘
                                                                  │
                         OpenAI-compatible API: Ollama (local) or a hosted provider
```

- **Extraction**: pdfplumber extracts the text layer; pages with no text (scans) are rendered and
  read by Tesseract. Text is split into overlapping, word-aligned chunks and embedded.
- **Search**: BM25 catches exact terms, vectors catch paraphrases;
  Reciprocal Rank Fusion merges both rankings without score calibration.
- **Agent**: a small explicit LangGraph graph, `retrieve → agent, tools`, with a step budget.
  The first search always runs; the agent then decides whether to search again or read a whole page. It
  cites sources as `[filename, p. N]`, and the API returns the passages and tool calls.
- **Evaluation**: hit@1, hit@k and MRR@k for BM25, vector and hybrid retrieval on a labelled
  question set. No LLM involved, so it runs in seconds.

## Running

Requires uv, Yarn (`corepack enable`), Docker, Tesseract and Ollama.

Models:

```bash
ollama pull qwen3:4b-instruct && ollama pull nomic-embed-text
```

Database:

```bash
docker compose up -d db
```

Backend (http://localhost:8000, API docs at `/docs`):

```bash
cd backend && uv run fastapi dev src/docagent/main.py
```

Frontend (http://localhost:5173):

```bash
cd frontend && yarn install && yarn dev
```

Sample documents (synthetic medical PDFs, one scanned):

```bash
cd backend && uv run python -m docagent.ingest ../data/samples/*.pdf
```

Retrieval evaluation:

```bash
cd backend && uv run python -m docagent.eval
```

Regenerate the API client after backend changes:

```bash
cd frontend && yarn gen:api
```

Settings (database, LLM and embedding endpoints) live in `backend/.env`; see `backend/.env.example`.
