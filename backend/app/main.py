from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import Base, engine
from app.models import content_topic, embedding, knowledge, knowledge_connection, knowledge_event, knowledge_gap_cache, profile, topic, topic_expansion_cache, topic_mastery, topic_relationship, topic_summary, user  # noqa: F401
from app.routers import ai, auth, bridges, connections, graph, insights, knowledge, knowledge_gaps, learning_paths, mentor, profile, recommendations, timeline, topics, upload


settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.execute(
            text("ALTER TABLE IF EXISTS topics ADD COLUMN IF NOT EXISTS type VARCHAR(30) NOT NULL DEFAULT 'standard'")
        )
        connection.execute(text("ALTER TABLE IF EXISTS topics ADD COLUMN IF NOT EXISTS parent_topic_id INTEGER"))
        connection.execute(text("ALTER TABLE IF EXISTS topics ADD COLUMN IF NOT EXISTS level INTEGER NOT NULL DEFAULT 2"))
        connection.execute(text("ALTER TABLE IF EXISTS topic_mastery ADD COLUMN IF NOT EXISTS mastery_score DOUBLE PRECISION NOT NULL DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS topic_mastery ADD COLUMN IF NOT EXISTS signals_json TEXT NOT NULL DEFAULT '{}'"))
        connection.execute(text("ALTER TABLE IF EXISTS topic_mastery ADD COLUMN IF NOT EXISTS last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()"))
        connection.execute(text("ALTER TABLE IF EXISTS topic_relationships ADD COLUMN IF NOT EXISTS source_topic_id INTEGER"))
        connection.execute(text("ALTER TABLE IF EXISTS topic_relationships ADD COLUMN IF NOT EXISTS target_topic_id INTEGER"))
        connection.execute(text("ALTER TABLE IF EXISTS topic_relationships ADD COLUMN IF NOT EXISTS evidence_json TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS topic_relationships ADD COLUMN IF NOT EXISTS explanation_text TEXT"))
        connection.execute(
            text(
                "ALTER TABLE IF EXISTS topic_relationships ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
            )
        )
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(knowledge.router)
app.include_router(knowledge.api_router)
app.include_router(knowledge_gaps.router)
app.include_router(recommendations.router)
app.include_router(upload.router)
app.include_router(ai.router)
app.include_router(topics.router)
app.include_router(bridges.router)
app.include_router(learning_paths.router)
app.include_router(mentor.router)
app.include_router(connections.router)
app.include_router(insights.router)
app.include_router(graph.router)
app.include_router(timeline.router)





