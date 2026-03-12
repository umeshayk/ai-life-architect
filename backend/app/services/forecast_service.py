from __future__ import annotations

from app.schemas.evolution import EvolutionResponse
from app.schemas.timeline import KnowledgeForecast, KnowledgeProject, TimelineTopicCount


FORECAST_DOMAINS = [
    {
        "domain": "AI Systems",
        "seeds": {"Embeddings", "Semantic Search", "Vector Databases", "Hybrid Search", "Retrieval Optimization"},
    },
    {
        "domain": "Agriculture",
        "seeds": {"Mushroom Farming", "Hydroponic Farming", "Spawn Quality", "Substrate Sterilization", "Yield Optimization", "Climate Control"},
    },
    {
        "domain": "Vedic Mathematics",
        "seeds": {"Vedic Mathematics", "Nikhilam Sutra", "Urdhva Tiryagbhyam", "Speed Multiplication", "Mental Math"},
    },
]


def build_knowledge_forecast(
    top_topics: list[TimelineTopicCount],
    projects: list[KnowledgeProject],
    evolution: EvolutionResponse,
) -> list[KnowledgeForecast]:
    topic_names = {topic.name for topic in top_topics}
    project_map = {project.name.replace(" Project", ""): project for project in projects}
    series_map = {series.topic: series.values for series in evolution.series}

    forecasts: list[KnowledgeForecast] = []
    for config in FORECAST_DOMAINS:
        project = project_map.get(config["domain"])
        matched_topics = config["seeds"].intersection(topic_names)
        if not matched_topics and project is None:
            continue

        current_total = 0
        previous_total = 0
        for topic_name in config["seeds"]:
            values = series_map.get(topic_name)
            if not values:
                continue
            current_total += values[-1]
            previous_total += values[-2] if len(values) >= 2 else 0

        growth_rate = max(current_total - previous_total, 0)
        progress = project.progress if project is not None else min(1.0, len(matched_topics) / max(len(config["seeds"]), 1))
        confidence = min(
            0.95,
            0.35
            + min(current_total, 12) * 0.02
            + min(growth_rate, 10) * 0.025
            + progress * 0.3,
        )
        estimated_mastery_months = max(3, min(12, round(10 - confidence * 6 - progress * 2)))

        forecasts.append(
            KnowledgeForecast(
                domain=config["domain"],
                confidence=round(confidence, 2),
                estimated_mastery_months=estimated_mastery_months,
            )
        )

    forecasts.sort(key=lambda forecast: (-forecast.confidence, forecast.estimated_mastery_months, forecast.domain))
    return forecasts[:3]
