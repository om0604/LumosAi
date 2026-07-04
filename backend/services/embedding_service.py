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

# Embedding dimension (Matryoshka truncation to match pgvector schema)
_EMBEDDING_DIMENSIONS = 384

# Retry configuration for transient failures
_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 2  # seconds
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _post_with_retry(headers: dict, payload: dict) -> requests.Response:
    """
    POST to Jina API with retry logic for transient failures.
    Retries up to _MAX_RETRIES times with exponential backoff.
    Does NOT retry authentication errors (401, 403).
    """
    last_exception = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.post(_JINA_API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code not in _RETRYABLE_STATUS_CODES:
                response.raise_for_status()
                return response

            # Retryable HTTP error
            logger.warning(
                f"Jina API returned HTTP {response.status_code} (attempt {attempt}/{_MAX_RETRIES})"
            )
            last_exception = RuntimeError(
                f"Jina API HTTP {response.status_code}: {response.text[:200]}"
            )

        except requests.exceptions.Timeout as exc:
            logger.warning(f"Jina API request timed out (attempt {attempt}/{_MAX_RETRIES})")
            last_exception = exc
        except requests.exceptions.ConnectionError as exc:
            logger.warning(f"Jina API connection error (attempt {attempt}/{_MAX_RETRIES})")
            last_exception = exc
        except requests.exceptions.HTTPError as exc:
            # Non-retryable HTTP error (e.g. 401, 403, 400)
            logger.error(f"Jina API non-retryable HTTP error: {exc}")
            raise RuntimeError(f"Jina AI API error: {exc}") from exc

        if attempt < _MAX_RETRIES:
            backoff = _RETRY_BACKOFF_BASE ** (attempt - 1)
            logger.info(f"Retrying in {backoff}s...")
            time.sleep(backoff)

    raise RuntimeError(f"Jina AI API failed after {_MAX_RETRIES} attempts: {last_exception}") from last_exception


def embed(texts: List[str], task: str = "retrieval.passage") -> List[List[float]]:
    """
    Generate embeddings for a list of texts using the Jina AI embedding API.

    Args:
        texts: One or more strings to embed. Batched internally in groups of 100.
        task:  Jina task hint.
               Use "retrieval.passage" for document chunks (indexing).
               Use "retrieval.query"   for user query embeddings (search).

    Returns:
        A list of embedding vectors, one per input text.
        Each vector is a List[float] with exactly 384 dimensions.

    Raises:
        RuntimeError: If the Jina API fails after retries or returns invalid data.
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
            "dimensions": _EMBEDDING_DIMENSIONS,
        }

        logger.info(f"Calling Jina API — batch {i // batch_size + 1}, texts={len(batch_texts)}")
        t_start_batch = time.time()

        response = _post_with_retry(headers, payload)

        elapsed_batch = time.time() - t_start_batch
        logger.info(f"Received embedding response — duration={elapsed_batch:.2f}s")

        try:
            body = response.json()
            if "data" not in body or not isinstance(body["data"], list):
                raise ValueError("Response missing 'data' array.")

            # Sort by index to guarantee order matches the input list
            items = sorted(body["data"], key=lambda x: x["index"])

            if len(items) != len(batch_texts):
                raise ValueError(f"Expected {len(batch_texts)} embeddings, got {len(items)}.")

            batch_embeddings = [item["embedding"] for item in items]

            # Validate dimension
            if not batch_embeddings or len(batch_embeddings[0]) != _EMBEDDING_DIMENSIONS:
                actual_dim = len(batch_embeddings[0]) if batch_embeddings else "unknown"
                raise ValueError(
                    f"Expected {_EMBEDDING_DIMENSIONS}-dim embeddings, got {actual_dim}."
                )

        except (KeyError, ValueError, TypeError) as exc:
            logger.error(f"Failed to parse Jina AI response: {exc}")
            raise RuntimeError(f"Jina AI response parse error: {exc}") from exc

        logger.info(f"Embeddings generated — count={len(batch_embeddings)}")
        all_embeddings.extend(batch_embeddings)

    elapsed_total = time.time() - t_start_total
    logger.info(
        f"Embedding completed — model={model}, num_embeddings={len(all_embeddings)}, "
        f"total_duration={elapsed_total:.2f}s"
    )

    return all_embeddings
