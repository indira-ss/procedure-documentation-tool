"""
services/groq_client.py
"""

import os
import time
import logging
from groq import Groq, RateLimitError, APIStatusError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_DELAY = 1.5

def call_groq(prompt, temperature=0.3, max_tokens=1024):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY is not set")
        return None

    client = Groq(api_key=api_key)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Groq call attempt %d/%d", attempt, MAX_RETRIES)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except RateLimitError as e:
            logger.warning("Rate limit hit (attempt %d): %s", attempt, e)

        except APIStatusError as e:
            logger.error("API error (attempt %d): %s", attempt, e)
            if e.status_code and 400 <= e.status_code < 500:
                break

        except Exception as e:
            logger.error("Unexpected error (attempt %d): %s", attempt, e)

        if attempt < MAX_RETRIES:
            delay = BASE_DELAY * (2 ** (attempt - 1))
            time.sleep(delay)

    return None