# PDF RAG Agent

A simple Retrieval-Augmented Generation (RAG) agent that answers questions about PDF documents using OpenAI embeddings, Supabase with pgvector, and PydanticAI.

## Features

- PDF document processing and text extraction
- Vector search using Supabase PostgreSQL with pgvector
- Question answering with PydanticAI
- Simple Streamlit chat interface

## Setup

### Prerequisites

- Python 3.10 or higher
- Supabase account with a project that has pgvector enabled
- OpenAI API key

### Installation

1. Clone the repository or create the project structure

2. Install dependencies
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables by copying the template:
   ```
   cp env.example .env
   ```
   
   Then edit the `.env` file with your:
   - OpenAI API key
   - Supabase project URL
   - Supabase anonymous key
   - Supabase service role key

4. Create the necessary database tables in Supabase
   ```
   python supabase_init_db.py
   ```
   
   Then follow the instructions to run the SQL commands in the Supabase dashboard.

## Usage

### Command Line Interface

1. Process and index PDF documents:
   ```bash
   # Process a single PDF file
   python -m rag_agent.main process path/to/your/document.pdf
   
   # Process all PDFs in a directory
   python -m rag_agent.main process path/to/pdf/directory
   
   # Process multiple specific files
   python -m rag_agent.main process doc1.pdf doc2.pdf doc3.pdf
   ```

2. List indexed documents:
   ```bash
   python -m rag_agent.main list
   ```

3. Check database tables:
   ```bash
   python -m rag_agent.main check-tables
   ```

### Streamlit Web Interface

1. Run the Streamlit app:
   ```bash
   streamlit run rag_agent/ui/app.py
   ```

2. Open your browser at http://localhost:8501

3. Upload PDFs using the file uploader in the sidebar

4. Ask questions about your documents in the chat interface

## Example Queries

Here are some examples of queries you can ask about your PDF documents:

- "What is the main topic of this document?"
- "Summarize the key points from page 2."
- "What does the document say about [specific term]?"
- "Compare the information on pages 1 and 3."
- "Find all mentions of [person/company name] in the document."

## Project Structure

- `db/`: Database schema and client
  - `supabase_client.py`: Client for interacting with Supabase with pgvector
  - `schema.py`: Database schema definitions
  - `client.py`: General database connection utilities
  - `check_tables.py`: Utilities to verify database setup
- `pdf/`: PDF processing utilities
- `agent/`: RAG agent implementation
- `ui/`: Streamlit user interface
- `tests/`: Test suite for verifying functionality
- `rag_agent/main.py`: CLI entry point for processing PDFs and managing documents
- `db_connection_test.py`: Script for testing direct database connectivity
- `supabase_init_db.py`: Script for setting up Supabase tables
- `supabase_vector_search.sql`: SQL function for vector similarity search

## Supabase Setup

This project uses Supabase PostgreSQL with pgvector for storing and retrieving document embeddings. The database tables are:

1. `documents` - Stores document metadata
   - id (serial primary key)
   - title (text)
   - filename (text, unique)
   - total_pages (integer)
   - created_at (timestamp)

2. `chunks` - Stores document chunks with embeddings
   - id (serial primary key)
   - document_id (references documents.id)
   - page_number (integer)
   - chunk_index (integer)
   - content (text)
   - embedding (vector(1536))
   - created_at (timestamp)

The project also creates a vector search function (`search_chunks`) for similarity search.

## Common Issues and Troubleshooting

### 1. "Error generating response: 'document_title'"

This error occurs when the vector search function in Supabase is missing the document_title field.

**Solution:**
1. Go to the Supabase SQL Editor
2. Drop the existing function:
   ```sql
   DROP FUNCTION search_chunks(vector,integer);
   ```
3. Re-create the function with the proper schema from `supabase_vector_search.sql`

### 2. Missing pgvector Extension

If you encounter an error about "type vector does not exist", follow these steps:

1. In the Supabase dashboard, go to the SQL Editor
2. Check if pgvector is available:
   ```sql
   SELECT * FROM pg_available_extensions WHERE name = 'vector';
   ```
3. Enable the extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### 3. Connection Issues

If you have trouble connecting to Supabase:

1. Check that your environment variables are correct in `.env`
2. Ensure your Supabase project is active and running
3. Try refreshing your API keys in the Supabase dashboard

### 4. PDF Processing Errors

If PDF processing fails:

1. Check that the PDF is not corrupt or password protected
2. Ensure the PDF contains actual text (not just scanned images)
3. For large PDFs, try processing them page by page

## Running Tests

To verify that your setup is working correctly:

```bash
# Run all tests
python -m pytest rag_agent/tests

# Test Supabase connection specifically
python -m pytest rag_agent/tests/test_supabase.py -v

# Test PDF processing
python -m pytest rag_agent/tests/test_pdf.py -v

# Test the RAG agent
python -m pytest rag_agent/tests/test_agent.py -v
```

## Supabase Connection Options

### Option 1: Allow Your IP Address

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Select your project
3. Go to Project Settings (gear icon) → Database
4. Find the "Connection Pooling" or "IP Allow List" section
5. Add your current IP address to the allow list
6. Save changes

### Option 2: Use Supabase REST API (Current Implementation)

This project uses the Supabase REST API for database interactions, which works over HTTPS and doesn't require IP whitelisting.

### Option 3: Use Supabase's Connection Pooling

For production applications, consider using Supabase's connection pooling:

```
postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-ID].pooler.supabase.co:5432/postgres
```

## License

MIT 