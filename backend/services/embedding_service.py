"""
Embedding service — wraps Jina AI's REST embedding API.

This is the ONLY place in the project that communicates with Jina AI.
All other modules must call embed() from here; nothing should import
the Jina SDK or make HTTP requests to Jina directly.
"""

import time
import logging
import requests
from typing import List

from config import config

logger = logging.getLogger(__name__)

# Jina REST endpoint — stable, no SDK required
_JINA_API_URL = "https://api.jina.ai/v1/embeddings"


def embed(texts: List[str], task: str = "retrieval.passage") -> List[List[float]]:
    """
    Generate embeddings for a list of texts using the Jina AI embedding API.

    Args:
        texts: One or more strings to embed. All are sent in a single request (batched internally).
        task:  Jina task hint.
               Use "retrieval.passage" for document chunks (indexing).
               Use "retrieval.query"   for user query embeddings (search).

    Returns:
        A list of embedding vectors, one per input text.
        Each vector is a List[float] compatible with pgvector (384 dimensions).

    Raises:
        RuntimeError: If the Jina API returns a non-200 response or
                      the response body cannot be parsed/validated.
        ValueError:   If `texts` is empty.
    """
    if not texts:
        raise ValueError("embed() received an empty list of texts.")

    model = config.JINA_EMBEDDING_MODEL
    batch_size = 100
    all_embeddings = []

    logger.info(
        f"Embedding request started — model={model}, task={task}, "
        f"num_texts={len(texts)}"
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.JINA_API_KEY}",
    }

    t_start_total = time.time()

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        payload = {
            "model": model,
            "input": batch_texts,
            "task": task,
            "dimensions": 384,
        }

        logger.info("Calling Jina API...")
        t_start_batch = time.time()
        
        try:
            response = requests.post(_JINA_API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error(f"Jina AI request failed with a network or HTTP error: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response body: {exc.response.text[:400]}")
            raise RuntimeError(f"Jina AI network/HTTP error: {exc}") from exc

        elapsed_batch = time.time() - t_start_batch
        logger.info(f"Received embedding response. Elapsed request time: {elapsed_batch:.2f}s")

        try:
            body = response.json()
            if "data" not in body or not isinstance(body["data"], list):
                 raise ValueError("Response missing 'data' array.")
            
            # Jina returns { "data": [ { "embedding": [...], "index": N }, ... ] }
            # Sort by index to guarantee order matches the input list.
            items = sorted(body["data"], key=lambda x: x["index"])
            
            if len(items) != len(batch_texts):
                 raise ValueError(f"Expected {len(batch_texts)} embeddings, got {len(items)}.")

            batch_embeddings = [item["embedding"] for item in items]
            
            # Simple validation to ensure it's a list of floats and correct dimension
            if not batch_embeddings or not isinstance(batch_embeddings[0], list) or len(batch_embeddings[0]) != 384:
                raise ValueError(f"Embedding format is invalid or dimension is not 384. Got dimension: {len(batch_embeddings[0]) if batch_embeddings else 'unknown'}")

        except (KeyError, ValueError) as exc:
            logger.error(f"Failed to parse Jina AI response or invalid format: {exc} — body: {response.text[:400]}")
            raise RuntimeError(f"Jina AI response parse error: {exc}") from exc
            
        logger.info(f"Number of embeddings generated: {len(batch_embeddings)}")
        all_embeddings.extend(batch_embeddings)

    elapsed_total = time.time() - t_start_total
    logger.info(
        f"Embedding completed — model={model}, num_embeddings={len(all_embeddings)}, "
        f"total_response_time={elapsed_total:.2f}s"
    )

    return all_embeddings
