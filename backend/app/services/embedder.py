"""OpenAI embedding service with batching and exponential backoff."""

import asyncio
import logging

import openai
from fastapi import HTTPException

from app.config import get_settings
from app.models.errors import ErrorCode

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def _get_client() -> openai.AsyncOpenAI:
    settings = get_settings()
    return openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def embed_chunks(
    texts: list[str],
    model: str | None = None,
) -> list[list[float]]:
    """
    Embed a list of texts using OpenAI embeddings.
    Splits into batches of <= BATCH_SIZE.
    Retries up to 3 times on RateLimitError with exponential backoff.
    """
    if model is None:
        model = get_settings().EMBEDDING_MODEL

    client = _get_client()
    all_embeddings: list[list[float]] = []

    batches = [texts[i : i + BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
    logger.debug(f"Embedding {len(texts)} texts in {len(batches)} batch(es)")

    for batch_i, batch in enumerate(batches):
        embedding_batch = await _embed_batch_with_retry(
            client, batch, model, batch_i, len(batches)
        )
        all_embeddings.extend(embedding_batch)

    return all_embeddings


async def _embed_batch_with_retry(
    client: openai.AsyncOpenAI,
    batch: list[str],
    model: str,
    batch_i: int,
    total_batches: int,
) -> list[list[float]]:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.embeddings.create(input=batch, model=model)
            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]

        except openai.RateLimitError as exc:
            wait_time = 2**attempt
            if attempt < max_retries - 1:
                logger.warning(
                    f"Embedding rate limit hit (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Embedding rate limit exceeded after {max_retries} retries")
                raise HTTPException(
                    status_code=502,
                    detail={
                        "error_code": ErrorCode.EMBEDDING_RATE_LIMIT,
                        "message": (
                            "Embedding API rate limit exceeded. "
                            "Please wait a moment and try again."
                        ),
                    },
                ) from exc

        except (openai.APIConnectionError, openai.APIStatusError) as exc:
            logger.error(f"Embedding API unavailable: {exc}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error_code": ErrorCode.EMBEDDING_UNAVAILABLE,
                    "message": f"Embedding service unavailable: {exc}",
                },
            ) from exc

    # Should never reach here
    raise HTTPException(
        status_code=503,
        detail={
            "error_code": ErrorCode.EMBEDDING_UNAVAILABLE,
            "message": "Embedding service failed after retries",
        },
    )


async def embed_query(
    text: str,
    model: str | None = None,
) -> list[float]:
    """Embed a single query string."""
    results = await embed_chunks([text], model=model)
    return results[0]
