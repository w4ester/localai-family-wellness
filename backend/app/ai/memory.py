# ./backend/app/ai/memory.py
"""
Functions for interacting with the AI's memory stored in the PGVector database.
Handles embedding generation, storage, and retrieval of memories.
"""
import logging
import json
from typing import List, Dict, Optional, Any
from uuid import UUID

from psycopg_pool import AsyncConnectionPool
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
# You might need Document if formatting results differently
# from langchain_core.documents import Document

from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Constants ---
# Define connection string based on settings
CONNECTION_STRING = str(settings.DATABASE_URL)
COLLECTION_NAME = "ai_memory" # Matches the table name for AIMemory model

# --- Embedding Helper ---
# Cache the embedding model instance for efficiency
_embeddings_instance: Optional[OllamaEmbeddings] = None

def get_embeddings() -> OllamaEmbeddings:
    """Initializes and returns the Ollama embeddings model (cached)."""
    global _embeddings_instance
    if _embeddings_instance is None:
        logger.info(f"Initializing Ollama Embeddings model: {settings.OLLAMA_EMBEDDING_MODEL}")
        _embeddings_instance = OllamaEmbeddings(model=settings.OLLAMA_EMBEDDING_MODEL)
    return _embeddings_instance

async def generate_embedding(text: str) -> List[float]:
    """Generates an embedding for the given text using the configured model."""
    try:
        embeddings = get_embeddings()
        # Use aembed_query for async execution
        logger.debug(f"Generating embedding for text: '{text[:50]}...'")
        vector = await embeddings.aembed_query(text)
        logger.debug(f"Embedding generated successfully (dimension: {len(vector)}).")
        return vector
    except Exception as e:
        logger.error(f"Error generating embedding for text '{text[:50]}...': {e}", exc_info=True)
        raise RuntimeError(f"Failed to generate embedding: {e}") from e

# --- Vector Store Helper ---
# Cache the vector store instance (uses the embedding function)
_vector_store_instance: Optional[PGVector] = None

def get_vector_store() -> PGVector:
    """Initializes and returns the PGVector store instance (cached)."""
    global _vector_store_instance
    if _vector_store_instance is None:
        logger.info(f"Initializing PGVector store. Collection: {COLLECTION_NAME}")
        _vector_store_instance = PGVector(
            connection_string=CONNECTION_STRING,
            collection_name=COLLECTION_NAME,
            embedding_function=get_embeddings(), # Use cached embedding function
        )
        # Optional: Add pre_delete_collection=True if you want it to drop/recreate on init
    return _vector_store_instance


# --- Memory Interaction Functions ---

async def search_relevant_memories(
    query_text: str,
    user_id: UUID,
    family_id: UUID,
    k: int = 5,
    score_threshold: Optional[float] = None # Optional relevance threshold
) -> List[Dict]:
    """
    Searches the vector store for memories relevant to the query text,
    filtered by user and family.

    Args:
        query_text: The text to search for relevant memories.
        user_id: The ID of the user whose context is relevant.
        family_id: The ID of the family context.
        k: The maximum number of relevant memories to return.
        score_threshold: Optional minimum similarity score (depends on distance strategy).

    Returns:
        A list of relevant memory dictionaries including text, metadata, and score.
    """
    try:
        vector_store = get_vector_store()

        # NOTE: Filtering directly within PGVector's similarity search can be complex
        # and depends on the exact langchain-community version and PGVector setup.
        # The most reliable method is often to search broadly and filter afterward,
        # or use SQL functions if performance with large datasets becomes an issue.
        # We will filter *after* the search in this implementation for robustness.

        logger.debug(f"Performing vector similarity search for query: '{query_text[:50]}...' (k={k})")

        # Use async search method with score
        # Langchain's PGVector might use distance (lower is better) or similarity (higher is better)
        # Check documentation. Assuming similarity search where higher score is better for now.
        results_with_scores = await vector_store.asimilarity_search_with_relevance_scores(
            query=query_text,
            k=k * 3, # Fetch more results initially to allow for filtering
        )

        # Process results: filter by user/family and score threshold
        relevant_memories = []
        for doc, score in results_with_scores:
            metadata = doc.metadata or {}
            doc_user_id = metadata.get("user_id")
            doc_family_id = metadata.get("family_id")

            # Apply score threshold if provided
            if score_threshold is not None and score < score_threshold:
                continue

            # Apply user and family filtering
            if doc_user_id and str(doc_user_id) == str(user_id) and \
               doc_family_id and str(doc_family_id) == str(family_id):
                 relevant_memories.append({
                     "text": doc.page_content,
                     "metadata": metadata,
                     "score": score # Include the relevance score
                 })
                 logger.debug(f"Found relevant memory (Score: {score:.4f}): {doc.page_content[:100]}...")
                 if len(relevant_memories) >= k: # Stop once we have enough filtered results
                     break

        # Optional: Re-rank based on importance or recency from metadata if needed
        # Sort by score descending (higher is better) before returning
        relevant_memories.sort(key=lambda x: x['score'], reverse=True)

        return relevant_memories

    except Exception as e:
        logger.error(f"Error searching relevant memories for query '{query_text[:50]}...': {e}", exc_info=True)
        return [] # Return empty list on error


async def store_memory(
    pool: AsyncConnectionPool, # Pass the pool explicitly
    user_id: UUID,
    family_id: UUID,
    text: str,
    memory_type: str, # Use strings matching MemoryType enum values
    metadata: Optional[Dict] = None,
    importance: int = 1,
    source: Optional[str] = None
) -> None:
    """
    Generates an embedding and stores a new memory in the 'ai_memory' table.

    Args:
        pool: The database connection pool.
        user_id: The user associated with the memory.
        family_id: The family associated with the memory.
        text: The textual content of the memory.
        memory_type: The type string (e.g., 'conversation', 'insight').
        metadata: Optional JSON metadata.
        importance: Importance score.
        source: Source of the memory (e.g., 'user_chat', 'ai_summary').
    """
    if not text:
        logger.warning("Attempted to store empty memory text. Skipping.")
        return

    try:
        # 1. Generate Embedding
        embedding = await generate_embedding(text)

        # 2. Ensure metadata is serializable or None
        serializable_metadata = None
        if metadata is not None:
            try:
                # Test serialization and reload to ensure it's valid JSON
                json_str = json.dumps(metadata)
                serializable_metadata = json_str # Store the JSON string
            except TypeError as json_err:
                logger.warning(f"Metadata for memory is not JSON serializable: {json_err}. Storing metadata as None. Original metadata: {metadata}")
                serializable_metadata = None # Fallback to None if not serializable


        # 3. Insert into Database using connection from pool
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                # Note: Assumes AIMemory model table/column names match these
                # The 'embedding' column expects a list/vector compatible with pgvector INSERT syntax
                # psycopg correctly handles list of floats for vector type
                await cur.execute(
                    """
                    INSERT INTO ai_memory (user_id, family_id, text, memory_type, metadata, importance, source, embedding, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (
                        user_id,
                        family_id,
                        text,
                        memory_type, # Pass the string value of the enum
                        serializable_metadata, # Pass the JSON string or None
                        importance,
                        source,
                        embedding, # Pass the embedding vector (list of floats)
                    ),
                )
                # No explicit commit needed with 'async with pool.connection()' unless autocommit=False
                # await conn.commit()
                logger.info(f"Stored memory (type: {memory_type}) for user {user_id}: {text[:50]}...")

    except Exception as e:
        logger.error(f"Error storing memory for user {user_id}: {e}", exc_info=True)
        # Decide if error should be propagated or just logged/handled