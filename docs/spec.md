# NLP and ML Intelligent Platform for Semantic Analysis, Classification and Predictive Modeling

## 1. Overview

A web platform that ingests unstructured text (CSV, JSON, TXT, API payloads), preprocesses it, runs semantic analysis (sentiment, entities, intent, topics), classifies text into categories, trains and evaluates ML models, predicts labels and trends, and shows everything on a dashboard and through REST APIs. Reviewers can correct predictions, and corrections feed retraining.

Prototype goal: a working end-to-end demo using pretrained models. No fine-tuning of transformers. Classical ML (Logistic Regression, Random Forest, XGBoost) is trained on top of BERT embeddings or TF-IDF features.

## 2. Users and Roles

- analyst: login, upload data, semantic analysis, classify, predict, submit feedback
- data_scientist: everything analyst can do, plus train and evaluate models
- manager: view dashboard and reports (read-only)
- admin: manage users, roles, model versions, system settings
- reviewer: review predictions, correct labels (feedback)
- external source: pushes data through the ingest API using an API key

## 3. Tech Stack

- Backend: Python 3.11, FastAPI, Uvicorn, SQLAlchemy 2, Alembic, Pydantic v2
- Database: SQLite for dev (SQLAlchemy URL configurable, PostgreSQL compatible)
- NLP: spaCy (en_core_web_sm) for tokenization, lemmatization, NER; sentence-transformers (all-MiniLM-L6-v2) for embeddings; transformers pipeline with distilbert-base-uncased-finetuned-sst-2-english for sentiment; scikit-learn TfidfVectorizer
- ML: scikit-learn (LogisticRegression, RandomForestClassifier), XGBoost, joblib for model persistence
- Auth: JWT (access tokens), bcrypt password hashing, role-based access control
- Security: AES-256-GCM encryption of stored text fields via the cryptography library, key from environment variable; TLS 1.3 terminated at a Caddy or Nginx reverse proxy in Docker
- Frontend: React 18, Vite, TypeScript, Tailwind CSS, Recharts, React Router, TanStack Query
- Packaging: Docker, docker-compose (backend, frontend, proxy)
- Tests: pytest, httpx

## 4. Project Structure

```
project-root/
  docs/spec.md
  design/            (PNG exports of every screen)
  backend/
    app/
      main.py
      config.py
      db.py
      models/        (SQLAlchemy models)
      schemas/       (Pydantic schemas)
      api/           (routers: auth, users, datasets, analysis, classify, models, predict, feedback, reports, ingest)
      services/      (preprocess, semantic, classifier, trainer, evaluator, predictor, trends, crypto, reports)
      core/          (security, deps, rbac)
    tests/
    storage/         (datasets, model artifacts)
    requirements.txt
    Dockerfile
  frontend/
    src/
    Dockerfile
  docker-compose.yml
  Caddyfile
  .env.example
```

## 5. Data Model

- User: id, email, name, password_hash, role, is_active, created_at
- ApiKey: id, user_id, key_hash, label, created_at
- Dataset: id, owner_id, name, source (upload or api), row_count, text_column, label_column nullable, time_column nullable, status, created_at
- Document: id, dataset_id, text_encrypted, label nullable, timestamp nullable, meta JSON, processed bool
- Analysis: id, document_id, sentiment_label, sentiment_score, entities JSON, intent, intent_score, topic_id, low_confidence bool, created_at
- Topic: id, dataset_id, keywords JSON, size
- ModelVersion: id, name, algorithm, feature_type (tfidf or bert), dataset_id, version, artifact_path, metrics JSON, status (trained, deployed, archived), created_by, created_at
- Prediction: id, model_version_id, document_id nullable, input_text_encrypted, predicted_label, confidence, probabilities JSON, created_by, created_at
- Feedback: id, prediction_id, corrected_label, comment, reviewer_id, status (submitted, draft), created_at
- AuditLog: id, user_id, action, detail, created_at

## 6. Functional Requirements

R1 Ingest: accept CSV, JSON, TXT upload and JSON API payloads. Validate type and size (max 20 MB, max 50,000 rows for prototype). Reject invalid files with a clear error. User selects text column, optional label column, optional time column.

R2 Semantic analysis: for each document produce sentiment (positive or negative with score), named entities (spaCy labels), intent, and topic. Intent is extracted by embedding similarity against a configurable list of intent labels (default: complaint, inquiry, praise, request, suggestion, other). Results with confidence below 0.6 are flagged low_confidence. Topics come from KMeans on embeddings (k configurable, default 6) with top TF-IDF keywords per cluster.

R3 Prediction: label prediction using a deployed classifier, and trend prediction: aggregate sentiment or label share per day/week from the time column, forecast the next N periods using an XGBoost regressor on lag features, with a simple moving-average fallback when data is short.

R4 REST APIs: all features available under /api/v1 with OpenAPI docs at /docs. Ingest and predict endpoints accept either a JWT or an API key header.

R5 Latency: single text inference (preprocess, embed, classify, sentiment) under 500 ms under normal load. Load all models once at startup, cache the embedder and spaCy pipeline, batch where possible. Include a latency test.

R6 Security: TLS via reverse proxy, AES-256-GCM on stored text, bcrypt passwords, JWT expiry, RBAC on every route, audit log of sensitive actions.

## 7. Use Cases

UC1 Login: email and password. Wrong password shows an error and allows retry. On success route by role to the dashboard.

UC2 Upload Data: pick file, map columns, preview first 10 rows, confirm. Invalid file rejected. Dataset stored and listed.

UC3 Preprocess Text (internal): clean (lowercase copy, strip HTML, URLs, extra whitespace), tokenize, lemmatize, remove stopwords, vectorize (TF-IDF and embeddings). Empty text is skipped and counted.

UC4 Semantic Analysis: user selects a dataset and analysis types (sentiment, entities, intent, topics), runs it, sees results and charts. Low confidence rows flagged. Results stored.

UC5 Classify Text: user selects a trained and deployed model, classifies a dataset or pasted text, sees classes with confidence. If no model exists, prompt to train one.

UC6 Train Model: data scientist selects labeled dataset, algorithm (Logistic Regression, Random Forest, XGBoost), feature type (TF-IDF or BERT embeddings), test split. Training runs as a background task with status polling. Model version saved. Failure is logged and shown.

UC7 Evaluate Model: run on held-out test split. Show accuracy, macro precision, macro recall, macro F1, per-class report, confusion matrix. Mark when F1 is below the 0.85 target and suggest retraining. Report stored.

UC8 Predict: submit single text or batch, choose a deployed model, see predicted label, confidence, probabilities. Bad input shows error. Predictions stored. Trend forecast available per dataset.

UC9 View Dashboard and Reports: KPI cards (documents, datasets, deployed model F1, predictions today), sentiment distribution, label distribution, topic sizes, trend line with forecast, recent low confidence items. Export report as CSV and PDF-ready HTML.

UC10 Manage Users and Models: admin creates, edits, deactivates users and sets roles; views model versions, deploys, archives or deletes them; sets confidence threshold and intent labels.

UC11 Submit Feedback: reviewer sees a prediction, corrects the label, optional comment, submits. On failure the draft is kept locally. Corrected labels can be added to the dataset and used for retraining.

## 8. API Endpoints (all under /api/v1)

- POST /auth/login, GET /auth/me
- GET/POST /users, PATCH /users/{id} (admin)
- POST /datasets/upload, GET /datasets, GET /datasets/{id}, GET /datasets/{id}/preview, DELETE /datasets/{id}
- POST /ingest (JSON payload, API key or JWT)
- POST /analysis/run, GET /analysis/{dataset_id}/results, GET /analysis/{dataset_id}/summary, GET /analysis/{dataset_id}/topics
- POST /analysis/text (single text, returns all semantic outputs)
- POST /models/train, GET /models, GET /models/{id}, POST /models/{id}/evaluate, POST /models/{id}/deploy, PATCH /models/{id}, DELETE /models/{id}
- POST /classify (dataset or text)
- POST /predict (text or batch), POST /predict/trend
- GET /predictions, POST /feedback, GET /feedback
- GET /reports/summary, GET /reports/export
- GET /health

## 9. Screens

Login, Dashboard, Datasets, Upload Data, Semantic Analysis, Classify Text, Train Model, Model Evaluation, Predict and Trends, Review and Feedback, Reports, Admin Users, Admin Models. The PNG for each screen is in the design/ folder and is the visual source of truth for layout, spacing, colors and components. Match it closely.

## 10. Non-Functional Requirements

- Inference under 500 ms per text block
- Models loaded once at startup
- Background tasks for training and bulk analysis
- Consistent JSON error format: {"error": {"code": "...", "message": "..."}}
- Input validation on every endpoint
- Config via environment variables, with .env.example
- Seed script creating one user per role with known dev passwords
- Sample dataset included for demo (about 500 labeled customer feedback rows with timestamps), generated by a script

## 11. Acceptance Criteria

- A user can log in, upload the sample CSV, run semantic analysis, train a model, see F1 and confusion matrix, deploy it, predict on new text, submit feedback, and see all of it on the dashboard
- Role restrictions enforced (analyst cannot train, manager cannot upload, only admin sees admin pages)
- Single-text prediction latency test passes under 500 ms on a warm server
- All pytest tests pass
- docker-compose up starts the full stack
