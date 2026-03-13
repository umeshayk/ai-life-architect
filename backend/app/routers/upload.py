from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.knowledge import serialize_knowledge
from app.schemas.knowledge import KnowledgeResponse
from app.services.file_parser import parse_uploaded_file
from app.services.upload_ingestion_service import create_ingested_knowledge_item


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

    extraction_failed = False
    try:
        content = parse_uploaded_file(file_path, original_name=file.filename or stored_name)
    except Exception:
        extraction_failed = True
        content = f"Uploaded file: {file.filename or stored_name}. Text extraction failed, so manual topic assignment may be needed."

    item, ingestion_summary = create_ingested_knowledge_item(
        db,
        user_id=current_user.id,
        item_type="file",
        title=file.filename or stored_name,
        content=content,
        file_name=file.filename or stored_name,
        skip_topic_generation=extraction_failed,
    )
    return serialize_knowledge(item, ingestion_summary=ingestion_summary)
