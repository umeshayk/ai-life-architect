from sqlalchemy.orm import Session

from app.services.learning_path_service import LEARNING_PATHS, build_learning_paths


TOPIC_EXPLANATIONS = {
    "Embeddings": "Embeddings turn meaning into vectors so your systems can compare ideas instead of just matching keywords.",
    "Vector Databases": "Vector Databases are required for storing and retrieving embeddings efficiently at scale.",
    "Semantic Search": "Semantic Search lets you retrieve ideas by meaning, which is the foundation of modern AI knowledge systems.",
    "Hybrid Search": "Hybrid Search combines semantic and keyword retrieval so your results stay both relevant and precise.",
    "Retrieval Augmented Generation": "Retrieval Augmented Generation connects retrieval with LLM responses so answers stay grounded in your knowledge.",
    "Retrieval Optimization": "Retrieval Optimization improves ranking quality, relevance, and reliability as your system grows.",
    "LLM Systems": "LLM Systems combine retrieval, prompting, orchestration, and evaluation into complete AI applications.",
    "Mushroom Farming": "Mushroom Farming is a practical entry point into controlled cultivation and repeatable agricultural systems.",
    "Hydroponic Farming": "Hydroponic Farming teaches soilless growing systems and controlled nutrient delivery.",
    "Controlled Environment Agriculture": "Controlled Environment Agriculture connects cultivation with climate, sensor, and systems thinking.",
    "Farm Automation": "Farm Automation turns manual agriculture workflows into repeatable, monitored systems.",
    "Yield Optimization": "Yield Optimization helps you improve output, quality, and operational efficiency once the system is running.",
    "Knowledge Management": "Knowledge Management is the foundation for capturing, organizing, and reusing what you learn.",
    "Action Planning": "Action Planning turns stored knowledge into concrete execution and follow-through.",
    "Personal Knowledge Systems": "Personal Knowledge Systems connect capture, retrieval, and execution into a durable workflow.",
    "AI Knowledge Architect": "AI Knowledge Architect brings retrieval, structure, and automation together into an intelligent personal system.",
    "Real Estate": "Real Estate is the domain foundation for understanding properties, markets, and decision drivers.",
    "Property Trends": "Property Trends helps you interpret how the market is shifting over time.",
    "Real Estate Data Analytics": "Real Estate Data Analytics turns raw market data into practical decision support.",
}

QUESTION_PATTERNS = {
    "next": ["what should i learn next", "learn next", "next topic"],
    "why": ["why should i learn", "why learn", "why should i study", "why is"],
    "unlock": ["what skills does", "what skills will", "what does", "unlock"],
    "progress": ["how close am i", "how close", "progress", "completing"],
    "missing": ["what topics am i missing", "what am i missing", "missing topics"],
    "focus_path": ["which learning path should i focus on next", "which path should i focus on", "which learning path next"],
}


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


def _all_paths() -> list[dict[str, object]]:
    return LEARNING_PATHS


def _all_topics() -> dict[str, dict[str, str]]:
    topics: dict[str, dict[str, str]] = {}
    for path in _all_paths():
        for index, topic in enumerate(path["topics"]):
            topics[_normalize(topic)] = {
                "topic": topic,
                "domain": path["domain"],
                "path_name": path["path_name"],
                "index": index,
            }
    return topics


def _resolve_path(question: str, learning_paths: list[dict]) -> dict | None:
    normalized_question = _normalize(question)

    for path in learning_paths:
        if _normalize(path["path_name"]) in normalized_question:
            return path

    for path in learning_paths:
        if _normalize(path["domain"]) in normalized_question:
            return path

    return learning_paths[0] if learning_paths else None


def _resolve_topic(question: str) -> dict | None:
    normalized_question = _normalize(question)
    for key, topic in _all_topics().items():
        if key in normalized_question:
            return topic
    return None


def _find_path_by_name(learning_paths: list[dict], path_name: str | None) -> dict | None:
    if not path_name:
        return None
    normalized_name = _normalize(path_name)
    for path in learning_paths:
        if _normalize(path["path_name"]) == normalized_name:
            return path
    return None


def _find_path_for_topic(learning_paths: list[dict], topic_name: str | None, path_name: str | None = None) -> dict | None:
    if path_name:
        matched = _find_path_by_name(learning_paths, path_name)
        if matched:
            return matched
    if not topic_name:
        return None
    normalized_topic = _normalize(topic_name)
    for path in learning_paths:
        if any(_normalize(topic["topic"]) == normalized_topic for topic in path["topics"]):
            return path
    return None


def _path_progress(path: dict | None) -> dict | None:
    if not path:
        return None
    return {
        "covered_count": path["covered_count"],
        "total_count": path["total_count"],
        "progress_percent": path["progress_percent"],
    }


def _topic_why(topic_name: str) -> str:
    return TOPIC_EXPLANATIONS.get(topic_name, f"{topic_name} matters because it advances the next stage of this learning path.")


def _skills_unlocked(topic_name: str, path_name: str | None = None) -> list[str]:
    for path in _all_paths():
        if path_name and _normalize(path["path_name"]) != _normalize(path_name):
            continue
        topics = path["topics"]
        for index, topic in enumerate(topics):
            if _normalize(topic) == _normalize(topic_name):
                return topics[index + 1:index + 4]
    return []


def _topic_state_lookup(path: dict | None) -> dict[str, dict[str, str]]:
    if not path:
        return {}
    return {_normalize(topic["topic"]): topic for topic in path["topics"]}


def _recommended_topic_data(path: dict | None, current_topic: str | None = None) -> dict | None:
    if not path:
        return None

    topic_lookup = _topic_state_lookup(path)
    if current_topic and _normalize(current_topic) in topic_lookup:
        topics = path["topics"]
        current_index = next(
            (index for index, topic in enumerate(topics) if _normalize(topic["topic"]) == _normalize(current_topic)),
            None,
        )
        if current_index is not None:
            for topic in topics[current_index + 1:]:
                if topic["state"] != "covered":
                    return {**topic, "domain": path["domain"]}

    next_topic = path.get("next_topic")
    return {**next_topic} if next_topic else None


def _mentor_path_topics(path: dict | None, current_topic: str | None = None) -> list[dict[str, str]]:
    if not path:
        return []

    normalized_current = _normalize(current_topic) if current_topic else ""
    fallback_current = _normalize(path["next_topic"]["topic"]) if path.get("next_topic") and not normalized_current else normalized_current
    topics_payload: list[dict[str, str]] = []

    for topic in path["topics"]:
        normalized_topic = _normalize(topic["topic"])
        if topic["state"] == "covered":
            mentor_state = "covered"
        elif fallback_current and normalized_topic == fallback_current:
            mentor_state = "current"
        else:
            mentor_state = "missing"
        topics_payload.append({"topic": topic["topic"], "state": mentor_state})

    return topics_payload


def _remaining_topics(path: dict | None, current_topic: str | None = None) -> list[str]:
    if not path:
        return []

    normalized_current = _normalize(current_topic) if current_topic else ""
    return [
        topic["topic"]
        for topic in path["topics"]
        if topic["state"] != "covered" and _normalize(topic["topic"]) != normalized_current
    ]


def _topic_action(path: dict | None, topic_name: str | None) -> str | None:
    if not path or not topic_name:
        return None
    for topic in path["topics"]:
        if _normalize(topic["topic"]) == _normalize(topic_name):
            return topic.get("action")
    return None


def _recommended_topic_reason(path: dict | None, current_topic: str | None, recommended_topic: str | None) -> str | None:
    if not path or not recommended_topic:
        return None
    if current_topic and _normalize(current_topic) != _normalize(recommended_topic):
        return f"This is the next step after {current_topic} in the {path['path_name']} path."
    return f"This is the next step in the {path['path_name']} path."


def _classify_question(question: str) -> str:
    normalized_question = _normalize(question)
    if any(phrase in normalized_question for phrase in QUESTION_PATTERNS["focus_path"]):
        return "focus_path"
    if any(phrase in normalized_question for phrase in QUESTION_PATTERNS["progress"]):
        return "progress"
    if any(phrase in normalized_question for phrase in QUESTION_PATTERNS["missing"]):
        return "missing"
    if any(phrase in normalized_question for phrase in QUESTION_PATTERNS["why"]):
        return "why"
    if "unlock" in normalized_question and "what" in normalized_question:
        return "unlock"
    if any(phrase in normalized_question for phrase in QUESTION_PATTERNS["unlock"][:2]):
        return "unlock"
    if any(phrase in normalized_question for phrase in QUESTION_PATTERNS["next"]):
        return "next"
    return "next"


def _build_response(
    *,
    answer: str,
    path: dict | None = None,
    current_topic: str | None = None,
    recommended_topic_data: dict | None = None,
    why_topic: str | None = None,
    skills_topic: str | None = None,
) -> dict:
    recommended_topic = recommended_topic_data.get("topic") if recommended_topic_data else None
    recommendation_path = path or None
    why_topic_name = why_topic or recommended_topic
    skills_topic_name = skills_topic or recommended_topic

    return {
        "answer": answer,
        "recommended_topic": recommended_topic,
        "recommended_action": recommended_topic_data.get("action") if recommended_topic_data else None,
        "path_name": recommendation_path["path_name"] if recommendation_path else None,
        "path_progress": _path_progress(recommendation_path),
        "why_it_matters": _topic_why(why_topic_name) if why_topic_name else None,
        "recommended_topic_reason": _recommended_topic_reason(recommendation_path, current_topic, recommended_topic),
        "skills_unlocked": _skills_unlocked(skills_topic_name, recommendation_path["path_name"]) if skills_topic_name and recommendation_path else [],
        "missing_topics": _remaining_topics(recommendation_path, current_topic),
        "path_topics": _mentor_path_topics(recommendation_path, current_topic),
    }


def answer_mentor_question(db: Session, user_id: int, question: str) -> dict:
    learning_paths = build_learning_paths(db, user_id)
    question_type = _classify_question(question)
    resolved_path = _resolve_path(question, learning_paths)
    resolved_topic = _resolve_topic(question)

    if question_type == "focus_path":
        target_path = next((path for path in learning_paths if path.get("next_topic")), learning_paths[0] if learning_paths else None)
        if not target_path:
            return {"answer": "I could not find a learning path yet. Add more knowledge to start building your roadmap."}
        next_topic = _recommended_topic_data(target_path)
        topic_name = next_topic["topic"] if next_topic else None
        return _build_response(
            answer=(
                f"The best learning path to focus on next is {target_path['path_name']} because it is currently active and your next step there is {topic_name}."
                if topic_name
                else f"{target_path['path_name']} is the best path to focus on next."
            ),
            path=target_path,
            current_topic=topic_name,
            recommended_topic_data=next_topic,
        )

    if question_type == "progress":
        target_path = resolved_path or (learning_paths[0] if learning_paths else None)
        if not target_path:
            return {"answer": "I could not find a learning path to measure yet."}
        next_topic = _recommended_topic_data(target_path)
        return _build_response(
            answer=(
                f"You are {target_path['progress_percent']}% of the way through {target_path['path_name']}, with {target_path['covered_count']} of {target_path['total_count']} topics covered."
                + (f" Your next topic is {next_topic['topic']}." if next_topic else " You have completed this path.")
            ),
            path=target_path,
            current_topic=next_topic["topic"] if next_topic else None,
            recommended_topic_data=next_topic,
        )

    if question_type == "missing":
        target_path = resolved_path or (learning_paths[0] if learning_paths else None)
        if not target_path:
            return {"answer": "I could not find a matching path to inspect for missing topics."}
        remaining_topics = _remaining_topics(target_path)
        next_topic = _recommended_topic_data(target_path)
        return _build_response(
            answer=(
                f"You are still missing {', '.join(remaining_topics)} in {target_path['path_name']}."
                if remaining_topics
                else f"You are not missing any topics in {target_path['path_name']}."
            ),
            path=target_path,
            current_topic=next_topic["topic"] if next_topic else None,
            recommended_topic_data=next_topic,
        )

    if question_type == "why":
        topic_name = resolved_topic["topic"] if resolved_topic else None
        topic_path = _find_path_for_topic(learning_paths, topic_name, resolved_topic["path_name"] if resolved_topic else None) or resolved_path
        if not topic_name:
            topic_name = (topic_path.get("next_topic") or {}).get("topic") if topic_path else None
        if not topic_name:
            return {"answer": "I could not find which topic you meant. Try asking about a topic from one of your learning paths."}
        next_topic = _recommended_topic_data(topic_path, topic_name)
        unlocked = _skills_unlocked(topic_name, topic_path["path_name"] if topic_path else None)
        return _build_response(
            answer=f"You should learn {topic_name} because {_topic_why(topic_name).rstrip('.')} and it supports the path toward {', '.join(unlocked[:2]) or 'the next stage of your roadmap'}.",
            path=topic_path,
            current_topic=topic_name,
            recommended_topic_data=next_topic,
            why_topic=topic_name,
            skills_topic=topic_name,
        )

    if question_type == "unlock":
        topic_name = resolved_topic["topic"] if resolved_topic else None
        topic_path = _find_path_for_topic(learning_paths, topic_name, resolved_topic["path_name"] if resolved_topic else None) or resolved_path
        if not topic_name:
            topic_name = (topic_path.get("next_topic") or {}).get("topic") if topic_path else None
        if not topic_name:
            return {"answer": "I could not find which topic you meant. Try naming a topic from one of your learning paths."}
        unlocked = _skills_unlocked(topic_name, topic_path["path_name"] if topic_path else None)
        next_topic = _recommended_topic_data(topic_path, topic_name)
        return _build_response(
            answer=(
                f"{topic_name} unlocks {', '.join(unlocked)}."
                if unlocked
                else f"{topic_name} is a later-stage topic and does not clearly unlock additional topics in the current paths."
            ),
            path=topic_path,
            current_topic=topic_name,
            recommended_topic_data=next_topic,
            why_topic=topic_name,
            skills_topic=topic_name,
        )

    target_path = resolved_path or (learning_paths[0] if learning_paths else None)
    if not target_path:
        return {"answer": "I could not find a learning path yet. Add more knowledge to start building your roadmap."}

    next_topic = _recommended_topic_data(target_path)
    if not next_topic:
        return {
            "answer": f"You have completed {target_path['path_name']}. Choose another active path to continue learning.",
            "path_name": target_path["path_name"],
            "path_progress": _path_progress(target_path),
            "missing_topics": [],
            "skills_unlocked": [],
            "path_topics": _mentor_path_topics(target_path),
        }

    topic_name = next_topic["topic"]
    unlocked = _skills_unlocked(topic_name, target_path["path_name"])
    return _build_response(
        answer=f"Your next best topic in {target_path['domain']} is {topic_name} because it is the next step in {target_path['path_name']} and it unlocks {', '.join(unlocked) or 'the next stage of your roadmap'}.",
        path=target_path,
        current_topic=topic_name,
        recommended_topic_data=next_topic,
    )
