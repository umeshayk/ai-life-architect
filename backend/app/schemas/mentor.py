from pydantic import BaseModel


class MentorAskRequest(BaseModel):
    question: str


class MentorPathProgress(BaseModel):
    covered_count: int
    total_count: int
    progress_percent: int


class MentorPathTopic(BaseModel):
    topic: str
    state: str


class MentorAskResponse(BaseModel):
    answer: str
    recommended_topic: str | None = None
    recommended_action: str | None = None
    path_name: str | None = None
    path_progress: MentorPathProgress | None = None
    why_it_matters: str | None = None
    recommended_topic_reason: str | None = None
    skills_unlocked: list[str] = []
    missing_topics: list[str] = []
    path_topics: list[MentorPathTopic] = []
