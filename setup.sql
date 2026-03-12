-- Run these commands in psql as a PostgreSQL superuser.
-- 1. CREATE DATABASE ai_life_architect;
-- 2. \c ai_life_architect

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    goals TEXT,
    interests TEXT,
    expertise TEXT,
    preferred_topics TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    tags TEXT,
    source_url VARCHAR(500),
    file_name VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    id SERIAL PRIMARY KEY,
    knowledge_item_id INTEGER NOT NULL UNIQUE REFERENCES knowledge_items(id) ON DELETE CASCADE,
    embedding VECTOR(384) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_knowledge_items_user_id ON knowledge_items(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_vector
ON knowledge_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
