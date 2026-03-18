from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class AITopicInsight(Base):
    __tablename__ = "ai_topic_insights"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "topic_name",
            "feature_type",
            "context_hash",
            "graph_version",
            name="uq_ai_topic_insights_scope",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    feature_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    context_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    graph_version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="rules", server_default="rules")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
