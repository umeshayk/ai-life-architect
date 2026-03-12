from __future__ import annotations

from app.schemas.action_plan import ActionPlanItem, ActionPlanResponse
from app.services.timeline_service import get_timeline


DOMAIN_TOPIC_MAP = {
    "AI Systems": {
        "Embeddings",
        "Semantic Search",
        "Vector Databases",
        "Hybrid Search",
        "Retrieval Optimization",
        "Retrieval Augmented Generation",
        "LLM Systems",
        "Index Optimization",
        "Vector Indexing",
        "Embedding Evaluation",
    },
    "Agriculture": {
        "Mushroom Farming",
        "Hydroponic Farming",
        "Spawn Quality",
        "Substrate Sterilization",
        "Yield Optimization",
        "Climate Control",
        "Controlled Environment Agriculture",
        "Farm Business",
        "Mushroom Business Models",
    },
    "Vedic Mathematics": {
        "Vedic Mathematics",
        "Nikhilam Sutra",
        "Urdhva Tiryagbhyam",
        "Speed Multiplication",
        "Mental Math",
        "Mental Math Speed Techniques",
        "Vedic Multiplication",
    },
    "Knowledge Management": {
        "Knowledge Management",
        "AI Life Architect",
        "Second Brain Workflows",
        "Personal Knowledge Architecture",
        "Note Linking Systems",
    },
}


def get_weekly_action_plan(
    db,
    user_id: int,
    range_key: str = "30d",
    group_by: str = "week",
) -> ActionPlanResponse:
    timeline = get_timeline(db, user_id, range_key=range_key, group_by=group_by)
    insights = timeline.insights

    if not insights:
        return ActionPlanResponse(weekly_plan=[])

    plan: list[ActionPlanItem] = []
    seen_domains: set[str] = set()

    for project in insights.projects:
        domain = project.name.removesuffix(" Project")
        if domain in seen_domains or not project.next_step:
            continue
        plan.append(
            ActionPlanItem(
                domain=domain,
                action=_build_action_label(project.next_step, domain),
                reason=(
                    f"{domain} project is {int(project.progress * 100)}% complete and "
                    f"{project.next_step} is the next missing step."
                ),
            )
        )
        seen_domains.add(domain)
        if len(plan) >= 3:
            return ActionPlanResponse(weekly_plan=plan)

    for gap in insights.knowledge_gaps:
        domain = _domain_for_topic(gap)
        if domain in seen_domains:
            continue
        plan.append(
            ActionPlanItem(
                domain=domain,
                action=_build_action_label(gap, domain),
                reason=f"{domain} is active in your knowledge and {gap} is still a missing foundational topic.",
            )
        )
        seen_domains.add(domain)
        if len(plan) >= 3:
            return ActionPlanResponse(weekly_plan=plan)

    for strategy in insights.strategies:
        if strategy.domain in seen_domains:
            continue
        next_step = next((step.topic for step in strategy.path if not step.completed), None)
        if not next_step:
            continue
        is_emerging = strategy.domain in insights.emerging_topics or strategy.domain == insights.emerging_topic
        reason = (
            f"{strategy.domain} is emerging and {next_step} is the next foundational step."
            if is_emerging
            else f"{strategy.domain} is active in your knowledge and {next_step} is the next foundational step."
        )
        plan.append(
            ActionPlanItem(
                domain=strategy.domain,
                action=_build_action_label(next_step, strategy.domain),
                reason=reason,
            )
        )
        seen_domains.add(strategy.domain)
        if len(plan) >= 3:
            break

    return ActionPlanResponse(weekly_plan=plan[:3])


def _build_action_label(topic_name: str, domain: str) -> str:
    if domain == "Vedic Mathematics" or "Sutra" in topic_name:
        return f"Start {topic_name}"
    return f"Study {topic_name}"


def _domain_for_topic(topic_name: str) -> str:
    for domain, topics in DOMAIN_TOPIC_MAP.items():
        if topic_name in topics:
            return domain
    return "Knowledge Development"
