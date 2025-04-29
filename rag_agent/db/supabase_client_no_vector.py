"""Client for interacting with the Supabase database via REST API (without pgvector)."""
import os
import logging
import json
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseClientNoVector:
    """Client for interacting with the PDF RAG database through Supabase REST API.
    This version works with the alternative schema without pgvector, storing embeddings as JSON.
    """
    
    def __init__(self):
        """Initialize the client with Supabase API credentials."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.headers = {
            "apikey": self.supabase_anon_key,
            "Authorization": f"Bearer {self.supabase_anon_key}",
            "Content-Type": "application/json"
        }
    
    async def add_document(self, title: str, filename: str, total_pages: int) -> int:
        """Add a document to the database.
        
        Args:
            title: The title of the document.
            filename: The filename of the document.
            total_pages: The total number of pages in the document.
            
        Returns:
            The ID of the added document.
        """
        endpoint = f"{self.supabase_url}/rest/v1/documents"
        
        payload = {
            "title": title,
            "filename": filename,
            "total_pages": total_pages
        }
        
        response = requests.post(
            endpoint,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 201:
            document = response.json()
            document_id = document.get("id")
            logger.info(f"Added document {title} with ID {document_id}")
            return document_id
        
        # Check if document already exists by unique filename constraint
        if response.status_code == 409:  # Conflict
            query_endpoint = f"{self.supabase_url}/rest/v1/documents?filename=eq.{filename}&select=id"
            query_response = requests.get(query_endpoint, headers=self.headers)
            
            if query_response.status_code == 200 and query_response.json():
                document_id = query_response.json()[0].get("id")
                logger.info(f"Document {title} already exists with ID {document_id}")
                return document_id
        
        logger.error(f"Failed to add document: {response.text}")
        raise Exception(f"Failed to add document: {response.text}")
    
    async def add_chunk(self, document_id: int, page_number: int, 
                      chunk_index: int, content: str, embedding: List[float]) -> int:
        """Add a chunk to the database.
        
        Args:
            document_id: The ID of the document.
            page_number: The page number.
            chunk_index: The chunk index.
            content: The content of the chunk.
            embedding: The embedding of the chunk.
            
        Returns:
            The ID of the added chunk.
        """
        endpoint = f"{self.supabase_url}/rest/v1/chunks"
        
        # Store embedding as JSON instead of vector
        payload = {
            "document_id": document_id,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "content": content,
            "embedding_json": embedding  # Store as JSON
        }
        
        response = requests.post(
            endpoint,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 201:
            chunk = response.json()
            chunk_id = chunk.get("id")
            return chunk_id
        
        logger.error(f"Failed to add chunk: {response.text}")
        raise Exception(f"Failed to add chunk: {response.text}")
    
    async def search_similar_chunks(self, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for chunks with similar content (text-based search).
        
        Since we don't have pgvector, we'll use text search as a fallback.
        
        Args:
            embedding: The query embedding (ignored in this implementation).
            limit: The maximum number of results to return.
            
        Returns:
            A list of chunks found via text search.
        """
        # We can't do vector similarity search without pgvector
        # Instead, we could implement a text search endpoint or use a custom RPC
        
        # For now, just return the most recent chunks as a fallback
        endpoint = f"{self.supabase_url}/rest/v1/chunks?order=created_at.desc&limit={limit}"
        
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        
        logger.error(f"Failed to search chunks: {response.text}")
        raise Exception(f"Failed to search chunks: {response.text}")
    
    async def get_document(self, document_id: int) -> Dict[str, Any]:
        """Get a document by ID.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            The document.
        """
        endpoint = f"{self.supabase_url}/rest/v1/documents?id=eq.{document_id}"
        
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code == 200 and response.json():
            return response.json()[0]
        
        logger.error(f"Failed to get document: {response.text}")
        raise Exception(f"Failed to get document: {response.text}")
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents.
        
        Returns:
            A list of documents.
        """
        endpoint = f"{self.supabase_url}/rest/v1/documents?select=*"
        
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        
        logger.error(f"Failed to get documents: {response.text}")
        raise Exception(f"Failed to get documents: {response.text}")
    
    async def get_chunks_by_document(self, document_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a document.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            A list of chunks.
        """
        endpoint = f"{self.supabase_url}/rest/v1/chunks?document_id=eq.{document_id}&select=*"
        
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        
        logger.error(f"Failed to get chunks: {response.text}")
        raise Exception(f"Failed to get chunks: {response.text}")

# Create an instance of the client
supabase_client_no_vector = SupabaseClientNoVector() 