from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.knowledge import KnowledgeItem
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.knowledge import KnowledgeResponse
from app.services.embeddings import sync_knowledge_embedding
from app.services.file_parser import parse_uploaded_file
from app.services.summarizer import build_summary_and_tags


router = APIRouter(prefix="/upload", tags=["upload"])
settings = get_settings()


@router.post("", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF and TXT files are supported")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    file_path = upload_dir / stored_name
    file_path.write_bytes(await file.read())

    content = parse_uploaded_file(file_path, original_name=file.filename or stored_name)
    summary, tags = build_summary_and_tags(file.filename or stored_name, content)

    item = KnowledgeItem(
        user_id=current_user.id,
        type="file",
        title=file.filename or stored_name,
        content=content,
        summary=summary,
        tags=",".join(tags),
        file_name=file.filename or stored_name,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    sync_knowledge_embedding(db, item)
    db.refresh(item)

    return KnowledgeResponse(
        id=item.id,
        user_id=item.user_id,
        type=item.type,
        title=item.title,
        content=item.content,
        summary=item.summary,
        tags=tags,
        source_url=item.source_url,
        file_name=item.file_name,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
