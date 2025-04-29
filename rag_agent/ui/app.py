"""Streamlit UI for the PDF RAG agent."""

import os
import sys
import asyncio
import tempfile
import logging
import time
import json
import shutil
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

# Add the parent directory to Python path to fix module import
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
from dotenv import load_dotenv

from rag_agent.agent.rag import RagAgent
from rag_agent.pdf.processor import PDFProcessor
from rag_agent.db.schema import check_db_connection

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="PDF RAG Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    st.error("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
    st.stop()


# Helper function to run async functions in Streamlit
def run_async(func, *args, **kwargs):
    """Run an async function in Streamlit."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(func(*args, **kwargs))
    finally:
        loop.close()


# Helper function to safely delete files in Windows
def safe_remove_file(file_path, max_retries=3, retry_delay=0.5):
    """Safely remove a file with retries for Windows environments.
    
    Args:
        file_path: Path to the file to delete
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    for attempt in range(max_retries):
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
            return True
        except PermissionError as e:
            logger.warning(f"Failed to delete file (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Could not delete temporary file: {file_path}")
                return False


# Helper function to create a temporary PDF file for processing
def save_uploaded_file(uploaded_file):
    """Save an uploaded file to a more permanent location in the temp directory.
    
    Args:
        uploaded_file: The uploaded file from Streamlit
        
    Returns:
        Path to the saved file
    """
    # Create a temp directory for our app if it doesn't exist
    temp_dir = Path(tempfile.gettempdir()) / "rag_agent_pdfs"
    temp_dir.mkdir(exist_ok=True)
    
    # Create a file path with a unique name
    file_path = temp_dir / f"{uploaded_file.name}"
    
    # If file exists, add timestamp to make it unique
    if file_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = temp_dir / f"{Path(uploaded_file.name).stem}_{timestamp}{Path(uploaded_file.name).suffix}"
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    return str(file_path)


# Helper function to format document for display
def format_document_for_display(doc):
    """Format document data for display, handling various data types.
    
    Args:
        doc: The document data from the database
    
    Returns:
        A document dict with properly formatted fields
    """
    # Make a copy of the doc to avoid modifying the original
    formatted_doc = dict(doc)
    
    # Handle created_at field that might be a string or already a datetime
    if 'created_at' in formatted_doc:
        if isinstance(formatted_doc['created_at'], str):
            try:
                # Try to parse the date string to datetime object
                formatted_doc['created_at'] = datetime.fromisoformat(
                    formatted_doc['created_at'].replace('Z', '+00:00')
                )
            except (ValueError, TypeError) as e:
                # If parsing fails, use current time
                logger.warning(f"Failed to parse created_at date: {e}")
                formatted_doc['created_at'] = datetime.now()
    else:
        # If no created_at field, use current time
        formatted_doc['created_at'] = datetime.now()
    
    return formatted_doc


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "documents" not in st.session_state:
    st.session_state.documents = []

if "agent" not in st.session_state:
    try:
        st.session_state.agent = RagAgent()
    except Exception as e:
        st.error(f"Failed to initialize RAG Agent: {e}")
        st.stop()


# Check database connection
try:
    db_ok = run_async(check_db_connection)
    if not db_ok:
        st.error("Failed to connect to the database. Make sure Supabase is configured properly.")
        st.info("Run the SQL commands in supabase_init_db.py through the Supabase dashboard.")
        st.stop()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()


# Sidebar for document upload and document list
with st.sidebar:
    st.title("PDF Documents")
    
    # Upload new PDF documents
    uploaded_files = st.file_uploader(
        "Upload PDF documents", 
        accept_multiple_files=True,
        type=["pdf"]
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Validate file size (limit to 10MB)
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB in bytes
                st.error(f"File {uploaded_file.name} is too large. Maximum size is 10MB.")
                continue
            
            # Validate file type again (even though Streamlit does some validation)
            if not uploaded_file.name.lower().endswith('.pdf'):
                st.error(f"File {uploaded_file.name} is not a PDF. Please upload only PDF files.")
                continue
            
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    # Save the uploaded file to a more permanent location
                    file_path = save_uploaded_file(uploaded_file)
                    
                    # Process the PDF
                    processor = PDFProcessor(db_client=st.session_state.agent.db_client)
                    doc_id = run_async(processor.process_pdf, file_path)
                    st.success(f"Processed {uploaded_file.name}")
                    
                    # Delete the file after processing (we don't need to keep it)
                    try:
                        os.unlink(file_path)
                    except Exception as e:
                        logger.warning(f"Could not delete processed file {file_path}: {e}")
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {e}")
    
    # Refresh document list button
    if st.button("Refresh Document List"):
        with st.spinner("Refreshing document list..."):
            try:
                documents = run_async(st.session_state.agent.list_documents)
                # Format documents for display
                st.session_state.documents = [format_document_for_display(doc) for doc in documents]
            except Exception as e:
                st.error(f"Error loading documents: {e}")
                st.session_state.documents = []
    
    # Display document list
    if st.session_state.documents:
        st.write(f"Found {len(st.session_state.documents)} documents:")
        for doc in st.session_state.documents:
            try:
                expander = st.expander(f"{doc['title']} ({doc['total_pages']} pages)")
                expander.text(f"Filename: {doc['filename']}")
                expander.text(f"Chunks: {doc['chunk_count']}")
                expander.text(f"Added: {doc['created_at'].strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                st.error(f"Error displaying document: {e}")
    else:
        # Load documents on first run
        with st.spinner("Loading documents..."):
            try:
                documents = run_async(st.session_state.agent.list_documents)
                # Format documents for display
                st.session_state.documents = [format_document_for_display(doc) for doc in documents]
                if st.session_state.documents:
                    st.rerun()
            except Exception as e:
                st.error(f"Error loading documents: {e}")
                st.session_state.documents = []


# Main chat interface
st.title("PDF RAG Agent")
st.write("Ask questions about your PDF documents")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
prompt = st.chat_input("Ask a question about your documents")
if prompt:
    # Validate query length
    if len(prompt) > 500:
        st.error("Your question is too long. Please limit it to 500 characters.")
    elif len(prompt) < 3:
        st.error("Your question is too short. Please provide a more detailed question.")
    else:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = run_async(
                        st.session_state.agent.answer_question, 
                        prompt
                    )
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_message = f"Error generating response: {e}"
                    st.error(error_message)
                    
                    # Add more helpful information about possible fixes
                    if "document_title" in str(e).lower():
                        st.error("""
                        It looks like there's an issue with the document vector search function. 
                        
                        To fix this:
                        1. Go to your Supabase dashboard SQL Editor
                        2. Run the SQL from "supabase_vector_search.sql" which should include:
                        ```sql
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
                        ```
                        """)
                    
                    st.session_state.messages.append({"role": "assistant", "content": error_message})


# Footer
st.divider()
st.caption("PDF RAG Agent - Powered by PydanticAI") 