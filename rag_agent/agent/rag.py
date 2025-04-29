"""RAG agent implementation using PydanticAI."""
import os
import logging
from dataclasses import dataclass
from typing import List, Dict, Any

import pydantic_core
from openai import AsyncOpenAI
from pydantic_ai import RunContext
from pydantic_ai.agent import Agent

from rag_agent.db.client import DBClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System prompt for better RAG responses
SYSTEM_PROMPT = """
You are a helpful assistant that answers questions based on the provided documents.
When answering questions:
1. Only use information from the retrieved document chunks
2. If the retrieved chunks don't contain the answer, say "I don't have enough information to answer this question"
3. Cite the source document and page number when providing information
4. Be concise and to the point

The user has provided PDF documents, and you are here to answer questions about their content.
"""


@dataclass
class RagDeps:
    """Dependencies for the RAG agent."""
    openai: AsyncOpenAI
    db_client: DBClient


class RagAgent:
    """RAG agent for answering questions about documents."""
    
    def __init__(self, model_name: str = "openai:gpt-4o"):
        """Initialize the RAG agent.
        
        Args:
            model_name: The LLM model to use.
        """
        self.openai_client = AsyncOpenAI()
        self.db_client = DBClient(self.openai_client)
        
        # Initialize the agent with the retrieval tool
        self.agent = Agent(
            model_name,
            deps_type=RagDeps,
            system_prompt=SYSTEM_PROMPT
        )
        
        # Register the retrieve tool
        self.agent.tool(self.retrieve)
    
    async def retrieve(self, context: RunContext[RagDeps], search_query: str) -> str:
        """Retrieve document chunks based on a search query.
        
        Args:
            context: The call context.
            search_query: The search query.
            
        Returns:
            Formatted document chunks.
        """
        logger.info(f"Retrieving documents for query: {search_query}")
        
        chunks = await context.deps.db_client.retrieve_chunks(search_query, limit=5)
        
        if not chunks:
            return "No relevant documents found for this query."
        
        results = []
        for chunk in chunks:
            try:
                # Use get method with a default value to avoid KeyError
                doc_title = chunk.get('document_title', 'Unknown Document')
                page_num = chunk.get('page_number', 0)
                similarity = chunk.get('similarity', 0.0)
                content = chunk.get('content', 'No content available')
                
                results.append(
                    f"# Document: {doc_title}\n"
                    f"Page: {page_num}\n"
                    f"Similarity: {similarity:.2f}\n\n"
                    f"{content}\n"
                )
            except Exception as e:
                logger.error(f"Error formatting chunk: {e}")
                # Add basic information about the chunk if we can't format it properly
                results.append(f"# Error retrieving complete document information: {str(e)}\n")
        
        return "\n\n".join(results)
    
    async def answer_question(self, question: str) -> str:
        """Answer a question using the RAG agent.
        
        Args:
            question: The question to answer.
            
        Returns:
            The agent's response.
        """
        logger.info(f"Answering question: {question}")
        
        deps = RagDeps(
            openai=self.openai_client,
            db_client=self.db_client
        )
        
        answer = await self.agent.run(question, deps=deps)
        return answer.output
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the database.
        
        Returns:
            List of documents.
        """
        return await self.db_client.list_documents()


if __name__ == "__main__":
    """Simple test for the RAG agent."""
    import asyncio
    
    async def test_agent():
        agent = RagAgent()
        answer = await agent.answer_question("What are the key features of the system?")
        print(answer)
    
    asyncio.run(test_agent()) 