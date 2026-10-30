# NyayaSetu · Legal Advisor

RAG chatbot for Indian law: Streamlit UI → FastAPI backend → LangGraph agent (Groq or Mistral LLM)
over a Qdrant index of the Constitution, BNS, CrPC, CPC, Indian Divorce Act, Motor Vehicles Act,
Indian Evidence Act and Negotiable Instruments Act. Redis caches answers; Postgres stores chat history.

## Run locally (no Docker)

```bash
./start.sh          # Postgres :5433, Redis :6379, Qdrant :6333, backend :8001, UI :8501
./stop.sh           # stop backend + UI   (./stop.sh --all also stops the databases)
```

Open http://localhost:8501. Service binaries, data and logs live in `~/.local/lexai-services/`.

## Configuration

Copy `.env.example` to `.env` and set `GROQ_API_KEY` (free at https://console.groq.com/keys).
To use Mistral instead, set `LLM_PROVIDER=mistral` and `MISTRAL_API_KEY`. `LLM_MODEL` overrides the model.

## Ingestion (one-time)

```bash
.venv/bin/python -m app.ingestion.ingest
```

Embeds `data/*.json` into Qdrant. On CPU this takes ~3 hours and **wipes and rebuilds** the
collection, so only re-run it when the data or embedding model changes.
To add or refresh a single act without a full rebuild, pass its source name(s), e.g.
`.venv/bin/python -m app.ingestion.ingest bnss`.
`data/hma.json` is malformed (broken CSV conversion) and is not ingested.

## Evaluation

```bash
.venv/bin/python evaluation.py    # needs the backend running
```

## Docker

`docker compose up --build` still works if your user can access Docker and the compose plugin
is installed; run the ingestion inside the backend container once.
