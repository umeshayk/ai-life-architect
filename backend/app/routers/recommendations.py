from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.topic import RecommendationItem, RecommendationListResponse
from app.services.recommendation_engine import recommend_next_topic, recommend_next_topics

router = APIRouter(tags=["recommendations"])


@router.get("/api/recommendations/next-topics", response_model=RecommendationListResponse)
def get_next_topic_recommendations(
    limit: int = Query(3, ge=1, le=10),
    domain: str = Query(""),
    topic: str = Query(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recommendations = recommend_next_topics(db, current_user.id, limit=limit, domain=domain, topic=topic)
    return RecommendationListResponse(
        recommendations=[RecommendationItem(**item) for item in recommendations]
    )


@router.get("/api/recommendations/next-topic", response_model=RecommendationItem | None)
def get_next_topic_recommendation(
    domain: str = Query(""),
    topic: str = Query(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recommendation = recommend_next_topic(db, current_user.id, domain=domain, topic=topic)
    return RecommendationItem(**recommendation) if recommendation else None
