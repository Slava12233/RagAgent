"""Check if required tables exist in Supabase and create them if needed."""
import os
import json
import logging
import asyncio
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database schema for systems WITHOUT pgvector
DB_SCHEMA_NO_VECTOR = """
CREATE TABLE IF NOT EXISTS documents (
    id serial PRIMARY KEY,
    title text NOT NULL,
    filename text NOT NULL UNIQUE,
    total_pages integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks (
    id serial PRIMARY KEY,
    document_id integer REFERENCES documents(id) ON DELETE CASCADE,
    page_number integer NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    embedding_text text NOT NULL, -- Store embedding as serialized JSON
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, page_number, chunk_index)
);

-- Create a basic text search index
CREATE INDEX IF NOT EXISTS idx_chunks_content ON chunks USING gin(to_tsvector('english', content));
"""

# Original database schema with pgvector
DB_SCHEMA_WITH_VECTOR = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id serial PRIMARY KEY,
    title text NOT NULL,
    filename text NOT NULL UNIQUE,
    total_pages integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks (
    id serial PRIMARY KEY,
    document_id integer REFERENCES documents(id) ON DELETE CASCADE,
    page_number integer NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    embedding vector(1536) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, page_number, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_l2_ops);

-- Create a function for vector similarity search
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
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM chunks c
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
"""

async def check_supabase_tables():
    """Check if required tables exist in Supabase."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL or SUPABASE_ANON_KEY not set in environment")
        return False
    
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    
    # Log headers for debugging (excluding the actual key value)
    logger.info(f"Using Supabase URL: {supabase_url}")
    logger.info(f"Headers: {json.dumps({k: '***' if k in ['apikey', 'Authorization'] else v for k, v in headers.items()})}")
    
    # Check connection to Supabase
    try:
        logger.info("Testing connection to Supabase API...")
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers)
        if response.status_code not in (200, 401):  # 401 is expected for /rest/v1/ without table
            logger.error(f"Failed to connect to Supabase API: {response.status_code} - {response.text}")
            return False
        logger.info("Successfully connected to Supabase API")
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {e}")
        return False
    
    # Check if documents table exists
    try:
        logger.info("Checking if 'documents' table exists...")
        response = requests.get(f"{supabase_url}/rest/v1/documents?limit=1", headers=headers)
        
        documents_exists = response.status_code != 404
        logger.info(f"Documents table {'exists' if documents_exists else 'does not exist'}")
        
        # Check if chunks table exists
        logger.info("Checking if 'chunks' table exists...")
        response = requests.get(f"{supabase_url}/rest/v1/chunks?limit=1", headers=headers)
        
        chunks_exists = response.status_code != 404
        logger.info(f"Chunks table {'exists' if chunks_exists else 'does not exist'}")
        
        # Check if pgvector extension is available
        logger.info("Checking if vector search function exists...")
        response = requests.post(
            f"{supabase_url}/rest/v1/rpc/search_chunks",
            headers=headers,
            json={"query_embedding": [0.0] * 1536, "match_count": 1}
        )
        
        vector_search_works = response.status_code != 404
        logger.info(f"Vector search function {'exists' if vector_search_works else 'does not exist'}")
        
        # If tables are missing, print schema creation SQL
        if not documents_exists or not chunks_exists:
            logger.warning("One or more required tables are missing!")
            logger.info("Please run the following SQL in the Supabase SQL Editor:")
            
            if vector_search_works:
                logger.info(DB_SCHEMA_WITH_VECTOR)
            else:
                # Try to check if pgvector extension is available
                logger.info("Checking if pgvector extension is available...")
                logger.info("If pgvector is available, use this schema:")
                logger.info(DB_SCHEMA_WITH_VECTOR)
                logger.info("\nIf pgvector is NOT available, use this schema:")
                logger.info(DB_SCHEMA_NO_VECTOR)
            
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return False

if __name__ == "__main__":
    """Run the table check script."""
    asyncio.run(check_supabase_tables()) 