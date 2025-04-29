"""Database client for PDF RAG agent."""
import logging
from typing import Dict, List, Optional, Tuple, Any

import asyncpg
import pydantic_core
import numpy as np
from openai import AsyncOpenAI

from rag_agent.db.schema import database_connect
from rag_agent.db.supabase_client import supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DBClient:
    """Client for interacting with the PDF RAG database."""

    def __init__(self, openai_client: AsyncOpenAI = None):
        """Initialize the database client.
        
        Args:
            openai_client: OpenAI API client for generating embeddings.
        """
        self.openai_client = openai_client or AsyncOpenAI()
        self.supabase = supabase_client
        
    async def add_document(self, title: str, filename: str, total_pages: int) -> int:
        """Add a document to the database.
        
        Args:
            title: The document title.
            filename: The document filename.
            total_pages: The total number of pages in the document.
            
        Returns:
            The document ID.
        """
        try:
            # Debug logging
            logger.info(f"Adding document to database: {title}, {filename}, {total_pages} pages")
            
            # Use Supabase API client instead of direct database connection
            try:
                document_id = await self.supabase.add_document(title, filename, total_pages)
                logger.info("Added document %s with ID %s", title, document_id)
                return document_id
            except ValueError as ve:
                # Handle specific error - empty response
                if "JSON" in str(ve) and "empty" in str(ve).lower():
                    # Try querying by filename to see if document already exists
                    logger.warning("Empty JSON response when adding document. Checking if document already exists by filename...")
                    
                    # This is a workaround - if we got an empty response but the document might have been created,
                    # we can try to query for it by filename to get its ID
                    query_endpoint = f"{self.supabase.supabase_url}/rest/v1/documents?filename=eq.{filename}&select=id"
                    
                    try:
                        import requests
                        response = requests.get(query_endpoint, headers=self.supabase.headers)
                        if response.status_code == 200 and response.content:
                            import json
                            data = response.json()
                            if data and len(data) > 0:
                                document_id = data[0].get("id")
                                if document_id:
                                    logger.info(f"Found existing document with filename {filename}, ID: {document_id}")
                                    return document_id
                    except Exception as query_error:
                        logger.error(f"Error checking for existing document: {query_error}")
                        
                # Re-raise the error if we couldn't recover
                raise
        except Exception as e:
            logger.error("Failed to add document: %s", e)
            raise
    
    async def add_chunk(
        self, 
        document_id: int, 
        page_number: int, 
        chunk_index: int, 
        content: str,
        embedding: List[float] = None
    ) -> int:
        """Add a document chunk to the database.
        
        Args:
            document_id: The document ID.
            page_number: The page number.
            chunk_index: The chunk index within the page.
            content: The chunk text content.
            embedding: The precomputed embedding vector, if any.
            
        Returns:
            The chunk ID.
        """
        # Generate embedding if not provided
        if embedding is None:
            embedding_response = await self.openai_client.embeddings.create(
                input=content,
                model="text-embedding-3-small"
            )
            embedding = embedding_response.data[0].embedding
        
        try:
            # Use Supabase API client
            chunk_id = await self.supabase.add_chunk(
                document_id, 
                page_number, 
                chunk_index, 
                content, 
                embedding
            )
            return chunk_id
        except Exception as e:
            logger.error("Failed to add chunk: %s", e)
            raise
    
    async def retrieve_chunks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve document chunks based on a search query.
        
        Args:
            query: The search query.
            limit: The maximum number of results to retrieve.
            
        Returns:
            A list of document chunks with similarity scores.
        """
        # Generate query embedding
        embedding_response = await self.openai_client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        embedding = embedding_response.data[0].embedding
        
        try:
            # Use Supabase API client for vector search
            results = await self.supabase.search_similar_chunks(embedding, limit)
            
            # If we have results but they're missing document titles, try to add them
            if results and not all('document_title' in chunk for chunk in results):
                logger.info("Some chunks missing document_title, enriching data")
                await self.enrich_chunks_with_titles(results)
                
            return results
        except Exception as e:
            logger.error("Failed to retrieve chunks: %s", e)
            # Fallback to a basic implementation if Supabase RPC fails
            logger.warning("Vector search through Supabase RPC failed, no results returned")
            return []
    
    async def enrich_chunks_with_titles(self, chunks: List[Dict[str, Any]]) -> None:
        """Add document titles to chunks that are missing them.
        
        Args:
            chunks: List of chunk results from search
        """
        # Keep track of document IDs we've already fetched to avoid duplicate lookups
        document_cache = {}
        
        for chunk in chunks:
            doc_id = chunk.get('document_id')
            if not doc_id:
                chunk['document_title'] = 'Unknown Document'
                continue
            
            # Check if we've already fetched this document
            if doc_id in document_cache:
                chunk['document_title'] = document_cache[doc_id]
                continue
            
            # Fetch document information
            try:
                doc = await self.get_document_by_id(doc_id)
                if doc and 'title' in doc:
                    document_cache[doc_id] = doc['title']
                    chunk['document_title'] = doc['title']
                else:
                    chunk['document_title'] = f'Document #{doc_id}'
            except Exception as e:
                logger.error(f"Error fetching document {doc_id} for chunk: {e}")
                chunk['document_title'] = f'Document #{doc_id}'
    
    async def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a document by its ID.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The document data or None if not found.
        """
        try:
            # Use Supabase API client
            return await self.supabase.get_document(document_id)
        except Exception as e:
            logger.error("Failed to get document: %s", e)
            return None
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the database.
        
        Returns:
            A list of documents.
        """
        try:
            # Use Supabase API client
            documents = await self.supabase.get_all_documents()
            
            # Format the result similar to the original function
            result = []
            for doc in documents:
                # Get chunk count for this document
                chunks = await self.supabase.get_chunks_by_document(doc["id"])
                doc_with_count = {
                    "id": doc["id"],
                    "title": doc["title"],
                    "filename": doc["filename"],
                    "total_pages": doc["total_pages"],
                    "created_at": doc["created_at"],
                    "chunk_count": len(chunks)
                }
                result.append(doc_with_count)
            
            return result
        except Exception as e:
            logger.error("Failed to list documents: %s", e)
            return []
    
    async def delete_document(self, document_id: int) -> bool:
        """Delete a document and all its chunks.
        
        Args:
            document_id: The document ID.
            
        Returns:
            True if the document was deleted, False otherwise.
        """
        # This would need a new method in the SupabaseClient class
        # For now, we'll just log that this isn't implemented
        logger.error("delete_document not implemented for Supabase API")
        return False 