# PDF RAG Agent - File Directory Explanation

This document provides a detailed explanation of each file and directory in the PDF RAG Agent project.

## Root Directory Files

| File | Purpose |
|------|---------|
| **README.md** | Main project documentation with setup instructions, usage examples, and troubleshooting guide |
| **PROJECT_OVERVIEW.md** | Comprehensive technical documentation for CTO/CEO/developers about system architecture and implementation |
| **PLANNING.md** | Initial planning document outlining project architecture, workflow, and technical stack |
| **TASK.md** | Project task list with implementation status for tracking progress |
| **requirements.txt** | Lists all Python dependencies with version requirements for the project |
| **setup.py** | Python package configuration for installation using pip |
| **env.example** | Template for the .env file with placeholder values for required environment variables |
| **.env** | Contains actual environment variables (API keys, database credentials) - not committed to version control |
| **supabase_init_db.py** | Script to initialize the Supabase database with required tables and functions |
| **supabase_vector_search.sql** | SQL definition of the vector similarity search function for Supabase |
| **db_connection_test.py** | Utility script to test direct database connectivity (not required for normal operation) |

## Main Package Directory (`rag_agent/`)

| File/Directory | Purpose |
|----------------|---------|
| **\_\_init\_\_.py** | Package initialization file that makes `rag_agent` a proper Python package |
| **main.py** | Command-line interface entry point with PDF processing and document management commands |

### Database Module (`rag_agent/db/`)

| File | Purpose |
|------|---------|
| **\_\_init\_\_.py** | Package initialization for the db module |
| **schema.py** | Database schema definitions and connection utilities |
| **client.py** | Main database client for interacting with the Supabase database |
| **supabase_client.py** | Client for Supabase REST API interactions |
| **check_tables.py** | Utilities to verify database table setup |

### PDF Processing Module (`rag_agent/pdf/`)

| File | Purpose |
|------|---------|
| **\_\_init\_\_.py** | Package initialization for the pdf module |
| **processor.py** | PDF text extraction, chunking, and processing logic |

### Agent Module (`rag_agent/agent/`)

| File | Purpose |
|------|---------|
| **\_\_init\_\_.py** | Package initialization for the agent module |
| **rag.py** | RAG (Retrieval-Augmented Generation) agent implementation using PydanticAI |
| **tools.py** | Custom tools for the RAG agent (if present) |

### User Interface Module (`rag_agent/ui/`)

| File | Purpose |
|------|---------|
| **\_\_init\_\_.py** | Package initialization for the ui module |
| **app.py** | Streamlit web application interface |

### Tests (`rag_agent/tests/`)

| File | Purpose |
|------|---------|
| **\_\_init\_\_.py** | Package initialization for the tests module |
| **conftest.py** | pytest configuration and fixtures |
| **test_agent.py** | Unit tests for the RAG agent |
| **test_db.py** | Unit tests for database operations |
| **test_pdf.py** | Unit tests for PDF processing |
| **test_supabase.py** | Integration tests for Supabase connectivity |

## Generated Directories

| Directory | Purpose |
|-----------|---------|
| **venv/** | Python virtual environment (generated when setting up the project) |
| **.pytest_cache/** | Cache directory for pytest (generated when running tests) |
| **rag_agent.egg-info/** | Package metadata (generated during setup.py installation) |
| **\_\_pycache\_\_/** | Python bytecode cache directories (generated during execution) |

## Key Data Flow Between Files

1. **Document Processing Flow**:
   - User runs `rag_agent/main.py process` or uploads via UI (`rag_agent/ui/app.py`)
   - PDF processing happens in `rag_agent/pdf/processor.py`
   - Data is stored via `rag_agent/db/client.py` → `rag_agent/db/supabase_client.py`

2. **Query Flow**:
   - User asks question via UI (`rag_agent/ui/app.py`)
   - Query is processed by `rag_agent/agent/rag.py`
   - Relevant chunks retrieved via `rag_agent/db/client.py`
   - Answer generated using PydanticAI and OpenAI

## File Relationships Diagram

```
README.md                  # User documentation
└── rag_agent/             # Main package
    ├── main.py            # CLI entry point
    ├── pdf/               # PDF processing
    │   └── processor.py   # ┐
    ├── db/                # │ Core 
    │   ├── client.py      # │ application
    │   └── supabase_*.py  # │ logic
    ├── agent/             # │
    │   └── rag.py         # ┘
    └── ui/                # User interface
        └── app.py         # Streamlit app
```

## Dependency Map

- `rag_agent/ui/app.py` → `rag_agent/agent/rag.py` → `rag_agent/db/client.py`
- `rag_agent/main.py` → `rag_agent/pdf/processor.py` → `rag_agent/db/client.py`
- `rag_agent/db/client.py` → `rag_agent/db/supabase_client.py`

## Configuration Flow

1. `.env` (from env.example) provides configuration values
2. `supabase_init_db.py` sets up the database using these values
3. Application components read configuration from environment variables 