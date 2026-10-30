# NyayaSetu – AI-Powered Legal Advisor

**An AI-powered legal document summarization and question-answering system using Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG).**

NyayaSetu is an intelligent legal assistance platform designed to make Indian legal information more accessible through natural language conversations. It leverages Retrieval-Augmented Generation (RAG) to retrieve relevant legal provisions from a curated knowledge base of Indian legislation and generate context-aware responses using Large Language Models (LLMs).

The system integrates semantic search, agent-based orchestration, response caching, and persistent conversation storage to deliver an efficient and interactive legal information experience.

> **Disclaimer:** NyayaSetu is intended for educational and informational purposes only. It does not replace professional legal advice from a qualified advocate.

## Key Features

- **Legal Question Answering:** Ask questions about Indian laws using natural language.
- **Retrieval-Augmented Generation:** Retrieves relevant legal provisions to provide contextually grounded responses.
- **Multi-LLM Support:** Configurable LLM providers with support for Groq and Mistral.
- **Semantic Search:** Uses vector embeddings and Qdrant for retrieving relevant legal documents.
- **Agent-Based Orchestration:** Uses LangGraph to coordinate query processing, retrieval, and response generation.
- **Response Caching:** Redis caches eligible responses to reduce repeated LLM calls and improve response times.
- **Conversation History:** PostgreSQL provides persistent storage for chat history.
- **Interactive Interface:** Streamlit provides a conversational interface for interacting with the legal assistant.

## System Architecture

NyayaSetu follows a modular architecture consisting of a frontend, backend API, agent orchestration layer, vector database, caching system, and persistent storage.

```text
                  USER
                   |
                   v
          +--------------------+
          |    Streamlit UI    |
          |    Frontend        |
          |      :8501         |
          +--------------------+
                   |
                   v
          +--------------------+
          |      FastAPI       |
          |      Backend       |
          |      :8001         |
          +--------------------+
                   |
                   v
          +--------------------+
          |   LangGraph Agent  |
          | Query Processing   |
          | Retrieval & RAG    |
          +--------------------+
                   |
          +--------+---------+
          |        |         |
          v        v         v
       Qdrant    Redis    LLM API
       Vector    Cache    Groq /
       Search             Mistral
          |
          v
       PostgreSQL
       Chat History
```

### Architecture Components

| Component | Technology | Responsibility |
|---|---|---|
| Frontend | Streamlit | Provides the interactive chatbot interface |
| Backend | FastAPI | Handles API requests and application logic |
| Agent Framework | LangGraph | Orchestrates the question-answering workflow |
| LLM Providers | Groq / Mistral | Generates natural language responses |
| Vector Database | Qdrant | Stores embeddings and retrieves relevant legal documents |
| Embedding Model | Configured embedding model | Converts legal text into vector representations |
| Cache | Redis | Stores eligible responses for faster retrieval |
| Database | PostgreSQL | Maintains persistent conversation history |

## Legal Knowledge Base

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

**Note:** The current ingestion configuration excludes `data/hma.json` because the source file contains malformed JSON resulting from CSV conversion.

The knowledge base should also distinguish historical legislation from currently applicable legislation, particularly following the introduction of the Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA).

## Retrieval-Augmented Generation Workflow

NyayaSetu uses a RAG pipeline to generate responses grounded in retrieved legal information.

1. **User Query:** The user submits a legal question through the Streamlit interface.
2. **API Request:** FastAPI receives the query and forwards it to the application workflow.
3. **Query Processing:** LangGraph orchestrates the question-answering process.
4. **Semantic Retrieval:** The query is converted into an embedding, and relevant legal documents are retrieved from Qdrant.
5. **Context Preparation:** Retrieved legal provisions are assembled into contextual information.
6. **Response Generation:** The selected LLM provider (Groq or Mistral) generates a response using the retrieved context.
7. **Response Caching:** Redis caches eligible responses to improve performance for repeated queries.
8. **Conversation Persistence:** PostgreSQL stores conversation history.
9. **Response Delivery:** The generated response is returned to the Streamlit interface.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Providers | Groq, Mistral |
| Vector Database | Qdrant |
| Caching | Redis |
| Relational Database | PostgreSQL |
| Embeddings | Configured text embedding model |
| Containerization | Docker, Docker Compose |

## Project Structure

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

*The structure above illustrates the main project components. Refer to the repository for the complete directory structure.*

## Installation and Setup

### Prerequisites

Ensure the following are installed:

- Python 3.11 or later
- Git
- Bash
- Required local service binaries or access to the local service setup
- Internet connection for LLM API access

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd NyayaSetu
```

### 2. Configure Environment Variables

Create the environment configuration file:

```bash
cp .env.example .env
```

Configure your preferred LLM provider and API credentials in `.env`.

**Option A: Groq (Default)**

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
```

Generate an API key:

https://console.groq.com/keys

**Option B: Mistral**

```env
LLM_PROVIDER=mistral
MISTRAL_API_KEY=your_mistral_api_key
```

Generate an API key:

https://console.mistral.ai/

You can optionally override the configured model:

```env
LLM_MODEL=your_model_name
```

Use a model identifier supported by your selected provider.

### 3. Start the Application

NyayaSetu supports local execution without requiring Docker.

Start all services using:

```bash
./start.sh
```

The startup script launches the following services:

| Service | Port |
|---|---:|
| Streamlit UI | 8501 |
| FastAPI Backend | 8001 |
| PostgreSQL | 5433 |
| Redis | 6379 |
| Qdrant | 6333 |

### 4. Access the Application

Open the following URL in your browser:

```text
http://localhost:8501
```

The NyayaSetu legal advisor interface will be available locally.

### 5. Stop the Application

To stop the frontend and backend services:

```bash
./stop.sh
```

To stop the application along with its associated databases:

```bash
./stop.sh --all
```

Local service binaries, database data, and logs are maintained under:

```text
~/.local/lexai-services/
```

## Legal Document Ingestion

NyayaSetu includes a document ingestion pipeline that processes legal documents, generates vector embeddings, and stores them in Qdrant.

### Full Ingestion

Execute the following command:

```bash
.venv/bin/python -m app.ingestion.ingest
```

The ingestion process:

1. Reads legal document JSON files from the `data/` directory.
2. Processes and prepares the legal text.
3. Generates vector embeddings.
4. Stores the embeddings and associated document information in Qdrant.
5. Rebuilds the configured vector collection.

**Important:** Full ingestion wipes and rebuilds the existing collection. On CPU, the process takes approximately three hours.

Only perform full ingestion when the source documents or embedding model have changed.

### Selective Ingestion

To ingest or refresh a specific legal act without performing a full collection rebuild, pass its source identifier:

```bash
.venv/bin/python -m app.ingestion.ingest bnss
```

Use the source identifiers supported by the ingestion script.

**Note:** `data/hma.json` is currently excluded because its JSON structure is malformed following CSV conversion.

## Evaluation

NyayaSetu includes an evaluation script to assess the application's question-answering functionality.

Ensure the backend is running before executing:

```bash
.venv/bin/python evaluation.py
```

The evaluation script communicates with the running backend to process its test queries.

## Docker Deployment

NyayaSetu also supports containerized deployment using Docker Compose.

Ensure Docker and the Docker Compose plugin are installed and accessible to your user.

Build and start the application:

```bash
docker compose up --build
```

After the services are ready, perform the initial legal document ingestion inside the backend container.

## Security Considerations

- Store API keys and credentials in environment variables.
- Never commit `.env` files or sensitive credentials to version control.
- Avoid exposing database ports to public networks.
- Validate and sanitize incoming user queries.
- Implement authentication and authorization before public deployment.
- Maintain user-level isolation for conversation history.
- Apply appropriate cache-key isolation when caching user-specific queries.
- Treat LLM-generated responses as informational rather than verified legal advice.

## Future Enhancements

- PDF upload and legal document summarization.
- Expanded coverage of Indian legislation and amendments.
- Legal source citations with section and provision references.
- Hybrid retrieval and reranking for improved search relevance.
- Multilingual legal question answering.
- User authentication and isolated conversation sessions.
- Enhanced evaluation using retrieval precision, recall, and answer faithfulness.
- Production deployment with monitoring and centralized logging.

## Project Objective

The objective of NyayaSetu is to simplify access to Indian legal information through conversational AI.

By combining Retrieval-Augmented Generation, semantic search, agent-based orchestration, and persistent conversation management, the platform aims to help users understand complex legal documents and access relevant legal information through a natural language interface.

## Disclaimer

NyayaSetu is an educational and informational project. It does not provide professional legal advice, establish an advocate-client relationship, or replace consultation with a qualified legal professional.
