from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class TopicExpansionCache(Base):
    __tablename__ = "topic_expansion_cache"
    __table_args__ = (
        UniqueConstraint("topic_key", name="uq_topic_expansion_cache_topic_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    suggestions_blob: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
