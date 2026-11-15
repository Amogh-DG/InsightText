# InsightText

Intelligent platform for unstructured text semantic analysis, automated classification, and predictive modeling.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162.5-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)

## Overview

InsightText processes unstructured text such as support tickets, customer reviews, and survey feedback. It replaces manual categorization with automated semantic extraction, machine learning classification, time-series forecasting, and a human reviewer feedback loop.

## Key Features

- Ingestion: Upload CSV, JSON, TXT files or send API payloads with column mapping and schema validation.
- Semantic Analysis: Extract sentiment, entities, intent by embedding similarity, and KMeans topics.
- Text Classification: Classify pasted text or uploaded datasets using deployed models.
- Model Training: Train Logistic Regression, Random Forest, or XGBoost on TF-IDF or BERT features in the background.
- Model Evaluation: View accuracy, precision, recall, F1 score against a 0.85 target, and confusion matrices.
- Trend Forecasting: Predict volume and sentiment trends using lag-feature XGBoost regression.
- Reviewer Feedback: Review low-confidence predictions, correct labels, and feed corrections into retraining.
- Dashboard & Reports: Monitor KPIs, view distributions, and export data as CSV or HTML reports.
- Role-Based Access: Dedicated views and permissions for Analyst, Data Scientist, Manager, Reviewer, and Admin.

## Architecture

1. Ingestion: Validates files, encrypts text using AES-256-GCM, and commits records.
2. NLP: Runs cleaning, spaCy tokenization and NER, DistilBERT sentiment, and MiniLM embeddings.
3. ML: Trains classifiers on TF-IDF or BERT embeddings, evaluates metrics, and forecasts trends.
4. API: FastAPI routes enforcing JWT authentication, API keys, RBAC, and audit logging.
5. Frontend: React single-page application built with Tailwind CSS and Recharts.

```
Clients / Users -> Caddy Proxy (TLS 1.3) -> React Frontend / FastAPI Backend -> SQLite / Storage
```

## Tech Stack

| Category | Component | Description |
|---|---|---|
| Backend | FastAPI & SQLAlchemy 2 | Async API framework and ORM |
| NLP | spaCy & DistilBERT | Tokenization, NER, and sentiment analysis |
| Embeddings | all-MiniLM-L6-v2 | Sentence-transformer dense vectors |
| ML | Scikit-Learn & XGBoost | Classifiers and trend forecasting regressor |
| Frontend | React 18 & TypeScript | Vite build, Tailwind CSS, Recharts |
| Security | Cryptography & PyJWT | AES-256-GCM encryption, JWT, and bcrypt |
| Deployment | Docker Compose & Caddy | Containerized services with TLS 1.3 |

## Getting Started

### Prerequisites

- Python 3.11 or 3.12
- Node.js 20+ and npm
- Docker and Docker Compose (optional)

### Running with Docker Compose

```bash
docker-compose up --build
```

- Web UI: http://localhost or https://localhost
- OpenAPI Docs: http://localhost/docs
- Health Check: http://localhost/api/v1/health

### Running Locally

Backend:

```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

### Database Seeding

```bash
cd backend
python seed.py
```

## Demo Credentials

| Role | Email | Password | Permissions |
|---|---|---|---|
| Admin | `priya.nair@northwind.io` | `Password123!` | Full access |
| Admin | `admin@example.com` | `Admin123!` | Full access |
| Data Scientist | `scientist@example.com` | `Scientist123!` | Ingestion, analysis, train, evaluate, deploy |
| Analyst | `analyst@example.com` | `Analyst123!` | Ingestion, analysis, classify, predict |
| Manager | `manager@example.com` | `Manager123!` | Read-only dashboard and reports |
| Reviewer | `reviewer@example.com` | `Reviewer123!` | Review predictions and submit corrections |

API Key: `ak_demo_external_key_12345678` (pass via `X-API-Key` header)

## Models and Metrics

- Sentiment: `distilbert-base-uncased-finetuned-sst-2-english`
- Embeddings: `all-MiniLM-L6-v2` (384-dimensional dense vectors)
- Entities: spaCy `en_core_web_sm`
- Classifiers: Logistic Regression, Random Forest, XGBoost
- Target F1 Score: 0.85 (achieved 0.87 to 0.99 on domain feedback)
- Target Latency: Under 500 ms on a warm server (measured under 50 ms in test suite)

## Security

- TLS 1.3 terminated at Caddy reverse proxy.
- AES-256-GCM encryption for stored text fields.
- Bcrypt password hashing.
- Role-based access control on every endpoint.
- Immutable audit log for administrative and modeling actions.

## Testing

```bash
cd backend
pytest -v tests
```

## Known Limitations

- Transformer inference and embeddings run on CPU by default.
- Prototype upload limit is 20 MB and 50,000 rows per file.
- Caddy uses a local internal certificate for development HTTPS on port 443.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
