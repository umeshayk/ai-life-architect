from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    group: str
    size: float
    importance: float = 0.0
    connection_count: int = 0
    domain: str | None = None
    cluster: str | None = None
    cluster_rank: int | None = None
    centrality: float | None = None
    is_center: bool = False
    summary: str | None = None
    content_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    related_titles: list[str] = Field(default_factory=list)
    linked_titles: list[str] = Field(default_factory=list)
    linked_count: int = 0


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    weight: float = 1.0


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    level: int = 1
    domain: str | None = None
    topic: str | None = None
    available_domains: list[str] = Field(default_factory=list)
