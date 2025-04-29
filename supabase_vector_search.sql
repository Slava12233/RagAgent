-- Create function for vector similarity search
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