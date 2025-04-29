"""Client for interacting with the Supabase database via REST API."""
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

class SupabaseClient:
    """Client for interacting with the PDF RAG database through Supabase REST API."""
    
    def __init__(self):
        """Initialize the client with Supabase API credentials."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        # Ensure trailing slash is removed from URL
        if self.supabase_url and self.supabase_url.endswith('/'):
            self.supabase_url = self.supabase_url[:-1]
            
        logger.info(f"Initializing Supabase client with URL: {self.supabase_url}")
        
        self.headers = {
            "apikey": self.supabase_anon_key,
            "Authorization": f"Bearer {self.supabase_anon_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"  # Ask Supabase to return the created object
        }
        
    async def test_connection(self) -> bool:
        """Test the connection to the Supabase API.
        
        Returns:
            True if the connection was successful, False otherwise.
        """
        try:
            endpoint = f"{self.supabase_url}/rest/v1/"
            logger.info(f"Testing connection to: {endpoint}")
            
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code in (200, 401):  # 401 is still a valid connection, just unauthorized
                logger.info("Successfully connected to Supabase API")
                return True
            else:
                logger.error(f"Failed to connect to Supabase API: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error testing Supabase connection: {e}")
            return False
    
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
        
        # Format the filename to be unique but shorter - use just the basename
        short_filename = os.path.basename(filename)
        
        # Create document payload
        payload = {
            "title": title,
            "filename": short_filename,
            "total_pages": total_pages
        }
        
        # Log full request details for debugging
        logger.info(f"Sending POST request to: {endpoint}")
        logger.info(f"Headers: {json.dumps({k: v for k, v in self.headers.items() if k not in ['Authorization', 'apikey']})}")
        logger.info(f"Payload: {json.dumps(payload)}")
        
        try:
            # Make the API request
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload
            )
            
            # Log response headers for debugging
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check if we have response content
            if response.content:
                logger.info(f"Response content length: {len(response.content)} bytes")
                logger.debug(f"Raw response: {response.content[:1000]}")  # Only log first 1000 chars
            else:
                logger.warning("Response has no content")
            
            # Try alternative endpoint if first attempt failed
            if response.status_code not in (200, 201) and not response.content:
                logger.info("Trying alternative endpoint format")
                alt_endpoint = f"{self.supabase_url}/rest/v1/documents"
                
                # Try with different Prefer header for handling created records
                alt_headers = self.headers.copy()
                alt_headers["Prefer"] = "return=minimal"
                
                response = requests.post(
                    alt_endpoint,
                    headers=alt_headers,
                    json=payload
                )
                logger.info(f"Alternative response status: {response.status_code}")
                
                if response.headers.get('Location'):
                    # Extract ID from Location header
                    location = response.headers.get('Location', '')
                    if location:
                        doc_id = location.split('=')[-1]
                        if doc_id.isdigit():
                            logger.info(f"Extracted document ID from Location header: {doc_id}")
                            return int(doc_id)
            
            # Process the response                
            if response.status_code in (200, 201):
                # Try to parse JSON response
                if response.content:
                    try:
                        data = response.json()
                        
                        # Handle the case where the response is a list
                        if isinstance(data, list) and len(data) > 0:
                            # Supabase sometimes returns a list with a single item
                            first_item = data[0]
                            logger.info(f"Response is a list, processing first item: {first_item}")
                            document_id = first_item.get("id")
                            if document_id:
                                logger.info(f"Added document {title} with ID {document_id}")
                                return document_id
                        elif isinstance(data, dict):
                            # Handle the case where response is a dictionary
                            document_id = data.get("id")
                            if document_id:
                                logger.info(f"Added document {title} with ID {document_id}")
                                return document_id
                        else:
                            logger.error(f"Unexpected response format: {type(data)}")
                            logger.error(f"Response content: {data}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse response as JSON: {e}, Response: {response.text}")
                else:
                    logger.error("Response has no content to parse")
            
            # If we couldn't get the ID from the direct response, check if document already exists by filename
            logger.info("Checking if document already exists by filename")
            check_endpoint = f"{self.supabase_url}/rest/v1/documents?filename=eq.{requests.utils.quote(short_filename)}&select=id"
            
            # Log check request for debugging
            logger.info(f"Sending GET request to: {check_endpoint}")
            
            check_response = requests.get(check_endpoint, headers=self.headers)
            
            # Log check response for debugging
            logger.info(f"Check response status: {check_response.status_code}")
            if check_response.content:
                logger.info(f"Check response content: {check_response.text[:1000]}")
            
            if check_response.status_code == 200 and check_response.content:
                try:
                    data = check_response.json()
                    if data and len(data) > 0:
                        document_id = data[0].get("id")
                        if document_id:
                            logger.info(f"Document {title} already exists with ID {document_id}")
                            return document_id
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse query response as JSON: {e}")
            
            # If we got here, something went wrong - try to diagnose
            error_msg = f"Failed to add document: Status {response.status_code}"
            
            # Check for specific error conditions
            if response.status_code == 401:
                error_msg += ", Unauthorized - check API key"
            elif response.status_code == 403:
                error_msg += ", Forbidden - check permissions"
            elif response.status_code == 404:
                error_msg += ", Not Found - check endpoint URL"
            elif response.status_code == 409:
                error_msg += ", Conflict - document may already exist"
            elif response.status_code >= 500:
                error_msg += ", Server Error - check Supabase status"
            
            logger.error(error_msg)
            raise ValueError(error_msg)
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise ValueError(f"Request to Supabase API failed: {e}")
    
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
        
        payload = {
            "document_id": document_id,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "content": content,
            "embedding": embedding
        }
        
        # Log request details (but not the full embedding)
        logger.info(f"Adding chunk for document_id={document_id}, page={page_number}, chunk={chunk_index}")
        logger.info(f"Sending POST request to: {endpoint}")
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload
            )
            
            # Log response details
            logger.info(f"Chunk response status: {response.status_code}")
            
            if response.status_code in (200, 201):
                if response.content:
                    try:
                        data = response.json()
                        
                        # Handle the case where the response is a list
                        if isinstance(data, list) and len(data) > 0:
                            # Supabase sometimes returns a list with a single item
                            first_item = data[0]
                            logger.info(f"Chunk response is a list, processing first item")
                            chunk_id = first_item.get("id")
                            if chunk_id:
                                logger.info(f"Added chunk ID {chunk_id} for document {document_id}, page {page_number}")
                                return chunk_id
                        elif isinstance(data, dict):
                            # Handle the case where response is a dictionary
                            chunk_id = data.get("id")
                            if chunk_id:
                                logger.info(f"Added chunk ID {chunk_id} for document {document_id}, page {page_number}")
                                return chunk_id
                        else:
                            logger.error(f"Unexpected chunk response format: {type(data)}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse chunk response as JSON: {e}, Response: {response.text}")
                        raise ValueError(f"Invalid JSON response from Supabase API: {response.text}")
                else:
                    logger.error("Chunk response has no content to parse")
                    
            # Try to query if the chunk exists already (in case of conflict)
            if response.status_code == 409:  # Conflict
                logger.warning(f"Conflict when adding chunk (may already exist)")
                query_endpoint = f"{self.supabase_url}/rest/v1/chunks?document_id=eq.{document_id}&page_number=eq.{page_number}&chunk_index=eq.{chunk_index}&select=id"
                
                logger.info(f"Checking if chunk already exists: {query_endpoint}")
                query_response = requests.get(query_endpoint, headers=self.headers)
                
                if query_response.status_code == 200 and query_response.content:
                    try:
                        data = query_response.json()
                        if data and len(data) > 0:
                            chunk_id = data[0].get("id")
                            if chunk_id:
                                logger.info(f"Found existing chunk ID {chunk_id}")
                                return chunk_id
                    except json.JSONDecodeError:
                        pass
            
            # If we got here, something went wrong
            error_msg = f"Failed to add chunk: Status {response.status_code}"
            
            # Check for specific error conditions
            if response.status_code == 401:
                error_msg += ", Unauthorized - check API key"
            elif response.status_code == 403:
                error_msg += ", Forbidden - check permissions"
            elif response.status_code == 404:
                error_msg += ", Not Found - check endpoint URL"
            elif response.status_code == 409:
                error_msg += ", Conflict - chunk may already exist with unique constraint violation"
            elif response.status_code >= 500:
                error_msg += ", Server Error - check Supabase status"
                
            if response.content:
                error_msg += f", Response: {response.text[:500]}"
                
            logger.error(error_msg)
            raise ValueError(error_msg)
        except requests.RequestException as e:
            logger.error(f"Request failed while adding chunk: {e}")
            raise ValueError(f"Request to Supabase API failed: {e}")
    
    async def search_similar_chunks(self, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for chunks with similar embeddings.
        
        Args:
            embedding: The query embedding.
            limit: The maximum number of results to return.
            
        Returns:
            A list of chunks with similar embeddings.
        """
        # Unfortunately, Supabase REST API doesn't directly support pgvector
        # operations like <-> (cosine distance). We would need to use a stored
        # procedure or RPC function for this.
        
        # This would be the endpoint if we had an RPC function named "search_chunks"
        endpoint = f"{self.supabase_url}/rest/v1/rpc/search_chunks"
        
        payload = {
            "query_embedding": embedding,
            "match_count": limit
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                try:
                    results = response.json()
                    # Enhance results with document title
                    enhanced_results = []
                    for chunk in results:
                        # Get the document to add title
                        doc_id = chunk.get('document_id')
                        if doc_id:
                            doc = await self.get_document(doc_id)
                            chunk['document_title'] = doc.get('title', 'Unknown Document')
                        else:
                            chunk['document_title'] = 'Unknown Document'
                        enhanced_results.append(chunk)
                    return enhanced_results
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse search response as JSON: {e}")
                    return []
            
            # The RPC function might not exist yet - this is expected initially
            if response.status_code == 404:
                logger.warning("Search RPC function not found. Vector search is not available.")
                return []
            
            logger.error(f"Failed to search chunks: Status {response.status_code}, Response: {response.text}")
            return []  # Return empty rather than failing
        except requests.RequestException as e:
            logger.error(f"Request failed during search: {e}")
            return []
    
    async def get_document(self, document_id: int) -> Dict[str, Any]:
        """Get a document by ID.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            The document.
        """
        endpoint = f"{self.supabase_url}/rest/v1/documents?id=eq.{document_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data and len(data) > 0:
                        return data[0]
                    else:
                        logger.warning(f"Document with ID {document_id} not found")
                        return {}
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse document response as JSON: {e}")
                    return {}
            
            logger.error(f"Failed to get document: Status {response.status_code}, Response: {response.text}")
            return {}
        except requests.RequestException as e:
            logger.error(f"Request failed while getting document: {e}")
            return {}
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents.
        
        Returns:
            A list of documents.
        """
        endpoint = f"{self.supabase_url}/rest/v1/documents?select=*"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse documents response as JSON: {e}")
                    return []
            
            logger.error(f"Failed to get documents: Status {response.status_code}, Response: {response.text}")
            return []
        except requests.RequestException as e:
            logger.error(f"Request failed while getting documents: {e}")
            return []
    
    async def get_chunks_by_document(self, document_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a document.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            A list of chunks.
        """
        endpoint = f"{self.supabase_url}/rest/v1/chunks?document_id=eq.{document_id}&select=*"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse chunks response as JSON: {e}")
                    return []
            
            logger.error(f"Failed to get chunks: Status {response.status_code}, Response: {response.text}")
            return []
        except requests.RequestException as e:
            logger.error(f"Request failed while getting chunks: {e}")
            return []

# Create an instance of the client
supabase_client = SupabaseClient() 