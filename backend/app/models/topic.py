from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_topics_user_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="standard", server_default="standard")
    parent_topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=2, server_default="2")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    content_topics = relationship("ContentTopic", back_populates="topic", cascade="all, delete-orphan")
    parent_topic = relationship("Topic", remote_side=[id], back_populates="child_topics")
    child_topics = relationship("Topic", back_populates="parent_topic")
