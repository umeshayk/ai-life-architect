# AI Life Architect – Project Memory

## Project Goal

Build a personal AI knowledge system where users can store notes, links, and documents and ask questions over them using AI.

The system should act as a personal "AI brain".

---

## Tech Stack

Frontend
React + Vite

Backend
FastAPI

Database
PostgreSQL

Vector Search
pgvector

Embeddings
sentence-transformers/all-MiniLM-L6-v2

LLM Runtime
Ollama

---

## Current Status

Working Features

Authentication
Dashboard
Knowledge storage (notes)
Document upload
Tag extraction
Recent activity tracking
Basic semantic search UI

Dashboard shows:
- Total knowledge items
- Items added this week
- Top tags
- Recent titles

---

## Data Model

Tables

users
user_profile
knowledge_items
knowledge_embeddings

knowledge_items fields

id
user_id
type (note, link, document)
title
content
summary
tags
source_url
file_name
created_at
updated_at

knowledge_embeddings fields

id
knowledge_id
embedding vector(384)

---

## Knowledge Types

Note
Link
Document

Documents are uploaded through Upload page.

---

## AI Pipeline

Knowledge ingestion

User saves knowledge
↓
Summary generated
↓
Embedding generated
↓
Stored in pgvector

AI Question Answering (RAG)

User question
↓
Generate question embedding
↓
Vector search (pgvector)
↓
Retrieve top knowledge items
↓
Send context to Ollama
↓
Return grounded answer

---

## Main API Endpoints

Auth

POST /api/auth/signup
POST /api/auth/login

Knowledge

GET /api/knowledge
POST /api/knowledge

Upload

POST /api/upload

AI

POST /api/ai/search
POST /api/ai/ask

---

## Frontend Pages

Login
Signup
Dashboard
Knowledge
Upload
Ask AI
Profile

---

## Current UI

Sidebar navigation

Dashboard
Knowledge
Upload
Ask AI
Profile

Dashboard widgets

Total Items
Added This Week
Top Tags
Recent Titles

Knowledge page

Save Knowledge
Semantic Search
Saved Items

---

## Current Development Stage

About 70% complete.

Working

Frontend + backend integration
Knowledge saving
Document upload
Dashboard analytics

Remaining

Vector search integration
Ask AI RAG pipeline
Improved tag extraction
Knowledge graph connections

---

## Future Vision

AI Life Architect becomes a personal AI memory system that can

Remember everything the user saves
Answer questions using personal knowledge
Provide insights from accumulated knowledge
Act like a personal AI advisor