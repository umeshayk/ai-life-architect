from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TopicSummary(Base):
    __tablename__ = "topic_summaries"
    __table_args__ = (UniqueConstraint("topic_id", name="uq_topic_summaries_topic_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    skills_unlocked_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="rules", server_default="rules")
    graph_version: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    topic = relationship("Topic", backref="topic_summary_record")
