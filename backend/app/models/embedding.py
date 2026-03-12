from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeEmbedding(Base):
    __tablename__ = "knowledge_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    knowledge_item_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)

    knowledge_item = relationship("KnowledgeItem", back_populates="embedding")
