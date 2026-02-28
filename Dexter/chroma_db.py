from __future__ import annotations

from typing import Optional
import os

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction


def get_chroma_client(persist_dir: Optional[str] = None) -> chromadb.Client:
    """Return a configured Chroma client.

    - If `persist_dir` is provided or `CHROMA_PERSIST_DIR` env var is set,
      a `PersistentClient` is returned (disk-backed).
    - Otherwise an in-memory `Client` is returned.
    """
    path = persist_dir or os.environ.get("CHROMA_PERSIST_DIR")
    if path:
        return chromadb.PersistentClient(path=path)
    return chromadb.Client()


def get_openai_embedding_function(model_name: str = "text-embedding-3-small") -> OpenAIEmbeddingFunction:
    """Helper to create an OpenAI embedding function (uses OPENAI_API_KEY).
    """
    return OpenAIEmbeddingFunction(model_name=model_name)


def get_or_create_collection(client: chromadb.Client, name: str, embedding_function: Optional[OpenAIEmbeddingFunction] = None):
    """Get or create a Chroma collection with a default OpenAI embedding function.
    """
    if embedding_function is None:
        embedding_function = get_openai_embedding_function()
    return client.get_or_create_collection(name=name, embedding_function=embedding_function)


def add_embeddings_with_metadata(
    collection,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict] = None
):
    """Add documents to a collection with optional metadata.
    
    Args:
        collection: Chroma collection
        ids: Unique identifiers for each document
        documents: Text documents to embed
        metadatas: List of metadata dictionaries (one per document)
    """
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas or [{}] * len(documents)
        )
    # future uses enhancement
    """
    We could use this to specify which chapter we are reading from
    results = collection.query(
    query_texts=["search query"],
    where={"source": "file1.txt"}  # Filter by metadata
    
    """


def add_to_database(
    collection_name: str,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict] = None,
    persist_dir: Optional[str] = None,
    embedding_model: str = "text-embedding-3-small"
):
    """Add documents to an existing database collection in one call.
    
    Args:
        collection_name: Name of the collection to add to
        ids: Unique identifiers for each document
        documents: Text documents to embed
        metadatas: List of metadata dictionaries (one per document)
        persist_dir: Path to persistent database (if None, uses env var or in-memory)
        embedding_model: OpenAI embedding model to use
    """
    client = get_chroma_client(persist_dir)
    embedding_function = get_openai_embedding_function(embedding_model)
    collection = get_or_create_collection(client, collection_name, embedding_function)
    add_embeddings_with_metadata(collection, ids, documents, metadatas)


def query_collection(
    collection,
    query_text: str,
    chapter: Optional[str] = None,
    top_k: int = 5
) -> dict:
    """Query a Chroma collection with optional chapter filtering.
    
    Args:
        collection: Chroma collection to query
        query_text: The search query text
        chapter: Optional chapter to filter by (filters metadata['chapter'])
        top_k: Number of top results to return (default: 5)
    
    Returns:
        Dictionary with query results including:
        - ids: Document IDs
        - documents: Document content
        - metadatas: Document metadata (chapter, section, subsection)
        - distances: Distance scores
    """
    where_filter = None
    if chapter:
        where_filter = {"chapter": chapter}
    
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        where=where_filter
    )
    
    return results


def query_textbook(
    collection_name: str,
    query_text: str,
    chapter: Optional[str] = None,
    top_k: int = 5,
    persist_dir: Optional[str] = None
) -> dict:
    """Query the textbook database with optional chapter filtering.
    
    Convenience function that handles client/collection setup.
    
    Args:
        collection_name: Name of the collection to query (e.g., "chapter-1-functions")
        query_text: The search query text
        chapter: Optional chapter to filter results by
        top_k: Number of top results to return (default: 5)
        persist_dir: Path to persistent database (if None, uses env var or in-memory)
    
    Returns:
        Query results with ids, documents, metadatas, and distances
    
    Example:
        results = query_textbook(
            collection_name="chapter-1-functions",
            query_text="How do derivatives work?",
            chapter="Chapter 1: Derivatives",
            top_k=3
        )
    """
    client = get_chroma_client(persist_dir)
    collection = get_or_create_collection(client, collection_name)
    return query_collection(collection, query_text, chapter, top_k)
    
