from datetime import datetime

from pydantic import BaseModel

from app.schemas.knowledge import KnowledgeResponse


class TopicSummary(BaseModel):
    id: int
    name: str
    count: int
    discovery_method: str = "discovered"


class TopicItem(BaseModel):
    id: int
    name: str
    confidence_score: float
    created_at: datetime


class TopicRebuildResponse(BaseModel):
    processed_items: int
    topics_created: int
    links_created: int
    discovery_method: str = "discovered"


class TopicItemsResponse(BaseModel):
    topic: TopicSummary
    items: list[KnowledgeResponse]
