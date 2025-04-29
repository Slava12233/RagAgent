"""Main entry point for the PDF RAG agent."""
import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path
from openai import AsyncOpenAI

from rag_agent.pdf.processor import PDFProcessor
from rag_agent.db.client import DBClient
from rag_agent.db.schema import check_db_connection
from rag_agent.db.check_tables import check_supabase_tables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_pdfs(paths: list[str]) -> list[int]:
    """Process PDF files and store them in the database.
    
    Args:
        paths: List of paths to PDF files or directories.
        
    Returns:
        List of document IDs for processed PDFs.
    """
    # Check database connection
    db_ok = await check_db_connection()
    if not db_ok:
        logger.error("Failed to connect to the database. Check your connection settings.")
        sys.exit(1)
    
    # Check if required tables exist
    tables_ok = await check_supabase_tables()
    if not tables_ok:
        logger.error("Required database tables are missing. Please run the SQL commands shown above in the Supabase dashboard.")
        logger.error("Then try again after creating the tables.")
        sys.exit(1)
    
    # Initialize OpenAI client
    openai_client = AsyncOpenAI()
    
    # Initialize database client
    db_client = DBClient(openai_client)
    
    # Initialize PDF processor
    processor = PDFProcessor(db_client=db_client, openai_client=openai_client)
    
    # Process all PDFs
    document_ids = []
    for path in paths:
        path_obj = Path(path)
        
        if not path_obj.exists():
            logger.error(f"Path does not exist: {path}")
            continue
        
        try:
            if path_obj.is_file() and path_obj.suffix.lower() == '.pdf':
                logger.info(f"Processing file: {path}")
                doc_id = await processor.process_pdf(str(path_obj))
                document_ids.append(doc_id)
                logger.info(f"Successfully processed PDF with document ID: {doc_id}")
            elif path_obj.is_dir():
                logger.info(f"Processing directory: {path}")
                dir_ids = await processor.process_directory(str(path_obj))
                document_ids.extend(dir_ids)
                logger.info(f"Successfully processed {len(dir_ids)} PDFs from directory")
            else:
                logger.warning(f"Skipping non-PDF file: {path}")
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")
    
    return document_ids

async def list_documents():
    """List all documents in the database."""
    # Check database connection
    db_ok = await check_db_connection()
    if not db_ok:
        logger.error("Failed to connect to the database. Check your connection settings.")
        sys.exit(1)
    
    # Check if required tables exist
    tables_ok = await check_supabase_tables()
    if not tables_ok:
        logger.error("Required database tables are missing. Please run the SQL commands shown above in the Supabase dashboard.")
        logger.error("Then try again after creating the tables.")
        sys.exit(1)
    
    # Initialize clients
    openai_client = AsyncOpenAI()
    db_client = DBClient(openai_client)
    
    # Get document list
    documents = await db_client.list_documents()
    
    if not documents:
        print("No documents found in the database.")
        return
    
    print(f"Found {len(documents)} documents:")
    for doc in documents:
        print(f"  - ID: {doc['id']}, Title: {doc['title']}")
        print(f"    Pages: {doc['total_pages']}, Chunks: {doc['chunk_count']}")
        print(f"    Added: {doc['created_at'].strftime('%Y-%m-%d %H:%M')}")
        print()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PDF RAG Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process PDF files")
    process_parser.add_argument("paths", nargs="+", help="Paths to PDF files or directories")
    
    # List command
    subparsers.add_parser("list", help="List all documents in the database")
    
    # Add setup command
    subparsers.add_parser("check-tables", help="Check if required tables exist in Supabase")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "process":
        document_ids = asyncio.run(process_pdfs(args.paths))
        print(f"Successfully processed {len(document_ids)} PDFs")
    elif args.command == "list":
        asyncio.run(list_documents())
    elif args.command == "check-tables":
        asyncio.run(check_supabase_tables())
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 