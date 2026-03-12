from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge import KnowledgeItem
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.ai import AskAIRequest, AskAIResponse, SearchResultItem, SemanticSearchRequest, SourceItem
from app.schemas.knowledge import WeeklyInsightsResponse
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
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    total_items = db.scalar(
        select(func.count(KnowledgeItem.id)).where(KnowledgeItem.user_id == current_user.id)
    ) or 0
    items_added_this_week = db.scalar(
        select(func.count(KnowledgeItem.id)).where(
            KnowledgeItem.user_id == current_user.id,
            KnowledgeItem.created_at >= week_ago,
        )
    ) or 0
    recent_items = db.scalars(
        select(KnowledgeItem)
        .where(KnowledgeItem.user_id == current_user.id)
        .order_by(desc(KnowledgeItem.created_at))
        .limit(10)
    ).all()

    tag_counts: dict[str, int] = {}
    for item in recent_items:
        for tag in (item.tags or "").split(","):
            cleaned = tag.strip()
            if cleaned:
                tag_counts[cleaned] = tag_counts.get(cleaned, 0) + 1

    return WeeklyInsightsResponse(
        total_items=total_items,
        items_added_this_week=items_added_this_week,
        top_tags=[tag for tag, _ in sorted(tag_counts.items(), key=lambda pair: pair[1], reverse=True)[:5]],
        recent_titles=[item.title for item in recent_items[:5]],
    )
