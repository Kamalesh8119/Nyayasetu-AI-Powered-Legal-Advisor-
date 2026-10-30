# ⚖️ NyayaSetu – AI-Powered Legal Advisor

**An intelligent Legal Document Summarization and Question-Answering System using Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG).**

NyayaSetu is an AI-powered legal assistance platform designed to help users understand Indian laws through natural language conversations. It uses Retrieval-Augmented Generation (RAG) to retrieve relevant legal provisions from a curated knowledge base of Indian legislation and generate context-aware responses using Large Language Models (LLMs).

The system combines semantic search, agent-based reasoning, response caching, and persistent conversation history to provide an efficient and user-friendly legal information assistant.

> **Disclaimer:** NyayaSetu is an informational legal assistance tool and does not replace professional legal advice from a qualified advocate.

---

## 🚀 Key Features

- **Legal Question Answering:** Ask questions about Indian laws using natural language.
- **Retrieval-Augmented Generation (RAG):** Retrieves relevant legal provisions before generating responses.
- **Multi-LLM Support:** Supports Groq and Mistral as configurable LLM providers.
- **Semantic Search:** Uses vector embeddings and Qdrant for retrieving relevant legal information.
- **Agent-Based Architecture:** Uses LangGraph to orchestrate the legal question-answering workflow.
- **Response Caching:** Redis caches answers to reduce repeated LLM calls and improve response time.
- **Conversation History:** PostgreSQL stores chat history for persistent conversations.
- **Interactive Interface:** Streamlit provides an accessible conversational interface.

## 🏗️ System Architecture

NyayaSetu follows a modular architecture consisting of a frontend, backend API, agent orchestration layer, vector database, caching layer, and persistent storage.

```text
                 ┌─────────────────────────┐
                 │       USER              │
                 │  Legal Question / Query │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │     STREAMLIT UI        │
                 │   Frontend :8501        │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │      FASTAPI            │
                 │   Backend :8001         │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │    LANGGRAPH AGENT      │
                 │ Query Processing        │
                 │ Retrieval & Generation  │
                 └────────────┬────────────┘
                              │
                  ┌───────────┼────────────┐
                  │           │            │
                  ▼           ▼            ▼
             ┌────────┐  ┌─────────┐  ┌──────────┐
             │ Qdrant │  │  Redis  │  │ LLM API  │
             │ Vector │  │  Cache  │  │ Groq /   │
             │ Search │  │         │  │ Mistral  │
             └────────┘  └─────────┘  └──────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │      PostgreSQL         │
                 │   Chat History Storage  │
                 └─────────────────────────┘
```

### Architecture Components

| Component | Technology | Responsibility |
|---|---|---|
| Frontend | Streamlit | Interactive chatbot interface |
| Backend | FastAPI | API endpoints and request handling |
| Agent Framework | LangGraph | Orchestrates retrieval and response generation |
| LLM | Groq / Mistral | Generates natural language responses |
| Vector Database | Qdrant | Stores embeddings and retrieves legal documents |
| Embedding Model | Configured embedding model | Converts legal text into vector representations |
| Cache | Redis | Caches previously generated answers |
| Database | PostgreSQL | Stores conversation history |

## 📚 Legal Knowledge Base

The system uses a curated collection of Indian legal documents to support legal information retrieval.

The knowledge base includes:

- Constitution of India
- Bharatiya Nyaya Sanhita (BNS)
- Code of Criminal Procedure (CrPC)
- Code of Civil Procedure (CPC)
- Indian Divorce Act
- Motor Vehicles Act
- Indian Evidence Act
- Negotiable Instruments Act

**Note:** The repository's current ingestion configuration excludes `data/hma.json` because the source file is malformed. Also, older legislation such as the IPC, CrPC and Indian Evidence Act has undergone legislative changes or replacement. The knowledge base should be updated and versioned to distinguish historical legislation from currently applicable laws.

## 🔄 RAG Workflow

The application follows a Retrieval-Augmented Generation pipeline:

1. **User Query:** The user submits a legal question through the Streamlit interface.
2. **API Request:** FastAPI receives the question and forwards it to the agent.
3. **Query Processing:** LangGraph orchestrates the question-answering workflow.
4. **Semantic Retrieval:** The query is converted into an embedding and relevant legal documents are retrieved from Qdrant.
5. **Context Preparation:** Retrieved legal provisions are assembled into contextual information.
6. **Response Generation:** The selected LLM (Groq or Mistral) generates an answer using the retrieved context.
7. **Caching:** Redis stores eligible responses for subsequent queries.
8. **Conversation Storage:** PostgreSQL persists chat history.
9. **Response Delivery:** The generated answer is returned to the Streamlit interface.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Providers | Groq, Mistral |
| Vector Database | Qdrant |
| Cache | Redis |
| Relational Database | PostgreSQL |
| Embeddings | Configured text embedding model |
| Deployment | Docker, Docker Compose |

---

## 📂 Project Structure

```text
NyayaSetu/
│
├── app/
│   ├── ingestion/
│   │   └── ingest.py
│   ├── backend/
│   ├── frontend/
│   └── ...
│
├── data/
│   ├── constitution.json
│   ├── bns.json
│   ├── crpc.json
│   ├── cpc.json
│   ├── hma.json
│   └── ...
│
├── evaluation.py
├── start.sh
├── stop.sh
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

*The structure above illustrates the main project components. Adjust filenames and directories to match the actual repository.*

---

## ⚙️ Installation and Setup

### Prerequisites

Ensure the following are installed:

- Python 3.11+
- Git
- Bash
- Required service binaries or access to the local service setup
- Internet connection for LLM API access

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd NyayaSetu
```

### 2. Configure Environment Variables

Create your environment configuration file:

```bash
cp .env.example .env
```

Open `.env` and configure your API credentials.

**Option A: Groq (Default)**

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
```

Get your API key:

https://console.groq.com/keys

**Option B: Mistral**

```env
LLM_PROVIDER=mistral
MISTRAL_API_KEY=your_mistral_api_key
```

Get your API key:

https://console.mistral.ai/

You can optionally override the configured model:

```env
LLM_MODEL=your_model_name
```

Use the model identifier supported by your selected provider.

### 3. Start the Application

Start the complete local environment without Docker:

```bash
./start.sh
```

The startup script launches the following services:

| Service | Local Port |
|---|---:|
| Streamlit UI | 8501 |
| FastAPI Backend | 8001 |
| PostgreSQL | 5433 |
| Redis | 6379 |
| Qdrant | 6333 |

### 4. Access the Application

Open the following URL in your browser:

http://localhost:8501

The NyayaSetu legal advisor interface should now be accessible.

### 5. Stop the Application

Stop the frontend and backend:

```bash
./stop.sh
```

Stop the application and all associated databases:

```bash
./stop.sh --all
```

Local service binaries, database data, and logs are maintained under:

```text
~/.local/lexai-services/
```

---

## 📥 Legal Document Ingestion

NyayaSetu uses a one-time ingestion process to convert legal documents into vector embeddings and store them in Qdrant.

### Full Ingestion

Run the following command:

```bash
.venv/bin/python -m app.ingestion.ingest
```

This process:

1. Reads the legal document JSON files from `data/`.
2. Processes the legal text.
3. Generates embeddings.
4. Stores the resulting vectors in Qdrant.
5. Rebuilds the configured vector collection.

**Important:** A full ingestion wipes and rebuilds the existing collection. On CPU, the operation can take approximately three hours.

Do not execute full ingestion unnecessarily.

### Selective Ingestion

To ingest or refresh a specific legal act without rebuilding the entire collection, provide its source name:

```bash
.venv/bin/python -m app.ingestion.ingest bnss
```

Use the appropriate source identifiers supported by the ingestion script.

**Note:** `data/hma.json` is currently excluded because its CSV conversion produced malformed JSON.

---

## 🧪 Evaluation

NyayaSetu includes an evaluation script to assess the application's question-answering functionality.

First, ensure the backend is running.

Execute:

```bash
.venv/bin/python evaluation.py
```

The evaluation script requires the running backend to process its test queries.

---

## 🐳 Docker Deployment

NyayaSetu also supports Docker Compose deployment.

Ensure Docker and the Docker Compose plugin are installed and that your user has permission to access Docker.

Build and start the services:

```bash
docker compose up --build
```

Run the initial legal document ingestion inside the backend container once after the services are ready.

---

## 🔐 Security Considerations

- Store API keys and credentials in environment variables.
- Never commit `.env` files or API secrets to GitHub.
- Avoid exposing database ports publicly.
- Validate and sanitize incoming user queries.
- Apply appropriate authentication and authorization before exposing the application publicly.
- Implement user-level isolation for conversation history.
- Avoid caching sensitive user-specific legal queries without appropriate cache-key isolation.
- Do not treat LLM-generated responses as verified legal advice.

---

## 🚧 Future Improvements

- PDF upload and legal document summarization.
- Support for additional Indian legislation and amendments.
- Source citations with section and provision references.
- Improved retrieval through hybrid search and reranking.
- Multilingual legal question answering.
- User authentication and isolated chat sessions.
- Enhanced evaluation using retrieval precision, recall, and answer faithfulness.
- Production deployment with monitoring and logging.

---

## 🎯 Project Objective

The primary objective of NyayaSetu is to make Indian legal information more accessible through conversational AI.

By combining Retrieval-Augmented Generation, vector search, LLM-based reasoning, and persistent conversation management, the platform aims to simplify access to complex legal information and help users understand relevant legal provisions.

---

## 👨‍💻 Author

**NyayaSetu – Legal Document Summarization and Question-Answering System**

Built using Python, FastAPI, Streamlit, LangGraph, Qdrant, Redis, PostgreSQL, and LLM APIs.

---

**Disclaimer:** This project is developed for educational and informational purposes. It does not constitute legal advice, and users should consult qualified legal professionals for specific legal matters.
