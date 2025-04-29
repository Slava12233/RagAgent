# PDF RAG Agent with PydanticAI

## Project Overview
A simple Retrieval-Augmented Generation (RAG) agent that can answer questions about PDF documents using PydanticAI.

## Architecture

### Components
1. **PDF Processor**: Extract and chunk text from PDF files
2. **Vector Database**: Store document chunks with embeddings (PostgreSQL + pgvector)
3. **Embedding Service**: Generate embeddings for text chunks (OpenAI embeddings)
4. **RAG Agent**: PydanticAI agent with retrieval tool
5. **UI**: Simple Streamlit interface for chatting with the agent

### Workflow
1. User uploads PDF documents
2. System processes PDFs, chunks text, and stores with embeddings in database
3. User asks questions through the UI
4. Agent uses vector search to retrieve relevant chunks
5. Agent generates answers using retrieved context

## Technical Stack
- **Language**: Python 3.10+
- **PDF Processing**: PyPDF2 or PyMuPDF (fitz)
- **Vector Database**: PostgreSQL with pgvector
- **Embeddings**: OpenAI text-embedding-3-small
- **Agent Framework**: PydanticAI
- **LLM**: OpenAI GPT-4o
- **UI**: Streamlit
- **Dependencies**: asyncpg, httpx, pydantic

## Data Structure
- Database schema with tables for documents, chunks, and embeddings
- Each document chunk will have:
  - Document ID
  - Chunk ID
  - Page number
  - Text content
  - Embedding vector (1536 dimensions)

## File Structure
```
rag_agent/
├── requirements.txt      # Project dependencies
├── README.md             # Project documentation
├── db/
│   ├── schema.py         # Database schema definitions
│   └── client.py         # Database connection and operations
├── pdf/
│   └── processor.py      # PDF processing utilities
├── agent/
│   ├── rag.py            # RAG agent implementation
│   └── tools.py          # Agent tools
├── ui/
│   └── app.py            # Streamlit UI
└── main.py               # Entry point
```

## Conventions
- Use type hints throughout the codebase
- Follow PEP8 style guidelines
- Use async/await for database operations and OpenAI API calls
- Document all functions with docstrings using Google style 