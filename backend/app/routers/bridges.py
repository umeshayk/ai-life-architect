from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.topic import DomainBridgeListResponse
from app.services.domain_bridge_engine import discover_domain_bridges

router = APIRouter(tags=["bridges"])


@router.get("/api/bridges", response_model=DomainBridgeListResponse)
def get_domain_bridges(
    limit: int = Query(4, ge=1, le=8),
    domain: str = Query(""),
    topic: str = Query(""),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = discover_domain_bridges(db, current_user.id, limit=limit, domain=domain, topic=topic, refresh=refresh)
    return DomainBridgeListResponse(
        bridges=payload.get("bridges", []),
        source=payload.get("source", "rules"),
        stored_source=payload.get("stored_source"),
        cached=payload.get("cached", False),
        feature_type=payload.get("feature_type", "bridge_suggestion"),
        graph_version=payload.get("graph_version"),
    )
