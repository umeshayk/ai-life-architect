from datetime import datetime

from pydantic import BaseModel


class RelatedKnowledgeItem(BaseModel):
    id: int
    title: str
    type: str
    summary: str | None = None
    similarity_score: float
    connection_type: str


class ConnectionResponse(BaseModel):
    knowledge_id: int
    related_items: list[RelatedKnowledgeItem]


class RebuildConnectionsResponse(BaseModel):
    processed_items: int
    connections_created: int
    created_at: datetime
