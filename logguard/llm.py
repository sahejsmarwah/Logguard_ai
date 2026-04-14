"""
logguard/llm.py
---------------
Groq LLM client with retry/backoff.
Model: llama-3.3-70b-versatile (fast, cheap, very capable).
"""
import os
import time
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError(
        "❌ GROQ_API_KEY is missing!\n"
        "Create a .env file in the project root (or export the variable):\n"
        "  GROQ_API_KEY=gsk_..."
    )

client = Groq(api_key=api_key)
logger = logging.getLogger("logguard")

_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_MAX_RETRIES = 3
_RETRY_DELAY = 2.0  # seconds


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = _DEFAULT_MODEL,
    json_mode: bool = False,
) -> str:
    """
    Call the Groq LLM with automatic retry on transient errors.

    Args:
        system_prompt: The system / role prompt.
        user_prompt:   The user message.
        model:         Groq model ID.
        json_mode:     If True, requests structured JSON output.

    Returns:
        The LLM's text response.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    kwargs = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "model": model,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as exc:
            last_error = exc
            if attempt < _MAX_RETRIES:
                logger.warning(
                    f"⚠️ LLM call failed (attempt {attempt}/{_MAX_RETRIES}): {exc} — retrying in {_RETRY_DELAY}s"
                )
                time.sleep(_RETRY_DELAY)
            else:
                logger.error(f"❌ LLM call failed after {_MAX_RETRIES} attempts: {exc}")

    raise RuntimeError(f"LLM call failed after {_MAX_RETRIES} retries: {last_error}") from last_error
