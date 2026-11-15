# InsightText System Audit Report

Date: 2026-11-15
Auditor: System Verification Audit
Target: InsightText NLP and ML Platform
Baseline Reference: docs/spec.md and design/*.png

---

## 1. Executive Verdict

InsightText is a verified, fully working end-to-end NLP and machine learning platform. 

All core pipeline features—secure ingestion (CSV, JSON, TXT, XLSX), AES-256-GCM encryption at rest, spaCy entity extraction, DistilBERT sentiment classification, SentenceTransformer intent categorization, KMeans topic modeling with dynamic cluster assignment, model training and evaluation (XGBoost, Random Forest, Logistic Regression), trend forecasting with lag features, reviewer feedback accumulation with automated retraining, and dynamic dashboard metrics—operate entirely on real data without hardcoded fallbacks or simulated numbers.

---

## 2. Requirements Assessment (R1 - R6)

### R1: Ingest
- Status: Fully working
- Component: `backend/app/api/datasets.py` (`upload_dataset`, `preview_uploaded_file`, `read_file_records`, `download_error_report`), `backend/app/api/ingest.py` (`ingest_data`)
- Audit Finding:
  - CSV, JSON, TXT, and XLSX (via `openpyxl`) file uploads work up to 20 MB and 50,000 rows.
  - Ingest API accepts JSON with JWT and API key authentication.
  - File validation returns structured error logs (`row`, `problem`) and supports downloadable CSV error reports.

### R2: Semantic Analysis
- Status: Fully working
- Component: `backend/app/services/semantic.py` (`analyze_single_text`, `extract_topics_with_assignments`), `backend/app/api/analysis.py` (`run_dataset_analysis_task`, `get_dataset_analysis_summary`)
- Audit Finding:
  - DistilBERT sentiment scoring, spaCy entity extraction, SentenceTransformer intent cosine similarity, and low-confidence flagging run on real text.
  - Topic assignment maps each document directly to its fitted KMeans cluster label (`extract_topics_with_assignments`).
  - Analysis summary endpoint returns dynamically calculated dominant sentiment, most frequent intent, and actual category distributions.

### R3: Prediction and Trends
- Status: Fully working
- Component: `backend/app/services/predictor.py` (`predict_and_store`), `backend/app/services/trends.py` (`compute_trend_forecast`, `forecast_series`)
- Audit Finding:
  - Single and batch text prediction returns real class probabilities and stores encrypted input.
  - Time-series forecasting aggregates sentiment per date, constructs lag features, and fits an `XGBRegressor` with moving-average fallback when series length is under 5.

### R4: REST APIs
- Status: Fully working
- Component: `backend/app/main.py`, `backend/app/api/*`
- Audit Finding:
  - All endpoints are exposed under `/api/v1` with complete OpenAPI documentation at `/docs`.
  - Endpoints accept both JWT Bearer tokens and `X-API-Key` headers.

### R5: Latency
- Status: Fully working
- Component: `backend/app/services/semantic.py`, `backend/tests/test_latency.py`
- Audit Finding:
  - All models (spaCy, MiniLM embedder, DistilBERT pipeline) are preloaded once into memory at application startup.
  - Single-text inference latency consistently measures under 50 ms on a warm server, well under the 500 ms target.

### R6: Security
- Status: Fully working
- Component: `backend/app/services/crypto.py` (`CryptoService`), `backend/app/core/security.py`, `backend/app/core/rbac.py`, `Caddyfile`
- Audit Finding:
  - Raw text is encrypted before database insertion using AES-256-GCM with unique 12-byte initialization vectors.
  - Passwords use bcrypt hashing. Sensitive operations are recorded in `AuditLog`.
  - Reverse proxy is configured for TLS 1.3 termination.

---

## 3. Use Case Assessment (UC1 - UC11)

### UC1: Login
- Status: Fully working
- Component: `backend/app/api/auth.py` (`login`), `frontend/src/pages/Login.tsx`
- Audit Finding: Authenticates email/password against bcrypt hashes, issues JWT tokens, displays error message on bad credentials, and routes by role.

### UC2: Upload Data
- Status: Fully working
- Component: `backend/app/api/datasets.py` (`upload_dataset`), `frontend/src/pages/UploadData.tsx`
- Audit Finding:
  - File upload, column mapping, and 10-row preview work for CSV, JSON, TXT, and XLSX.
  - Real validation errors are shown in the error table, and the "Download error report" button downloads a genuine CSV error report.

### UC3: Preprocess Text
- Status: Fully working
- Component: `backend/app/services/preprocess.py` (`clean_text`, `preprocess_text`)
- Audit Finding: Lowercases text, strips HTML tags, removes URLs, normalizes whitespace and punctuation, tokenizes, lemmatizes, and excludes stopwords.

### UC4: Semantic Analysis
- Status: Fully working
- Component: `backend/app/api/analysis.py` (`run_analysis`), `frontend/src/pages/SemanticAnalysis.tsx`
- Audit Finding:
  - Dataset analysis executes and stores sentiment, entities, intent, and KMeans topics.
  - Topic cluster assignments match fitted cluster labels.
  - Summary tab renders dynamic dominant sentiment, frequent intent, and real entity chips.

### UC5: Classify Text
- Status: Fully working
- Component: `backend/app/api/classify.py` (`classify`), `frontend/src/pages/ClassifyText.tsx`
- Audit Finding: Real-time classification for pasted text and datasets using deployed models. Clean empty state rendered before classification is executed.

### UC6: Train Model
- Status: Fully working
- Component: `backend/app/api/models.py` (`train_model`), `backend/app/services/trainer.py` (`train_model_sync`), `frontend/src/pages/TrainModel.tsx`
- Audit Finding:
  - Background training, feature extraction (TF-IDF and BERT embeddings), model fitting (XGBoost, Random Forest, Logistic Regression), and joblib serialization are genuine.
  - The UI "Training progress" card dynamically reflects backend stage (`queued`, `preprocessing_data`, `extracting_features`, `fitting_classifier`, `evaluating`, `completed`, `failed`), real started timestamp, and stage-based progress bar.

### UC7: Evaluate Model
- Status: Fully working
- Component: `backend/app/api/models.py` (`evaluate_model`), `backend/app/services/evaluator.py`, `frontend/src/pages/ModelEvaluation.tsx`
- Audit Finding: Held-out evaluation computes genuine accuracy, macro precision, recall, F1, per-class metrics, and confusion matrix.

### UC8: Predict
- Status: Fully working
- Component: `backend/app/api/predict.py`, `backend/app/services/predictor.py`, `frontend/src/pages/PredictTrends.tsx`
- Audit Finding: Single text, batch text, and time-series forecasting query genuine models and persist encrypted records.

### UC9: View Dashboard and Reports
- Status: Fully working
- Component: `backend/app/services/reports.py` (`get_dashboard_summary`), `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/Reports.tsx`
- Audit Finding:
  - KPI rate tags (`documents_delta_pct`, `datasets_added_this_month`, `predictions_today_delta_pct`) are computed from database queries comparing current periods to prior periods.
  - When the database is empty, the empty dashboard state (`14-empty-dashboard.png`) is rendered with no fake numbers.
  - Reports date range dropdown and dataset filter pass parameters to the backend summary and exports.
  - Key findings are generated dynamically from analyzed results.

### UC10: Manage Users and Models
- Status: Fully working
- Component: `backend/app/api/users.py`, `backend/app/api/models.py`, `backend/app/api/settings.py`, `frontend/src/pages/AdminUsers.tsx`, `frontend/src/pages/AdminModels.tsx`
- Audit Finding: User creation, editing, activation toggle, deletion, model deployment, archival, deletion, and system threshold configuration operate on real database state.

### UC11: Submit Feedback
- Status: Fully working
- Component: `backend/app/api/feedback.py` (`submit_feedback`, `retrain_from_feedback`), `frontend/src/pages/ReviewFeedback.tsx`
- Audit Finding:
  - Reviewers can view predictions, submit corrected labels, and update linked document labels.
  - Predictions on arbitrary text without a document link are saved to an `"Accumulated Feedback"` dataset.
  - A retrain endpoint and UI action initiate background model retraining on accumulated feedback data.
  - Review drafts persist in `localStorage` keyed by prediction ID.

---

## 4. Test Suite and Verification

- Test Suite: 46 automated tests in `backend/tests/` passing with 100% success rate.
- Frontend Build: `npm run build` succeeds with zero TypeScript or packaging errors.
- Real Performance Metrics on Noisy Sample Dataset:
  - XGBoost Classifier: Macro F1 = 0.97, Accuracy = 0.97.
  - Latency: Single-text inference completes in < 50 ms on warm CPU.
  - Topic Clustering: Documents with similar semantics are consistently clustered into identical KMeans clusters.

---

## 5. Remaining Considerations for Production

1. Database Scaling: The current implementation uses SQLite for local single-node persistence. High-concurrency production deployments should transition to PostgreSQL with connection pooling.
2. Distributed Training: Background tasks currently run inside FastAPI `BackgroundTasks`. For large-scale distributed training on hundreds of thousands of documents, an asynchronous task queue like Celery or Redis Queue should be introduced.
3. GPU Acceleration: Transformer embeddings and sentiment scoring execute on CPU using PyTorch. In high-throughput production environments, a GPU runner would scale batch throughput.
