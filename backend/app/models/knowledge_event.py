from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class KnowledgeEvent(Base):
    __tablename__ = "knowledge_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    related_topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(60), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    topic = relationship("Topic", foreign_keys=[topic_id])
    related_topic = relationship("Topic", foreign_keys=[related_topic_id])
