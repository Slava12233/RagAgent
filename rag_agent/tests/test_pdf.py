"""Tests for the PDF processor."""
import os
import asyncio
from unittest.mock import MagicMock, patch, mock_open

import pytest
import fitz

from rag_agent.pdf.processor import PDFProcessor
from rag_agent.db.client import DBClient


@pytest.fixture
def mock_db_client():
    """Mock database client for testing."""
    mock_client = MagicMock(spec=DBClient)
    return mock_client


@pytest.fixture
def mock_pdf_document():
    """Mock PDF document for testing."""
    mock_doc = MagicMock(spec=fitz.Document)
    # Mock metadata
    mock_doc.metadata = {"title": "Test PDF"}
    # Mock document length
    mock_doc.__len__.return_value = 2
    
    # Mock pages
    page1 = MagicMock()
    page1.get_text.return_value = "This is page 1 content."
    
    page2 = MagicMock()
    page2.get_text.return_value = "This is page 2 content."
    
    mock_doc.__iter__.return_value = [page1, page2]
    
    return mock_doc


@pytest.mark.asyncio
async def test_process_pdf(mock_db_client, mock_pdf_document):
    """Test processing a PDF file."""
    # Setup
    processor = PDFProcessor(db_client=mock_db_client)
    
    # Mock DB client methods
    mock_db_client.add_document.return_value = 1  # Return document ID 1
    mock_db_client.add_chunk.return_value = 1  # Return chunk ID 1
    
    # Mock fitz.open
    with patch('fitz.open', return_value=mock_pdf_document):
        # Mock os.path.exists to return True
        with patch('os.path.exists', return_value=True):
            # Call process_pdf
            result = await processor.process_pdf("test.pdf")
    
    # Assertions
    assert result == 1  # Should return document ID 1
    mock_db_client.add_document.assert_called_once()
    # Should call add_chunk twice (once for each page)
    assert mock_db_client.add_chunk.call_count == 2


@pytest.mark.asyncio
async def test_process_directory(mock_db_client):
    """Test processing a directory of PDFs."""
    # Setup
    processor = PDFProcessor(db_client=mock_db_client)
    
    # Mock Path.glob to return some PDF files
    pdf_files = ["file1.pdf", "file2.pdf"]
    
    # Mock processor.process_pdf to return document IDs
    processor.process_pdf = MagicMock()
    processor.process_pdf.side_effect = [1, 2]  # Return IDs 1 and 2
    
    # Mock os.path.exists and isdir to return True
    with patch('os.path.exists', return_value=True):
        with patch('os.path.isdir', return_value=True):
            with patch('pathlib.Path.glob', return_value=pdf_files):
                # Call process_directory
                result = await processor.process_directory("test_dir")
    
    # Assertions
    assert result == [1, 2]  # Should return list of document IDs
    assert processor.process_pdf.call_count == 2  # Should call process_pdf twice


def test_chunk_text():
    """Test the text chunking function."""
    # Setup
    processor = PDFProcessor()
    
    # Test with a simple text
    text = "This is a test text that should be chunked into smaller pieces. " * 20
    
    # Call _chunk_text
    chunks = list(processor._chunk_text(text))
    
    # Assertions
    assert len(chunks) > 1  # Should create at least 2 chunks
    for chunk in chunks:
        assert len(chunk) <= 1000  # Each chunk should be <= MAX_CHUNK_SIZE
    
    # Test with empty text
    assert list(processor._chunk_text("")) == [] 