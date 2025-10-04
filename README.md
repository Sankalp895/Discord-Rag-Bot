🤖 Discord RAG Bot

A Discord bot powered by FastAPI and RAG (Retrieval-Augmented Generation) to answer user queries, ingest documents, and collect feedback.
It connects Discord with a backend service that retrieves knowledge, generates AI-based answers, and logs user interactions.

🚀 Features

Ask questions directly in Discord using !ask <your question>.

Retrieval-Augmented Generation (RAG) for more accurate and context-aware responses.

Document ingestion: Upload files (PDF/DOCX/FAQ JSON) to enrich the knowledge base.
Feedback collection: Users can rate answers with ⭐ reactions (1–5).
Logging & Observability: Tracks requests, errors, and response quality.
Dockerized deployment: Run locally or on the cloud easily.

🛠️ Tech Stack

Backend: FastAPI
Discord Bot: discord.py
RAG Pipeline: Sentence Transformers
, FAISS
Containerization: Docker
Deployment Options: Deployment Options: Render, Railway, Azure, or local Docker(Haven't deployed I'm sorry, because of free tier limitation)

🔗 API Endpoints

POST /api/rag-query → Ask a question
POST /api/feedback → Submit feedback
POST /api/ingest → Ingest new documents

📊 Feedback & Observability

⭐ Rating system (1–5) directly in Discord
Logs key events: queries, responses, errors, latency
Metrics can be exported to Prometheus/Grafana (optional)

