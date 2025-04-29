# PDF RAG Agent - Technical Documentation

## Executive Summary

The PDF RAG Agent is a Retrieval-Augmented Generation (RAG) system that processes PDF documents, stores their content with vector embeddings, and answers natural language queries about the documents' content. This document provides a technical overview of the system's architecture, components, data flow, and implementation details.

## Technology Stack

### Core Technologies

| Technology | Purpose | Implementation |
|------------|---------|---------------|
| **Python 3.10+** | Primary programming language | Core application logic, processing, and API interactions |
| **Supabase PostgreSQL** | Vector database | Document storage, vector embeddings, and similarity search |
| **pgvector** | Vector extension for PostgreSQL | Enables vector similarity search in the database |
| **OpenAI APIs** | Embeddings and language model | Text-embedding-3-small for embeddings, GPT-4o for answering |
| **PydanticAI** | Agent framework | Structures the RAG system with retrieval tools |
| **Streamlit** | Web user interface | Provides simple, interactive UI for users |

### Key Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| pydantic-ai | ≥0.1.8 | Agent framework for structured AI interactions |
| openai | ≥1.15.0 | Client for OpenAI API services |
| asyncpg | ≥0.29.0 | Asynchronous PostgreSQL client |
| httpx | ≥0.27.0 | HTTP client for async API calls |
| pymupdf (fitz) | ≥1.24.0 | PDF processing and text extraction |
| numpy | ≥1.26.0 | Vector operations and numerical processing |
| streamlit | ≥1.32.0 | Web interface development |
| python-dotenv | ≥1.0.0 | Environment variable management |
| psycopg2-binary | ≥2.9.9 | PostgreSQL database driver |
| pgvector | ≥0.2.4 | Python client for pgvector |
| pydantic | ≥2.5.0 | Data validation and settings management |
| requests | ≥2.31.0 | HTTP client for Supabase REST API |

## System Architecture

The system follows a modular architecture with clear separation of concerns:

![System Architecture](https://mermaid.ink/img/pako:eNqNkk9PwzAMxb9KlHMR7NTblnFCQpuExAEhLk16KaNLW-U_Go347qRpB0xIgFOcvPj32nHPIBkX4IO2qBnL8FJ7bfCYOu5UpUXGFu-GbDjlUomSrCgjH4_R0pJQklO1kjkpeecEaZPh40P-ULjQcbXlMVJwxE9oWPaBM1W3SXwKDWs-7yOb9j7f3kj-Jlf5bZzfJUNXWsLV8cRVJpTu1wSTL4U8LnVDRsgrPc9cY6RDNC3pK-lWOZkFOctIfQvGXLiyqnW-vBIKvVIb9HBFimsqR40gYF_s9s2-vq8bStLyFH3fQP-vR8MjqC1D13RI2q2_D4kPgfsbmK5lDw?type=png)

### Components

1. **PDF Processor**: 
   - Extracts text from PDFs using PyMuPDF
   - Splits text into manageable chunks
   - Manages document metadata

2. **Embedding Service**:
   - Uses OpenAI's text-embedding-3-small model
   - Generates 1536-dimensional vector embeddings for text chunks
   - Enables semantic similarity search

3. **Vector Database**:
   - Supabase PostgreSQL with pgvector extension
   - Stores document metadata, text chunks, and vector embeddings
   - Performs vector similarity search

4. **RAG Agent**:
   - Built with PydanticAI framework
   - Retrieves relevant document chunks based on queries
   - Uses OpenAI's GPT-4o to generate answers from retrieved content

5. **Web Interface**:
   - Streamlit-based UI
   - Provides document upload functionality
   - Implements chat interface for asking questions

## Data Flow

1. **Document Processing Pipeline**:
   ```
   Upload PDF → Extract Text → Chunk Text → Generate Embeddings → Store in Database
   ```

2. **Query Processing Pipeline**:
   ```
   User Query → Generate Query Embedding → Vector Similarity Search → Retrieve Relevant Chunks → Generate Answer
   ```

## Implementation Details

### PDF Processing

The PDF processing module uses PyMuPDF (fitz) for text extraction and implements a sophisticated chunking strategy:

1. **Text Extraction**:
   - Extracts text page by page while preserving structure
   - Handles various PDF formatting and encoding issues
   - Cleans and normalizes text (removes excessive whitespace, fixes encoding)

2. **Chunking Strategy**:
   - Uses a page-based chunking approach with consideration for context
   - Maintains metadata about page numbers and positions
   - Balances chunk size (typically 1000-1500 characters) for optimal embedding quality

### Vector Database Implementation

The system uses Supabase PostgreSQL with pgvector for vector storage and similarity search:

1. **Database Schema**:
   - `documents` table for document metadata
   - `chunks` table for text chunks with vector embeddings
   - Vector indices for efficient similarity search

2. **Vector Search Function**:
   ```sql
   CREATE OR REPLACE FUNCTION search_chunks(
       query_embedding vector(1536),
       match_count int DEFAULT 5
   ) 
   RETURNS TABLE(
       id int,
       document_id int,
       page_number int,
       chunk_index int,
       content text,
       document_title text,
       similarity float
   )
   LANGUAGE plpgsql
   AS $$
   BEGIN
       RETURN QUERY
       SELECT
           c.id,
           c.document_id,
           c.page_number,
           c.chunk_index,
           c.content,
           d.title as document_title,
           1 - (c.embedding <=> query_embedding) AS similarity
       FROM chunks c
       JOIN documents d ON c.document_id = d.id
       ORDER BY c.embedding <=> query_embedding
       LIMIT match_count;
   END;
   $$;
   ```

3. **Database Access**:
   - Uses the Supabase REST API for cross-platform compatibility
   - Implements robust error handling and retry mechanisms
   - Provides asynchronous operations for better performance

### RAG Implementation

The RAG agent uses PydanticAI to structure the retrieval and generation process:

1. **Retrieval Tool**:
   - Accepts natural language queries
   - Converts queries to vector embeddings
   - Retrieves most similar document chunks
   - Formats retrieved content with metadata

2. **Agent Prompt Engineering**:
   - Uses carefully crafted system prompts
   - Instructs the model to cite sources and page numbers
   - Provides guidelines for handling cases where information is insufficient

3. **Answer Generation**:
   - Uses OpenAI GPT-4o for high-quality responses
   - Generates answers based only on retrieved content
   - Provides citations to document sources

### User Interface

The Streamlit-based UI provides a simple, intuitive interface:

1. **Document Management**:
   - PDF upload with validation and progress indicators
   - Document list with metadata display
   - Refresh functionality to show newly uploaded documents

2. **Chat Interface**:
   - Clean, chat-like interface for questions and answers
   - Input validation for user queries
   - Error handling with helpful suggestions

## Security Measures

1. **API Key Management**:
   - Environment variables for sensitive credentials
   - No hardcoded credentials in the codebase

2. **Input Validation**:
   - File type and size validation for uploads
   - Query length and content validation

3. **Error Handling**:
   - Graceful failure with informative error messages
   - Logging for troubleshooting without exposing sensitive information

## Performance Considerations

1. **Asynchronous Operations**:
   - Async/await pattern for I/O-bound operations
   - Concurrent processing where possible

2. **Database Optimizations**:
   - Vector indexes for efficient similarity search
   - Document ID caching to reduce redundant lookups

3. **Memory Management**:
   - Process large PDFs in chunks to avoid memory issues
   - Clean up temporary files after processing

## Testing Approach

The project includes a comprehensive test suite:

1. **Unit Tests**:
   - Tests for individual components (PDF processor, database client, etc.)
   - Mocked dependencies for isolated testing

2. **Integration Tests**:
   - Tests for component interactions
   - Actual database and API interactions

3. **Test Coverage**:
   - Focus on core functionality and error cases
   - Both expected and edge cases

## Deployment Considerations

1. **Environment Setup**:
   - Python 3.10+ environment
   - Required environment variables
   - Supabase with pgvector extension

2. **Scaling**:
   - Consider connection pooling for production
   - Implement caching for frequent queries
   - Monitor API usage (OpenAI costs)

## Future Enhancements

1. **Document Support**:
   - Extend to other document types (DOCX, TXT, HTML)
   - Support for image-based PDFs with OCR

2. **Chunking Improvements**:
   - Semantic chunking based on content structure
   - Hierarchical chunking with summaries

3. **Search Enhancements**:
   - Metadata filtering
   - Hybrid search (vector + keyword)
   - Multi-query retrieval

4. **User Features**:
   - Chat history
   - User authentication
   - Document sharing and permissions

5. **Performance**:
   - Caching of common queries
   - Batch processing for large document sets
   - Alternative embedding models for specific domains

## Conclusion

The PDF RAG Agent provides a powerful, flexible system for document question answering. Its modular architecture allows for easy extension and maintenance, while the use of state-of-the-art technology ensures high-quality results. The combination of vector embeddings for retrieval and large language models for generation creates a system that can understand and answer complex questions about document content with accuracy and context awareness. 