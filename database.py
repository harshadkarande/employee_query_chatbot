
from sqlalchemy import text
import json 

def insert_document_chunks(
    engine,
    document_id,
    chunks,
    embeddings
):

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks and embeddings must match"
        )

    query = text("""
        INSERT INTO document_chunks (
            document_id,
            chunk_index,
            content,
            metadata,
            embedding
        )
        VALUES (
            :document_id,
            :chunk_index,
            :content,
            CAST(:metadata AS JSONB),
            CAST(:embedding AS VECTOR)
        )
        ON CONFLICT (document_id, chunk_index)
        DO UPDATE SET

            content = EXCLUDED.content,

            metadata = EXCLUDED.metadata,

            embedding = EXCLUDED.embedding
    """)

    records = []

    for chunk, embedding in zip(chunks, embeddings):

        records.append({
            "document_id": str(document_id),

            "chunk_index": chunk.metadata["chunk_index"],

            "content": chunk.page_content,

            "metadata": json.dumps(
                chunk.metadata,
                ensure_ascii=False
            ),

            "embedding": str(embedding.tolist())

        })

    with engine.begin() as connection:

        connection.execute(query, records)

    print(
        f"Successfully stored {len(records)} chunks "
        f"for document ID: {document_id}"
    )