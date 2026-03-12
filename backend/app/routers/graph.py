from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.graph import GraphResponse
from app.services.graph_service import build_graph_for_user


router = APIRouter(tags=["graph"])


@router.get("/api/graph", response_model=GraphResponse)
def get_graph(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return build_graph_for_user(db, current_user.id)
