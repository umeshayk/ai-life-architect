from pydantic import BaseModel, Field


class AskAIRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=10)


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceItem(BaseModel):
    id: int
    title: str
    type: str
    summary: str | None = None
    similarity: float


class SearchResultItem(SourceItem):
    pass


class AskAIResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
