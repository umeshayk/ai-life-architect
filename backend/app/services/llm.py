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
            f"Topics: {', '.join(content_topic.topic.name for content_topic in match.item.content_topics if content_topic.topic) or 'None'}\n"
            f"Similarity: {match.similarity:.0%}\n"
            f"Summary: {match.item.summary or 'No summary'}\n"
            f"Content: {match.item.content[:1500]}"
        )
        for index, match in enumerate(matches, start=1)
    )


def build_mentor_context_block(mentor_context: dict | None) -> str:
    if not mentor_context:
        return "No higher-level knowledge insights available."

    projects = mentor_context.get("projects") or []
    strategies = mentor_context.get("strategies") or []
    weekly_plan = mentor_context.get("weekly_plan") or []
    forecast = mentor_context.get("forecast") or []

    project_lines = [
        f"- {project['name']}: {project['progress']}% complete, next step: {project.get('next_step') or 'None'}"
        for project in projects[:3]
    ] or ["- None"]
    strategy_lines = [
        f"- {strategy['domain']}: " + ", ".join(
            f"{step['topic']} ({'done' if step['completed'] else 'next'})" for step in strategy["path"][:5]
        )
        for strategy in strategies[:3]
    ] or ["- None"]
    plan_lines = [
        f"- {plan['domain']}: {plan['action']} because {plan['reason']}"
        for plan in weekly_plan[:3]
    ] or ["- None"]
    forecast_lines = [
        f"- {entry['domain']}: {entry['confidence']}% confidence, {entry['estimated_mastery_months']} month estimate"
        for entry in forecast[:3]
    ] or ["- None"]

    return (
        "Topic Intelligence:\n"
        f"- Dominant Topic: {mentor_context.get('dominant_topic') or 'None'}\n"
        f"- Top Topics: {', '.join(mentor_context.get('top_topics') or []) or 'None'}\n"
        f"- Emerging Topics: {', '.join(mentor_context.get('emerging_topics') or []) or 'None'}\n"
        f"- Knowledge Gaps: {', '.join(mentor_context.get('knowledge_gaps') or []) or 'None'}\n"
        f"- Suggested Exploration: {', '.join(mentor_context.get('suggested_topics') or []) or 'None'}\n\n"
        "Project Intelligence:\n"
        + "\n".join(project_lines)
        + "\n\nLearning Strategy:\n"
        + "\n".join(strategy_lines)
        + "\n\nWeekly Action Plan:\n"
        + "\n".join(plan_lines)
        + "\n\nForecast:\n"
        + "\n".join(forecast_lines)
    )


def ask_ollama(question: str, matches: list[SearchMatch], mentor_context: dict | None = None) -> str:
    context = build_context_block(matches)
    intelligence = build_mentor_context_block(mentor_context)
    prompt = (
        "You are a grounded personal knowledge mentor for a user's saved knowledge base.\n"
        "Answer only from the provided saved knowledge and generated knowledge insights.\n"
        "Do not invent topics, projects, or progress that are not in the context.\n"
        "If the answer is not supported by the context, say: "
        "'I could not verify that from your saved knowledge.'\n"
        "Do not hallucinate. Keep the answer concise, practical, and mentor-like.\n"
        "When useful, recommend the next concrete step.\n\n"
        f"User Knowledge Context:\n{context or 'No matching knowledge found.'}\n\n"
        f"{intelligence}\n\n"
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
