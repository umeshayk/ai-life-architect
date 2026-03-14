import logging
import re

import requests

from app.core.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


def _clean_lines(response_text: str) -> list[str]:
    suggestions: list[str] = []
    for raw_line in (response_text or '').splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r'^[-*\\u2022]+\\s*', '', line)
        line = re.sub(r'^\\d+[.):-]?\\s*', '', line)
        line = line.strip(' .,:;')
        if line:
            suggestions.append(line)
    return suggestions


def generate_list(prompt: str, timeout: int = 25) -> list[str]:
    response = requests.post(
        settings.ollama_url,
        json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    response.raise_for_status()
    return _clean_lines((response.json() or {}).get('response', ''))


def generate_topic_expansion(prompt: str, timeout: int = 25) -> list[str]:
    return generate_list(prompt, timeout=timeout)
