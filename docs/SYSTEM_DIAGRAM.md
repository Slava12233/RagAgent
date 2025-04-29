# PDF RAG Agent - System Process Diagrams

## Complete System Process Flow

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     PDF RAG AGENT SYSTEM FLOW                                      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                 ┌───────────────────────────┴────────────────────────────┐
                 │                                                        │
                 ▼                                                        ▼
┌────────────────────────────────────┐              ┌────────────────────────────────────┐
│       DOCUMENT PROCESSING FLOW     │              │         QUERY PROCESSING FLOW       │
└────────────────────────────────────┘              └────────────────────────────────────┘
                 │                                                        │
                 ▼                                                        ▼
┌────────────────────────────────────┐              ┌────────────────────────────────────┐
│ 1. User uploads PDF                │              │ 1. User inputs natural language    │
│    - UI (app.py)                   │              │    query                           │
│    - CLI (main.py process)         │              │    - Streamlit UI (app.py)         │
└────────────────┬───────────────────┘              └─────────────────┬──────────────────┘
                 │                                                     │
                 ▼                                                     ▼
┌────────────────────────────────────┐              ┌────────────────────────────────────┐
│ 2. Extract Text                    │              │ 2. Generate Query Embedding        │
│    - PyMuPDF/fitz                  │              │    - rag_agent/agent/rag.py        │
│    - processor.py                  │              │    - OpenAI text-embedding-3-small │
└────────────────┬───────────────────┘              └─────────────────┬──────────────────┘
                 │                                                     │
                 ▼                                                     ▼
┌────────────────────────────────────┐              ┌────────────────────────────────────┐
│ 3. Chunk Text                      │              │ 3. Vector Similarity Search        │
│    - processor.py                  │              │    - Supabase pgvector             │
│    - Page-based chunking           │              │    - search_chunks SQL function    │
│    - Context preservation          │              │    - supabase_client.py            │
└────────────────┬───────────────────┘              └─────────────────┬──────────────────┘
                 │                                                     │
                 ▼                                                     ▼
┌────────────────────────────────────┐              ┌────────────────────────────────────┐
│ 4. Generate Chunk Embeddings       │              │ 4. Format Retrieved Context        │
│    - client.py → add_chunk()       │              │    - rag_agent/agent/rag.py        │
│    - OpenAI text-embedding-3-small │              │    - Add document metadata         │
└────────────────┬───────────────────┘              └─────────────────┬──────────────────┘
                 │                                                     │
                 ▼                                                     ▼
┌────────────────────────────────────┐              ┌────────────────────────────────────┐
│ 5. Store in Database               │              │ 5. Generate Answer with LLM        │
│    - Supabase PostgreSQL           │              │    - OpenAI GPT-4o                 │
│    - Vector data type (pgvector)   │              │    - PydanticAI agent framework    │
│    - Documents & chunks tables     │              │    - System prompt with guidelines │
└────────────────────────────────────┘              └────────────────────────────────────┘
```

## Detailed Embedding Process

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               EMBEDDING GENERATION PROCESS                                         │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                 ┌───────────────────────────┴────────────────────────────┐
                 │                                                        │
                 ▼                                                        ▼
┌────────────────────────────────────┐              ┌────────────────────────────────────┐
│      DOCUMENT EMBEDDING FLOW       │              │        QUERY EMBEDDING FLOW        │
└────────────────────────────────────┘              └────────────────────────────────────┘
                 │                                                        │
                 ▼                                                        ▼
┌───────────────────────────────────┐               ┌───────────────────────────────────┐
│ File: rag_agent/db/client.py     │               │ File: rag_agent/agent/rag.py      │
│ Method: add_chunk()              │               │ Method: retrieve()                │
└─────────────────┬─────────────────┘               └─────────────────┬─────────────────┘
                  │                                                   │
                  ▼                                                   ▼
┌───────────────────────────────────┐               ┌───────────────────────────────────┐
│ Input: Text chunk from PDF        │               │ Input: User's natural language    │
│        processing                 │               │        query                      │
└─────────────────┬─────────────────┘               └─────────────────┬─────────────────┘
                  │                                                   │
                  ▼                                                   ▼
┌───────────────────────────────────┐               ┌───────────────────────────────────┐
│ API Call:                         │               │ API Call:                         │
│ openai_client.embeddings.create(  │               │ openai_client.embeddings.create(  │
│   input=content,                  │               │   input=search_query,             │
│   model="text-embedding-3-small"  │               │   model="text-embedding-3-small"  │
│ )                                 │               │ )                                 │
└─────────────────┬─────────────────┘               └─────────────────┬─────────────────┘
                  │                                                   │
                  ▼                                                   ▼
┌───────────────────────────────────┐               ┌───────────────────────────────────┐
│ Output: 1536-dimensional vector   │               │ Output: 1536-dimensional vector   │
└─────────────────┬─────────────────┘               └─────────────────┬─────────────────┘
                  │                                                   │
                  ▼                                                   ▼
┌───────────────────────────────────┐               ┌───────────────────────────────────┐
│ Storage: PostgreSQL with pgvector │               │ Usage: Vector similarity search   │
│          extension                │               │        using <=> operator         │
└───────────────────────────────────┘               └───────────────────────────────────┘
```

## Database Structure for Embeddings

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  DATABASE SCHEMA DIAGRAM                                           │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────┐              ┌────────────────────────────────────┐
│              documents             │              │                chunks               │
├────────────────────────────────────┤              ├────────────────────────────────────┤
│ id: serial PRIMARY KEY             │◄─────────────┤ document_id: integer REFERENCES    │
│ title: text                        │              │                 documents(id)       │
│ filename: text                     │              │ page_number: integer               │
│ total_pages: integer               │              │ chunk_index: integer               │
│ created_at: timestamp              │              │ content: text                      │
└────────────────────────────────────┘              │ embedding: vector(1536)            │
                                                    │ created_at: timestamp              │
                                                    └────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 VECTOR SEARCH FUNCTION                                             │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘

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
    document_title text,    ◄─── Join with documents title
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
        1 - (c.embedding <=> query_embedding) AS similarity  ◄─── Vector similarity calculation
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    ORDER BY c.embedding <=> query_embedding  ◄─── Sort by vector distance
    LIMIT match_count;
END;
$$;
```

## Vector Similarity Search Visualization

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             VECTOR SIMILARITY SEARCH CONCEPT                                       │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘

                                       Query: "What is artificial intelligence?"
                                                        │
                                                        │
                                                        ▼
                                      ┌─────────────────────────────────┐
                                      │      Query Embedding Vector     │
                                      │      [0.021, -0.345, ... ]      │
                                      └──────────────────┬──────────────┘
                                                        │
                                                        │ Vector comparison
                                                        ▼
                 ┌─────────────────────────────────────────────────────────────────────┐
                 │                    Vector space of document chunks                   │
                 │                                                                     │
                 │                 Chunk 1      ●                                      │
                 │                                                                     │
                 │                                         ● Chunk 4                   │
                 │                                                                     │
                 │      ● Chunk 2                                                      │
                 │                                                     ● Chunk 5       │
                 │                          ●    ★ Query                              │
                 │                       Chunk 3                                       │
                 │                                                                     │
                 │                               Nearest                               │
                 │                                │                                    │
                 │                                │                                    │
                 │                                ▼                                    │
                 │                               Chunk 3                              │
                 │                               Chunk 5                              │
                 │                               Chunk 1                              │
                 └─────────────────────────────────────────────────────────────────────┘
``` 