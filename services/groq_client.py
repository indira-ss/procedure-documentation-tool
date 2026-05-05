import os
import time
import logging
from groq import Groq

# ── Logging setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ── Client init ────────────────────────────────────────────────
# Reads GROQ_API_KEY from .env automatically
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"


def call_groq(
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1000,
    retries: int = 3
) -> str | None:
    """
    Send a prompt to Groq and return the response text.
    Returns None if all retries fail (caller must handle fallback).

    temperature:
        0.3 = factual / structured JSON  (use for reports, describe)
        0.7 = creative / varied          (use for recommendations)
    """
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Groq call attempt {attempt}/{retries}")

            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise technical documentation assistant. "
                            "Always respond with valid JSON only. "
                            "Never include markdown, code fences, or explanation text."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content.strip()

            if not content:
                raise ValueError("Groq returned empty content")

            logger.info("Groq call succeeded")
            return content

        except Exception as e:
            wait = 2 ** (attempt - 1)  # 1s, 2s, 4s
            logger.error(f"Groq attempt {attempt} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    logger.error("All Groq retries exhausted. Returning None.")
    return None