from pydantic import BaseModel


class TopicInsight(BaseModel):
    id: int
    name: str
    count: int


class WeeklyInsightResponse(BaseModel):
    total_items: int
    items_added_this_week: int
    top_topics: list[TopicInsight]
    top_tags: list[str]
    recent_titles: list[str]
    suggestions: list[str]
