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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bridges = discover_domain_bridges(db, current_user.id, limit=limit, domain=domain, topic=topic)
    return DomainBridgeListResponse(bridges=bridges)
