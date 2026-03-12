from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge import KnowledgeItem
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.ai import AskAIRequest, AskAIResponse, SearchResultItem, SemanticSearchRequest, SourceItem
from app.schemas.knowledge import WeeklyInsightsResponse
from app.services.insight_service import build_weekly_insights
from app.services.llm import ask_ollama
from app.services.retrieval import semantic_search


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
    return AskAIResponse(
        answer=ask_ollama(payload.question, matches),
        sources=[build_source_payload(match.item, match.similarity) for match in matches],
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
