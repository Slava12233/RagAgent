"""Tests for the RAG agent."""
import os
import asyncio
from unittest.mock import MagicMock, patch

import pytest
from openai import AsyncOpenAI
from pydantic_ai.agent import Agent
from pydantic_ai import RunContext

from rag_agent.agent.rag import RagAgent, RagDeps
from rag_agent.db.client import DBClient


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock(spec=AsyncOpenAI)
    mock_embeddings = MagicMock()
    mock_client.embeddings.create = mock_embeddings
    return mock_client


@pytest.fixture
def mock_db_client(mock_openai_client):
    """Mock database client for testing."""
    mock_client = MagicMock(spec=DBClient)
    mock_client.openai_client = mock_openai_client
    return mock_client


@pytest.mark.asyncio
async def test_retrieve_with_results(mock_openai_client, mock_db_client):
    """Test retrieve tool with results."""
    # Setup
    chunks = [
        {
            "chunk_id": 1,
            "document_id": 1,
            "document_title": "Test Document",
            "page_number": 1,
            "content": "This is a test chunk.",
            "similarity": 0.9
        }
    ]
    mock_db_client.retrieve_chunks.return_value = chunks
    
    # Create agent instance with mocked dependencies
    agent = RagAgent()
    
    # Create context with mocked dependencies
    deps = RagDeps(openai=mock_openai_client, db_client=mock_db_client)
    context = RunContext(deps=deps)
    
    # Call retrieve
    result = await agent.retrieve(context, "test query")
    
    # Assertions
    mock_db_client.retrieve_chunks.assert_called_once_with("test query", limit=5)
    assert "Test Document" in result
    assert "Page: 1" in result
    assert "This is a test chunk." in result


@pytest.mark.asyncio
async def test_retrieve_no_results(mock_openai_client, mock_db_client):
    """Test retrieve tool with no results."""
    # Setup
    mock_db_client.retrieve_chunks.return_value = []
    
    # Create agent instance with mocked dependencies
    agent = RagAgent()
    
    # Create context with mocked dependencies
    deps = RagDeps(openai=mock_openai_client, db_client=mock_db_client)
    context = RunContext(deps=deps)
    
    # Call retrieve
    result = await agent.retrieve(context, "test query")
    
    # Assertions
    mock_db_client.retrieve_chunks.assert_called_once_with("test query", limit=5)
    assert "No relevant documents found" in result


@pytest.mark.asyncio
async def test_answer_question(mock_openai_client, mock_db_client):
    """Test answer_question method."""
    # Setup
    agent = RagAgent()
    
    # Mock the agent.run method
    agent.agent = MagicMock(spec=Agent)
    mock_response = MagicMock()
    mock_response.output = "This is a test answer."
    agent.agent.run.return_value = mock_response
    
    # Call answer_question
    result = await agent.answer_question("test question")
    
    # Assertions
    assert agent.agent.run.called
    assert result == "This is a test answer."


@pytest.mark.asyncio
async def test_list_documents(mock_openai_client, mock_db_client):
    """Test list_documents method."""
    # Setup
    documents = [
        {
            "id": 1,
            "title": "Test Document",
            "filename": "test.pdf",
            "total_pages": 10,
            "created_at": "2023-01-01",
            "chunk_count": 20
        }
    ]
    mock_db_client.list_documents.return_value = documents
    
    # Create agent instance with mocked dependencies
    agent = RagAgent()
    agent.db_client = mock_db_client
    
    # Call list_documents
    result = await agent.list_documents()
    
    # Assertions
    mock_db_client.list_documents.assert_called_once()
    assert result == documents 