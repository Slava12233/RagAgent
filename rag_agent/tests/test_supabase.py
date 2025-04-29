"""Tests for Supabase connection and API functionality."""
import os
import pytest
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase connection details
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Test headers
headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"  # This is important for Supabase to return the created object
}

def test_supabase_connection():
    """Test that we can connect to the Supabase REST API."""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/",
        headers=headers
    )
    
    assert response.status_code == 200, f"Failed to connect to Supabase: {response.text}"

def test_documents_table_exists():
    """Test that the documents table exists."""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/documents?limit=1",
        headers=headers
    )
    
    # 200 if table exists, 404 if it doesn't
    assert response.status_code in (200, 404), f"Unexpected response: {response.status_code}, {response.text}"
    
    if response.status_code == 404:
        pytest.skip("Documents table does not exist yet. Run the initialization script first.")

def test_chunks_table_exists():
    """Test that the chunks table exists."""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/chunks?limit=1",
        headers=headers
    )
    
    # 200 if table exists, 404 if it doesn't
    assert response.status_code in (200, 404), f"Unexpected response: {response.status_code}, {response.text}"
    
    if response.status_code == 404:
        pytest.skip("Chunks table does not exist yet. Run the initialization script first.")

def test_pgvector_extension():
    """Test that the pgvector extension is available.
    
    This is an indirect test since we can't directly query for extensions via REST API.
    If the chunks table was created with a vector column, we can assume pgvector is enabled.
    """
    # Skip this test if the chunks table doesn't exist
    test_chunks_table_exists()
    
    # Try to insert a document and a chunk with embeddings
    # First, create a test document
    document_payload = {
        "title": "Test Document",
        "filename": "test_pgvector.pdf",
        "total_pages": 1
    }
    
    doc_response = requests.post(
        f"{SUPABASE_URL}/rest/v1/documents",
        headers=headers,
        json=document_payload
    )
    
    # If document exists, it will return 409 conflict
    assert doc_response.status_code in (201, 409), f"Failed to create test document: {doc_response.status_code}, {doc_response.text}"
    
    # Get the document ID
    document_id = None
    if doc_response.status_code == 201:
        # Document was created successfully, parse the ID from the response
        if doc_response.text and len(doc_response.text) > 0:
            try:
                document_id = doc_response.json()[0].get("id")
            except Exception:
                print(f"Could not parse document ID from response: {doc_response.text}")
    
    # If we couldn't get the ID from the creation response, try to fetch it
    if not document_id:
        # Document might already exist, get its ID
        get_doc_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/documents?filename=eq.test_pgvector.pdf&select=id",
            headers=headers
        )
        assert get_doc_response.status_code == 200, f"Failed to get test document: {get_doc_response.text}"
        try:
            document_id = get_doc_response.json()[0].get("id")
        except Exception:
            pytest.fail(f"Could not retrieve document ID: {get_doc_response.text}")
    
    assert document_id, "Failed to obtain document ID"
    print(f"Using document ID: {document_id}")
    
    # Now try to insert a chunk with an embedding
    # This will only work if pgvector is enabled
    chunk_payload = {
        "document_id": document_id,
        "page_number": 1,
        "chunk_index": 1,
        "content": "This is a test chunk to verify pgvector is working",
        "embedding": [0.1] * 1536  # Create a 1536-dimensional vector with all values 0.1
    }
    
    chunk_response = requests.post(
        f"{SUPABASE_URL}/rest/v1/chunks",
        headers=headers,
        json=chunk_payload
    )
    
    # Cleanup - delete the test document and its chunks (cascade delete)
    requests.delete(
        f"{SUPABASE_URL}/rest/v1/documents?id=eq.{document_id}",
        headers=headers
    )
    
    # Check if the chunk insertion was successful
    assert chunk_response.status_code in (201, 409), f"PgVector test failed: {chunk_response.status_code}, {chunk_response.text}"
    print("PgVector is correctly configured and working!") 