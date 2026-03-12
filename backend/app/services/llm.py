import logging

import requests

from app.core.config import get_settings
from app.services.retrieval import SearchMatch


logger = logging.getLogger(__name__)
settings = get_settings()


def build_context_block(matches: list[SearchMatch]) -> str:
    return "\n\n".join(
        (
            f"Source {index}\n"
            f"Title: {match.item.title}\n"
            f"Type: {match.item.type}\n"
            f"Similarity: {match.similarity:.0%}\n"
            f"Summary: {match.item.summary or 'No summary'}\n"
            f"Content: {match.item.content[:1500]}"
        )
        for index, match in enumerate(matches, start=1)
    )


def ask_ollama(question: str, matches: list[SearchMatch]) -> str:
    context = build_context_block(matches)
    prompt = (
        "You are a grounded assistant for a personal knowledge base.\n"
        "Answer only from the provided sources.\n"
        "If the answer is not supported by the sources, say: "
        "'I could not verify that from your saved knowledge.'\n"
        "Do not hallucinate. Keep the answer concise and practical.\n\n"
        f"Sources:\n{context or 'No matching knowledge found.'}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )
    try:
        response = requests.post(
            settings.ollama_url,
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip() or "Ollama returned an empty response."
    except Exception as exc:
        logger.warning("Ollama request failed: %s", exc)
        if not matches:
            return "I could not verify that from your saved knowledge."
        titles = ", ".join(match.item.title for match in matches[:3])
        return f"Ollama is unavailable. Closest saved sources: {titles}."
