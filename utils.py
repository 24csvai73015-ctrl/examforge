import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

OLLAMA_BASE_URL = "http://localhost:11434"


def get_available_ollama_models() -> list[str]:
    """Query local Ollama and return installed model names. Empty list if unreachable."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def get_llm_client(use_openai: bool, openai_key: str = "", openai_model: str = "gpt-4o-mini", ollama_model: str = "") -> tuple:
    """
    Returns (OpenAI-compatible client, model_name).

    - use_openai=True  → connects to OpenAI cloud using the provided key.
    - use_openai=False → connects to local Ollama server (no key needed).
    """
    if use_openai:
        if not openai_key:
            raise ValueError("Please enter a valid OpenAI API key in the sidebar.")
        client = OpenAI(api_key=openai_key)
        return client, openai_model
    else:
        client = OpenAI(
            api_key="ollama",
            base_url=f"{OLLAMA_BASE_URL}/v1"
        )
        return client, ollama_model
