"""Database schema initialization script for Supabase.

This script helps set up the necessary tables and functions for the RAG application
in a Supabase PostgreSQL database with pgvector support.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase API details
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Headers for API requests
headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
}

# Schema with JSON embeddings as fallback if pgvector is not available
DB_SCHEMA_NO_VECTOR = """
-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id serial PRIMARY KEY,
    title text NOT NULL,
    filename text NOT NULL UNIQUE,
    total_pages integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- Create chunks table without pgvector
CREATE TABLE IF NOT EXISTS chunks (
    id serial PRIMARY KEY,
    document_id integer REFERENCES documents(id) ON DELETE CASCADE,
    page_number integer NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    embedding_json jsonb NOT NULL, -- Store embedding as JSON
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, page_number, chunk_index)
);

-- Create a basic text search index
CREATE INDEX IF NOT EXISTS idx_chunks_content ON chunks USING gin(to_tsvector('english', content));
"""

# Schema with pgvector
DB_SCHEMA_WITH_VECTOR = """
-- First, enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id serial PRIMARY KEY,
    title text NOT NULL,
    filename text NOT NULL UNIQUE,
    total_pages integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- Create chunks table with pgvector
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

-- Create vector search index
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_l2_ops);
"""

# Vector search function - updated to include document_title
VECTOR_SEARCH_FUNCTION = """
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
"""

def main():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set.")
        print("Make sure you have a .env file with these variables or set them in your environment.")
        return
        
    print("Initializing database schema in Supabase...")
    
    print("""
The error 'ERROR: 42704: type vector does not exist' indicates that the pgvector extension 
is not available or not properly enabled in your Supabase database.
    
Please go to https://app.supabase.com/ and:
1. Select your project
2. Go to the SQL Editor tab
3. First check if pgvector is available by running:

   SELECT * FROM pg_available_extensions WHERE name = 'vector';

If pgvector is available, enable it with:

   CREATE EXTENSION IF NOT EXISTS vector;

If pgvector is NOT available, you have two options:
1. Upgrade your Supabase plan to one that includes pgvector support
2. Use the alternative schema that stores embeddings as JSON
""")

    print("\nHere are two schema options:")
    
    print("\n------ OPTION 1: Schema with pgvector (preferred) ------")
    print(DB_SCHEMA_WITH_VECTOR)
    
    print("\n------ OPTION 2: Schema without pgvector (fallback) ------")
    print(DB_SCHEMA_NO_VECTOR)
    
    print("\n------ Vector Search Function (if using pgvector) ------")
    print(VECTOR_SEARCH_FUNCTION)
    
    # Test if we can access the database at all
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/",
            headers=headers
        )
        
        if response.status_code == 200:
            print("\nConnection to Supabase API works.")
            print("Once you've created your tables, test again with: python -m rag_agent.tests.test_supabase")
        else:
            print("\nWarning: Cannot connect to Supabase API.")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"\nError connecting to Supabase API: {e}")
        print("Please check your SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")

if __name__ == "__main__":
    main() 