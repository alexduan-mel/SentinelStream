# SentinelStream

SentinelStream is an event-driven market news intelligence system that combines
Java-based execution components with Python-based AI analysis.

The system focuses on processing U.S. equities news, analyzing it with
LLM-based models, and turning unstructured information into structured,
inspectable analysis results that can be stored, visualized, and evaluated.

Rather than treating AI outputs as black-box predictions, SentinelStream is
designed to make each step in the pipeline explicit and traceable, allowing
the system to be understood, extended, and improved over time.

---

## Motivation

This project started from a personal interest in understanding how news-driven
market analysis can be built as a real system, rather than as isolated scripts
or experiments.

While experimenting with LLM-based analysis, it became clear that generating
a result is only part of the problem. How analysis results should be structured,
how their reliability can be assessed, and how downstream components consume
them are equally important questions.

SentinelStream is built as a way to explore these questions in practice.
By implementing an end-to-end pipeline—from news ingestion, to AI-based analysis,
to structured storage and visualization—the project helps turn abstract ideas
about AI-driven analysis into something concrete and observable.

The system is designed to be modular and customizable, so that individual
components can evolve independently. Correctness, clarity, and extensibility
are treated as primary goals from the beginning.

---

## Architecture Overview

SentinelStream follows an event-driven architecture that separates data ingestion,
AI analysis, and downstream processing into loosely coupled components.

This separation allows the system to remain flexible while keeping each part
simple and focused on a clear responsibility.

### Core Components

- **Java Core (Spring Boot, Java 21)**  
  Handles execution-oriented tasks such as coordinating downstream actions
  and managing integration points.

- **Python AI Service (FastAPI)**  
  Performs news analysis using LLMs and produces structured analysis results.

- **Redis (Event Bridge and Cache)**  
  Acts as an asynchronous communication layer between services.

- **TimescaleDB (PostgreSQL)**  
  Stores news events, analysis results, and related metadata for querying
  and visualization.

- **Storage Worker**  
  A consumer service responsible for persisting events in a reliable manner.

- **Dashboard (Streamlit, planned)**  
  A visualization layer for inspecting news items and their corresponding
  AI analysis results.

### Data Flow

1. Market news is ingested from an external source and normalized into
   structured news events.
2. The Python AI service analyzes the news content and generates structured
   analysis results.
3. Analysis results are published through the event pipeline.
4. All data is persisted in the database for inspection and later evaluation.
5. The dashboard reads from the database to present human-readable views.

---

## Key Features

### Event-Driven Pipeline
Components communicate asynchronously, which keeps the system flexible and
reduces tight coupling between services.

### Structured AI Analysis
LLM outputs are converted into structured formats that include extracted
entities, sentiment, confidence, and short reasoning summaries.

### Verification-Oriented Design
The system is designed to support explicit verification and filtering rules,
making it easier to reason about which analysis results should be trusted.

### Persistence and Traceability
All inputs and outputs are stored with clear identifiers, allowing individual
items to be traced through the entire pipeline.

### Visualization (Planned)
A lightweight dashboard is planned to make analysis results easier to explore
and understand without directly querying the database.

---

## Local Development

The system can be started locally using Docker Compose.

```bash
docker compose up --build

# Check Java service
curl http://localhost:8080

# Check Python AI service
curl http://localhost:8000

# Monitor storage worker logs
docker compose logs -f storage-worker

# Inspect Redis queue
docker compose exec redis redis-cli LLEN news_ingest_queue

# Inspect database
docker compose exec timescaledb psql -U sentinel -d sentinelstream \
  -c "SELECT COUNT(*) FROM news_events;"




