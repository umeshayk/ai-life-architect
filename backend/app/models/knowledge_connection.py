from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class KnowledgeConnection(Base):
    __tablename__ = "knowledge_connections"
    __table_args__ = (
        UniqueConstraint(
            "source_knowledge_id",
            "target_knowledge_id",
            "connection_type",
            name="uq_knowledge_connections_pair_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_knowledge_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_knowledge_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    connection_type: Mapped[str] = mapped_column(String(50), nullable=False, default="semantic_related")
    similarity_score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    source_item = relationship("KnowledgeItem", foreign_keys=[source_knowledge_id], back_populates="outgoing_connections")
    target_item = relationship("KnowledgeItem", foreign_keys=[target_knowledge_id], back_populates="incoming_connections")
