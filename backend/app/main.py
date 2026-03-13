from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import Base, engine
from app.models import content_topic, embedding, knowledge, knowledge_connection, profile, topic, user  # noqa: F401
from app.routers import ai, auth, connections, graph, insights, knowledge, profile, timeline, topics, upload


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
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(knowledge.router)
app.include_router(knowledge.api_router)
app.include_router(upload.router)
app.include_router(ai.router)
app.include_router(topics.router)
app.include_router(connections.router)
app.include_router(insights.router)
app.include_router(graph.router)
app.include_router(timeline.router)
