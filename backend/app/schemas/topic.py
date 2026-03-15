from datetime import datetime

from pydantic import BaseModel

from app.schemas.knowledge import KnowledgeResponse


class TopicSummary(BaseModel):
    id: int
    name: str
    count: int
    discovery_method: str = "discovered"
    domain: str | None = None


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


class TopicCleanupResponse(BaseModel):
    merged_topics: int
    discovery_method: str = "normalized"


class TopicItemsResponse(BaseModel):
    topic: TopicSummary
    items: list[KnowledgeResponse]


class TopicNoteSummary(BaseModel):
    id: int
    title: str
    type: str
    preview: str


class TopicDetailResponse(BaseModel):
    topic: str
    topic_id: int | None = None
    notes: list[TopicNoteSummary]
    related_topics: list[str]


class TopicCreateRequest(BaseModel):
    name: str


class TopicCreateResponse(BaseModel):
    topic: TopicSummary
    created: bool = False


class TopicExpansionResponse(BaseModel):
    topic: str
    source: str = "rules"
    cached: bool = False
    rule_confidence: float = 0.0
    ai_confidence: float = 0.0
    context_topics: list[str] = []
    suggestions: list[str]


class TopicSummaryResponse(BaseModel):
    topic: str
    summary: str
    why_it_matters: str
    skills_unlocked: list[str] = []
    source: str = "rules"


class TopicSearchResult(BaseModel):
    id: int
    name: str
    domain: str | None = None
    count: int = 0


class KnowledgeSuggestion(BaseModel):
    suggested_topic: str
    reason: str
    confidence: float
    domain: str
    topic_exists: bool = False
    state: str = "missing"
    action: str = "add"


class NextLearningTopic(BaseModel):
    topic: str
    reason: str
    confidence: float
    domain: str
    state: str = "missing"
    action: str = "add"
    priority: int
    topic_exists: bool = False


class LearningPathTopic(BaseModel):
    topic: str
    state: str = "missing"
    action: str = "add"
    domain: str | None = None


class LearningPathResponse(BaseModel):
    path_name: str
    domain: str
    progress_percent: int
    covered_count: int
    total_count: int
    next_topic: LearningPathTopic | None = None
    topics: list[LearningPathTopic]
    completed_topics: list[str] = []
    upcoming_topics: list[str] = []


class KnowledgeGapItem(BaseModel):
    topic: str
    state: str = "missing"
    action: str = "add"
    reason: str
    confidence: float
    source: str = "rules"


class KnowledgeGapPathResponse(BaseModel):
    path_name: str
    domain: str
    progress_percent: int
    covered_count: int
    total_count: int
    next_topic: LearningPathTopic | None = None
    source: str = "rules"
    cached: bool = False
    rule_confidence: float = 0.0
    ai_confidence: float = 0.0
    missing_topics: list[KnowledgeGapItem] = []


class RelationshipDetailResponse(BaseModel):
    id: int
    source_topic: str
    target_topic: str
    relationship_type: str
    confidence: float
    explanation: str
    evidence: dict = {}
from pydantic import BaseModel

class RecommendationItem(BaseModel):
    topic: str
    score: float
    confidence: float
    reason: str
    source_signals: list[str] = []
    domain: str
    action: str = "add"
    path_name: str | None = None


class RecommendationListResponse(BaseModel):
    recommendations: list[RecommendationItem] = []


class TopicMasteryResponse(BaseModel):
    topic: str
    topic_id: int
    mastery_score: float
    signals: dict = {}
    last_updated: datetime | None = None
