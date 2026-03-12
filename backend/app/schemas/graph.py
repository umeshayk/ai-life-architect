from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    group: str
    size: float
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


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
