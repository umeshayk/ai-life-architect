from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="knowledge_items")
    embedding = relationship(
        "KnowledgeEmbedding", back_populates="knowledge_item", uselist=False, cascade="all, delete-orphan"
    )
    content_topics = relationship(
        "ContentTopic", back_populates="knowledge_item", cascade="all, delete-orphan"
    )
    outgoing_connections = relationship(
        "KnowledgeConnection",
        foreign_keys="KnowledgeConnection.source_knowledge_id",
        back_populates="source_item",
        cascade="all, delete-orphan",
    )
    incoming_connections = relationship(
        "KnowledgeConnection",
        foreign_keys="KnowledgeConnection.target_knowledge_id",
        back_populates="target_item",
        cascade="all, delete-orphan",
    )
