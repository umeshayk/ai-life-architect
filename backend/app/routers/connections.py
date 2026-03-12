from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge import KnowledgeItem
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.connection import ConnectionResponse, RebuildConnectionsResponse, RelatedKnowledgeItem
from app.services.connection_service import (
    build_connection_rebuild_response,
    get_related_connections,
    rebuild_connections_for_user,
)


router = APIRouter(tags=["connections"])


@router.get("/api/connections/{knowledge_id}", response_model=ConnectionResponse)
def get_connections(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.scalar(
        select(KnowledgeItem).where(KnowledgeItem.id == knowledge_id, KnowledgeItem.user_id == current_user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    related = get_related_connections(db, current_user.id, knowledge_id)
    return ConnectionResponse(
        knowledge_id=knowledge_id,
        related_items=[
            RelatedKnowledgeItem(
                id=connection.target_item.id,
                title=connection.target_item.title,
                type=connection.target_item.type,
                summary=connection.target_item.summary,
                similarity_score=connection.similarity_score,
                connection_type=connection.connection_type,
            )
            for connection in related
        ],
    )


@router.post("/api/connections/rebuild", response_model=RebuildConnectionsResponse)
def rebuild_connections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    processed_items, connections_created = rebuild_connections_for_user(db, current_user.id)
    return RebuildConnectionsResponse(**build_connection_rebuild_response(processed_items, connections_created))
