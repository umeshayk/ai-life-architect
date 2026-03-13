from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge import KnowledgeItem
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.ai import AskAIInsights, AskAIRequest, AskAIResponse, SearchResultItem, SemanticSearchRequest, SourceItem
from app.schemas.knowledge import WeeklyInsightsResponse
from app.services.insight_service import build_weekly_insights
from app.services.llm import ask_ollama
from app.services.action_plan_service import get_weekly_action_plan
from app.services.retrieval import semantic_search
from app.services.timeline_service import get_timeline


router = APIRouter(tags=["ai"])


def build_source_payload(item: KnowledgeItem, similarity: float) -> SourceItem:
    return SourceItem(
        id=item.id,
        title=item.title,
        type=item.type,
        summary=item.summary,
        similarity=similarity,
        topic_names=[content_topic.topic.name for content_topic in item.content_topics if content_topic.topic],
    )


@router.post("/api/ai/search", response_model=list[SearchResultItem])
@router.post("/ai/search", response_model=list[SearchResultItem], include_in_schema=False)
def search_ai(
    payload: SemanticSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    matches = semantic_search(db, current_user.id, payload.query, payload.top_k)
    return [
        SearchResultItem(
            id=match.item.id,
            title=match.item.title,
            type=match.item.type,
            summary=match.item.summary,
            similarity=match.similarity,
        )
        for match in matches
    ]


@router.post("/api/ai/ask", response_model=AskAIResponse)
@router.post("/ai/ask", response_model=AskAIResponse, include_in_schema=False)
def ask_ai(
    payload: AskAIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    matches = semantic_search(db, current_user.id, payload.question, payload.top_k)
    timeline = get_timeline(db, current_user.id, range_key="30d", group_by="week")
    weekly_plan = get_weekly_action_plan(db, current_user.id, range_key="30d", group_by="week")
    mentor_context = build_mentor_context(timeline, weekly_plan)
    top_project = timeline.insights.projects[0] if timeline.insights.projects else None
    next_step = weekly_plan.weekly_plan[0].action if weekly_plan.weekly_plan else (top_project.next_step if top_project else None)
    return AskAIResponse(
        answer=ask_ollama(payload.question, matches, mentor_context=mentor_context),
        sources=[build_source_payload(match.item, match.similarity) for match in matches],
        insights=AskAIInsights(
            dominant_topic=timeline.insights.dominant_topic,
            next_step=next_step,
            top_project=top_project.name if top_project else None,
            project_progress=int(top_project.progress * 100) if top_project else None,
        ),
    )


@router.get("/api/ai/weekly-insights", response_model=WeeklyInsightsResponse)
@router.get("/ai/weekly-insights", response_model=WeeklyInsightsResponse, include_in_schema=False)
def weekly_insights(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    insights = build_weekly_insights(db, current_user.id)
    return WeeklyInsightsResponse(
        total_items=insights["total_items"],
        items_added_this_week=insights["items_added_this_week"],
        top_tags=insights["top_tags"],
        recent_titles=insights["recent_titles"],
    )


def build_mentor_context(timeline, weekly_plan):
    return {
        "top_topics": [topic.name for topic in timeline.top_topics[:5]],
        "dominant_topic": timeline.insights.dominant_topic,
        "emerging_topics": timeline.insights.emerging_topics,
        "knowledge_gaps": timeline.insights.knowledge_gaps,
        "suggested_topics": timeline.insights.suggested_topics,
        "strategies": [strategy.model_dump() for strategy in timeline.insights.strategies],
        "projects": [
            {
                "name": project.name,
                "progress": int(project.progress * 100),
                "next_step": project.next_step,
            }
            for project in timeline.insights.projects
        ],
        "weekly_plan": [item.model_dump() for item in weekly_plan.weekly_plan],
        "forecast": [
            {
                "domain": entry.domain,
                "confidence": int(entry.confidence * 100),
                "estimated_mastery_months": entry.estimated_mastery_months,
            }
            for entry in timeline.insights.forecast
        ],
    }
