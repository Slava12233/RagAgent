"""PDF processing utilities for the RAG agent."""
import os
import logging
from pathlib import Path
from typing import Dict, List, Generator, Tuple

import fitz  # PyMuPDF
from openai import AsyncOpenAI

from rag_agent.db.client import DBClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_CHUNK_SIZE = 1000  # Maximum characters per chunk
OVERLAP = 200  # Overlap between chunks in characters


class PDFProcessor:
    """PDF document processor for text extraction and chunking."""
    
    def __init__(self, db_client: DBClient = None, openai_client: AsyncOpenAI = None):
        """Initialize the PDF processor.
        
        Args:
            db_client: Database client for storing documents and chunks.
            openai_client: OpenAI API client for generating embeddings.
        """
        self.openai_client = openai_client or AsyncOpenAI()
        self.db_client = db_client or DBClient(self.openai_client)
    
    async def process_pdf(self, pdf_path: str) -> int:
        """Process a PDF document and store it in the database.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            The document ID.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            # Get document metadata
            title = pdf_path.stem  # Use filename as title if no title in metadata
            if doc.metadata and doc.metadata.get("title"):
                title = doc.metadata["title"]
                
            # Add document to database
            document_id = await self.db_client.add_document(
                title=title,
                filename=str(pdf_path),
                total_pages=len(doc)
            )
            
            # Process each page
            for page_num, page in enumerate(doc):
                logger.info(f"Processing page {page_num + 1}/{len(doc)} of {title}")
                
                # Extract text from page
                text = page.get_text()
                
                # Skip empty pages
                if not text.strip():
                    continue
                
                # Chunk the page text
                for chunk_idx, chunk in enumerate(self._chunk_text(text)):
                    if not chunk.strip():
                        continue
                        
                    # Add chunk to database
                    await self.db_client.add_chunk(
                        document_id=document_id,
                        page_number=page_num + 1,  # 1-indexed
                        chunk_index=chunk_idx,
                        content=chunk
                    )
            
            logger.info(f"Completed processing {title} with {len(doc)} pages")
            return document_id
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise
            
    def _chunk_text(self, text: str) -> Generator[str, None, None]:
        """Split text into overlapping chunks.
        
        Args:
            text: The text to chunk.
            
        Yields:
            Text chunks of appropriate size.
        """
        if not text:
            return
            
        # Simple chunking by character count with overlap
        start = 0
        while start < len(text):
            end = min(start + MAX_CHUNK_SIZE, len(text))
            
            # Adjust end to avoid splitting in the middle of a word or sentence
            if end < len(text):
                # Try to find a period followed by space
                period_pos = text.rfind(". ", start, end)
                if period_pos > start + MAX_CHUNK_SIZE // 2:
                    end = period_pos + 1
                else:
                    # Try to find a newline
                    newline_pos = text.rfind("\n", start, end)
                    if newline_pos > start + MAX_CHUNK_SIZE // 2:
                        end = newline_pos + 1
                    else:
                        # Try to find a space
                        space_pos = text.rfind(" ", start, end)
                        if space_pos > start + MAX_CHUNK_SIZE // 2:
                            end = space_pos
            
            # Yield the chunk
            yield text[start:end].strip()
            
            # Move start for next chunk with overlap
            start = max(start + MAX_CHUNK_SIZE - OVERLAP, end - OVERLAP)
    
    async def process_directory(self, directory_path: str) -> List[int]:
        """Process all PDF files in a directory.
        
        Args:
            directory_path: Path to the directory containing PDF files.
            
        Returns:
            List of document IDs for processed PDFs.
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise NotADirectoryError(f"Directory not found: {directory}")
            
        document_ids = []
        for pdf_file in directory.glob("*.pdf"):
            try:
                doc_id = await self.process_pdf(str(pdf_file))
                document_ids.append(doc_id)
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
        
        return document_ids 