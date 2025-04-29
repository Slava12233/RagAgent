"""Pytest configuration for the PDF RAG agent tests."""
import os
import pytest
from unittest.mock import patch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set environment variables for testing if not already set
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:54320/pdf_rag_test"


@pytest.fixture(autouse=True)
def mock_asyncpg_connect():
    """Mock asyncpg.connect for all tests."""
    # This prevents actual database connections during testing
    with patch("asyncpg.connect") as mock_connect:
        yield mock_connect 