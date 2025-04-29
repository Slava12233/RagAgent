"""Database schema for PDF RAG agent."""
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional, Any, Dict
import warnings

import asyncpg
from dotenv import load_dotenv

from rag_agent.db.supabase_client import SupabaseClient

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters - keep for reference
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:54320/pdf_rag")
SERVER_DSN = DB_URL.rsplit("/", 1)[0]
DATABASE = DB_URL.rsplit("/", 1)[1].split("?")[0]  # Remove query parameters

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
    embedding_text text NOT NULL, -- Store embedding as serialized JSON text
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
"""

# Use pgvector schema with Supabase
DB_SCHEMA = DB_SCHEMA_WITH_VECTOR

# Mock pool class to provide compatibility with existing code
# This allows us to switch between direct PostgreSQL and Supabase API
class MockPool:
    def __init__(self, supabase_client):
        self.supabase_client = supabase_client
    
    async def close(self):
        pass
    
    async def acquire(self):
        return MockConnection(self.supabase_client)
    
    @asynccontextmanager
    async def acquire_context(self):
        conn = await self.acquire()
        try:
            yield conn
        finally:
            pass  # No need to release with REST API

class MockConnection:
    def __init__(self, supabase_client):
        self.supabase_client = supabase_client
        
    async def execute(self, query, *args):
        # Log the query but don't execute - must be done through Supabase dashboard
        logger.info(f"SQL Query (not executed): {query}")
        return "MOCK EXECUTE RESULT"
    
    async def fetchval(self, query, *args):
        # For simple version check
        if "SELECT version()" in query:
            return "PostgreSQL via Supabase API"
        logger.info(f"SQL Query fetchval (not executed): {query}")
        return None
        
    async def fetchrow(self, query, *args):
        # Mock for compatibility
        logger.info(f"SQL Query fetchrow (not executed): {query}")
        return None
        
    async def fetch(self, query, *args):
        # Mock for compatibility
        logger.info(f"SQL Query fetch (not executed): {query}")
        return []

@asynccontextmanager
async def database_connect(create_db: bool = False) -> AsyncGenerator[MockPool, None]:
    """Connect to the database using Supabase REST API.
    
    Args:
        create_db: Ignored parameter (kept for compatibility)
        
    Yields:
        A mock connection pool that redirects to SupabaseClient
    """
    logger.info("Connecting to database %s", DB_URL)
    try:
        # Create a Supabase client instead of direct PostgreSQL connection
        supabase_client = SupabaseClient()
        pool = MockPool(supabase_client)
        yield pool
    except Exception as e:
        logger.error(f"Error creating Supabase client: {e}")
        raise


async def init_db():
    """Initialize the database schema.
    
    Note: This function doesn't do anything via REST API.
    You must manually create tables in Supabase dashboard.
    """
    logger.warning("Database schema must be created manually in Supabase dashboard")
    logger.info("See the supabase_init_db.py script for the SQL commands to run")


async def check_db_connection() -> bool:
    """Check if the database connection works using Supabase API.
    
    Returns:
        True if the connection was successful, False otherwise.
    """
    try:
        # Create Supabase client and test connection
        client = SupabaseClient()
        
        # Test Supabase API connection
        response = await client.test_connection()
        if response:
            logger.info("Connected to Supabase API successfully")
            return True
        else:
            logger.error("Failed to connect to Supabase API")
            return False
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        return False


if __name__ == "__main__":
    """Run the database initialization script."""
    asyncio.run(init_db()) 