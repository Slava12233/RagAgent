"""Tests for the database client."""
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
import asyncpg
from openai import AsyncOpenAI

from rag_agent.db.client import DBClient


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock(spec=AsyncOpenAI)
    # Mock embeddings.create method
    mock_embeddings = AsyncMock()
    mock_embeddings.return_value.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    mock_client.embeddings.create = mock_embeddings
    return mock_client


@pytest.fixture
def mock_pool():
    """Mock asyncpg connection pool."""
    pool = MagicMock(spec=asyncpg.Pool)
    conn = AsyncMock(spec=asyncpg.Connection)
    transaction = AsyncMock()
    
    # Setup conn.transaction to return transaction context manager
    conn.transaction.return_value.__aenter__.return_value = transaction
    conn.transaction.return_value.__aexit__.return_value = None
    
    # Setup pool.acquire to return conn context manager
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None
    
    return pool, conn


@pytest.mark.asyncio
async def test_add_document(mock_openai_client, mock_pool):
    """Test adding a document."""
    # Setup
    pool, conn = mock_pool
    conn.fetchval.return_value = 1  # Return document ID 1
    
    with patch('rag_agent.db.schema.database_connect') as mock_db_connect:
        # Setup database_connect to return pool context manager
        mock_db_connect.return_value.__aenter__.return_value = pool
        mock_db_connect.return_value.__aexit__.return_value = None
        
        # Create client and call add_document
        client = DBClient(mock_openai_client)
        result = await client.add_document("Test Document", "test.pdf", 10)
    
    # Assertions
    assert result == 1  # Should return document ID 1
    conn.fetchval.assert_called_once()
    assert "INSERT INTO documents" in conn.fetchval.call_args[0][0]


@pytest.mark.asyncio
async def test_add_document_exists(mock_openai_client, mock_pool):
    """Test adding a document that already exists."""
    # Setup
    pool, conn = mock_pool
    
    # Simulate unique violation on first call, then return ID on second call
    conn.fetchval.side_effect = [
        asyncpg.UniqueViolationError("duplicate key value"),
        1  # Return document ID 1
    ]
    
    with patch('rag_agent.db.schema.database_connect') as mock_db_connect:
        # Setup database_connect to return pool context manager
        mock_db_connect.return_value.__aenter__.return_value = pool
        mock_db_connect.return_value.__aexit__.return_value = None
        
        # Create client and call add_document
        client = DBClient(mock_openai_client)
        result = await client.add_document("Test Document", "test.pdf", 10)
    
    # Assertions
    assert result == 1  # Should return document ID 1
    assert conn.fetchval.call_count == 2
    assert "SELECT id FROM documents" in conn.fetchval.call_args[0][0]


@pytest.mark.asyncio
async def test_add_chunk(mock_openai_client, mock_pool):
    """Test adding a chunk."""
    # Setup
    pool, conn = mock_pool
    conn.fetchval.return_value = 1  # Return chunk ID 1
    
    with patch('rag_agent.db.schema.database_connect') as mock_db_connect:
        # Setup database_connect to return pool context manager
        mock_db_connect.return_value.__aenter__.return_value = pool
        mock_db_connect.return_value.__aexit__.return_value = None
        
        # Create client and call add_chunk
        client = DBClient(mock_openai_client)
        result = await client.add_chunk(1, 1, 1, "Test content")
    
    # Assertions
    assert result == 1  # Should return chunk ID 1
    assert mock_openai_client.embeddings.create.called
    conn.fetchval.assert_called_once()
    assert "INSERT INTO chunks" in conn.fetchval.call_args[0][0]


@pytest.mark.asyncio
async def test_retrieve_chunks(mock_openai_client, mock_pool):
    """Test retrieving chunks."""
    # Setup
    pool, conn = mock_pool
    mock_rows = [
        {
            "chunk_id": 1,
            "document_id": 1,
            "document_title": "Test Document",
            "page_number": 1,
            "content": "Test content",
            "similarity": 0.9
        }
    ]
    conn.fetch.return_value = mock_rows
    
    with patch('rag_agent.db.schema.database_connect') as mock_db_connect:
        # Setup database_connect to return pool context manager
        mock_db_connect.return_value.__aenter__.return_value = pool
        mock_db_connect.return_value.__aexit__.return_value = None
        
        # Create client and call retrieve_chunks
        client = DBClient(mock_openai_client)
        result = await client.retrieve_chunks("test query", 5)
    
    # Assertions
    assert len(result) == 1
    assert result[0]["document_title"] == "Test Document"
    assert mock_openai_client.embeddings.create.called
    conn.fetch.assert_called_once()
    assert "SELECT" in conn.fetch.call_args[0][0]
    assert "ORDER BY" in conn.fetch.call_args[0][0]


@pytest.mark.asyncio
async def test_list_documents(mock_openai_client, mock_pool):
    """Test listing documents."""
    # Setup
    pool, conn = mock_pool
    mock_rows = [
        {
            "id": 1,
            "title": "Test Document",
            "filename": "test.pdf",
            "total_pages": 10,
            "created_at": "2023-01-01",
            "chunk_count": 20
        }
    ]
    conn.fetch.return_value = mock_rows
    
    with patch('rag_agent.db.schema.database_connect') as mock_db_connect:
        # Setup database_connect to return pool context manager
        mock_db_connect.return_value.__aenter__.return_value = pool
        mock_db_connect.return_value.__aexit__.return_value = None
        
        # Create client and call list_documents
        client = DBClient(mock_openai_client)
        result = await client.list_documents()
    
    # Assertions
    assert len(result) == 1
    assert result[0]["title"] == "Test Document"
    conn.fetch.assert_called_once()
    assert "SELECT" in conn.fetch.call_args[0][0]
    assert "FROM documents" in conn.fetch.call_args[0][0] 