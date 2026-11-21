
from functools import lru_cache

from sentence_transformers import SentenceTransformer


# ==========================================
# 1. MODEL CONFIGURATION
# ==========================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384


# ==========================================
# 2. LOAD EMBEDDING MODEL
# ==========================================

@lru_cache(maxsize=1)
def load_embedding_model():

    model = SentenceTransformer(MODEL_NAME)

    print(f"Embedding model loaded: {MODEL_NAME}")

    return model


# ==========================================
# 3. GENERATE EMBEDDINGS
# ==========================================

def generate_embeddings(chunks):

    if not chunks:
        return []

    model = load_embedding_model()

    # Extract text from LangChain Document objects
    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    # Generate embeddings in batches
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    print(f"Total embeddings generated: {len(embeddings)}")

    print(f"Embedding dimensions: {embeddings.shape[1]}")

    return embeddings
