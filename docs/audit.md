# InsightText System Audit Report

Date: 2026-11-15
Auditor: Automated System Audit
Target: InsightText NLP and ML Platform
Baseline Reference: docs/spec.md and design/*.png

---

## 1. Executive Verdict

InsightText is a functional, well-structured demo prototype that executes real machine learning and natural language processing pipelines end to end. It is not production-ready. 

While core algorithms (spaCy, DistilBERT, SentenceTransformers, XGBoost, Scikit-Learn) and cryptographic security (AES-256-GCM) run genuinely on real data, substantial layers of the user experience rely on visual fallbacks, hardcoded strings, and non-functional UI controls designed to match the provided Figma/PNG mocks.

---

## 2. Requirements Assessment (R1 - R6)

### R1: Ingest
- Status: Partially working
- Component: `backend/app/api/datasets.py` (`upload_dataset`, `preview_uploaded_file`, `read_file_records`), `backend/app/api/ingest.py` (`ingest_data`)
- Audit Finding:
  - CSV, JSON, and TXT uploads work up to 20 MB and 50,000 rows. Ingest API accepts JSON with JWT and API keys.
  - What is missing: The UI dropzone claims `.xlsx` support, but `read_file_records()` does not parse Excel files and raises an `UNSUPPORTED_FILE_TYPE` error.

### R2: Semantic Analysis
- Status: Partially working
- Component: `backend/app/services/semantic.py` (`analyze_single_text`, `extract_topics`), `backend/app/api/analysis.py` (`run_dataset_analysis_task`)
- Audit Finding:
  - DistilBERT sentiment scoring, spaCy entity extraction, SentenceTransformer intent cosine similarity, and low-confidence flagging (< 0.6) run accurately on real text.
  - What is missing: In `run_dataset_analysis_task` (line 69), topic assignment for stored documents uses round-robin indexing (`i % len(topic_mapping)`) rather than assigning the actual cluster index returned by KMeans (`cluster_labels[i]`).

### R3: Prediction and Trends
- Status: Fully working
- Component: `backend/app/services/predictor.py` (`predict_and_store`), `backend/app/services/trends.py` (`compute_trend_forecast`, `forecast_series`)
- Audit Finding:
  - Single and batch text prediction returns real class probabilities and stores encrypted input. Time-series forecasting aggregates sentiment per date, constructs lag features, and fits an `XGBRegressor` with moving-average fallback when series length is under 5.

### R4: REST APIs
- Status: Fully working
- Component: `backend/app/main.py`, `backend/app/api/*`
- Audit Finding:
  - All endpoints are exposed under `/api/v1` with complete OpenAPI documentation at `/docs`. Endpoints accept both JWT Bearer tokens and `X-API-Key` headers.

### R5: Latency
- Status: Fully working
- Component: `backend/app/services/semantic.py`, `backend/tests/test_latency.py`
- Audit Finding:
  - All models (spaCy, MiniLM embedder, DistilBERT pipeline) are preloaded once into memory at application startup. Single-text prediction achieves sub-50 ms latency on a warm server, well within the 500 ms requirement.

### R6: Security
- Status: Fully working
- Component: `backend/app/services/crypto.py` (`CryptoService`), `backend/app/core/security.py`, `backend/app/core/rbac.py`, `Caddyfile`
- Audit Finding:
  - Raw text is encrypted before database insertion using AES-256-GCM with unique 12-byte initialization vectors. Passwords use bcrypt. Sensitive operations are recorded in `AuditLog`. Reverse proxy is configured for TLS 1.3 termination.

---

## 3. Use Case Assessment (UC1 - UC11)

### UC1: Login
- Status: Fully working
- Component: `backend/app/api/auth.py` (`login`), `frontend/src/pages/Login.tsx`
- Audit Finding: Authenticates email/password against bcrypt hashes, issues JWT tokens, displays error message on bad credentials, and routes by role.

### UC2: Upload Data
- Status: Partially working
- Component: `backend/app/api/datasets.py` (`upload_dataset`), `frontend/src/pages/UploadData.tsx`
- Audit Finding:
  - File upload, column mapping, and 10-row preview work for CSV and JSON.
  - What is missing: The "Download error report" button on the error screen is a stub that calls a browser `alert()`. The error table details are hardcoded in the frontend rather than parsed from structured backend validation responses. XLSX format is not implemented.

### UC3: Preprocess Text
- Status: Fully working
- Component: `backend/app/services/preprocess.py` (`clean_text`, `preprocess_text`)
- Audit Finding: Lowercases text, strips HTML tags, removes URLs, normalizes whitespace and punctuation, tokenizes, lemmatizes, and excludes stopwords.

### UC4: Semantic Analysis
- Status: Partially working
- Component: `backend/app/api/analysis.py` (`run_analysis`), `frontend/src/pages/SemanticAnalysis.tsx`
- Audit Finding:
  - Dataset analysis executes and stores sentiment, entities, and intent.
  - What is missing: Document topic ID assignment in bulk analysis is round-robin rather than cluster-mapped. The "Summary" tab in the UI displays hardcoded cards for "Positive" and "Complaint".

### UC5: Classify Text
- Status: Fully working
- Component: `backend/app/api/classify.py` (`classify`), `frontend/src/pages/ClassifyText.tsx`
- Audit Finding: Real-time classification for pasted text and datasets using deployed models. Initial screen displays static example cards before user triggers real inference.

### UC6: Train Model
- Status: Partially working
- Component: `backend/app/api/models.py` (`train_model`), `backend/app/services/trainer.py` (`train_model_sync`), `frontend/src/pages/TrainModel.tsx`
- Audit Finding:
  - Background training, feature extraction (TF-IDF and BERT embeddings), model fitting (XGBoost, Random Forest, Logistic Regression), and joblib serialization are genuine.
  - What is missing: The UI "Training progress" card hardcodes "Epoch 6 of 10", "Estimated 3 min remaining", and a static 60% progress bar instead of streaming real progress from the backend.

### UC7: Evaluate Model
- Status: Fully working
- Component: `backend/app/api/models.py` (`evaluate_model`), `backend/app/services/evaluator.py`, `frontend/src/pages/ModelEvaluation.tsx`
- Audit Finding: Held-out evaluation computes genuine accuracy, macro precision, recall, F1, per-class metrics, and confusion matrix.

### UC8: Predict
- Status: Fully working
- Component: `backend/app/api/predict.py`, `backend/app/services/predictor.py`, `frontend/src/pages/PredictTrends.tsx`
- Audit Finding: Single text, batch text, and time-series forecasting query genuine models and persist encrypted records.

### UC9: View Dashboard and Reports
- Status: Hardcoded or fake data
- Component: `backend/app/services/reports.py` (`get_dashboard_summary`), `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/Reports.tsx`
- Audit Finding:
  - While total document and dataset counts come from database queries, KPI rate tags (`+12.4% this week`, `2 added this month`, `+8.1% vs yesterday`) are hardcoded in the frontend JSX.
  - In `Dashboard.tsx`, if database counts return 0, the UI falls back to hardcoded numbers (`248,310` and `3,482`).
  - In `Reports.tsx`, the Date Range selector is purely visual and ignored by the API. The "Key findings" section consists of static hardcoded bullet points.

### UC10: Manage Users and Models
- Status: Fully working
- Component: `backend/app/api/users.py`, `backend/app/api/models.py`, `backend/app/api/settings.py`, `frontend/src/pages/AdminUsers.tsx`, `frontend/src/pages/AdminModels.tsx`
- Audit Finding: User creation, editing, activation toggle, deletion, model deployment, archival, deletion, and system threshold configuration operate on real database state.

### UC11: Submit Feedback
- Status: Partially working
- Component: `backend/app/api/feedback.py` (`submit_feedback`), `frontend/src/pages/ReviewFeedback.tsx`
- Audit Finding:
  - Reviewers can view predictions, submit corrected labels, and update linked document labels.
  - What is missing: Predictions made on arbitrary text without a dataset document link (`document_id = None`) are not appended to any dataset for retraining. The "Draft saved {time}" badge is an in-memory client timer that does not persist across page refreshes.

---

## 4. Deep-Dive Findings

### Frontend Screens with Hardcoded or Placeholder Data
1. `Dashboard.tsx`: Fallbacks for KPI numbers (`248,310`, `3,482`), hardcoded delta badges (`+12.4%`, `+8.1%`), and hardcoded label/topic percentage defaults.
2. `SemanticAnalysis.tsx`: Hardcoded "Positive" and "Complaint" cards on the Summary tab.
3. `TrainModel.tsx`: Hardcoded "Epoch 6 of 10" and "Estimated 3 min remaining" in the progress indicator.
4. `ReviewFeedback.tsx`: Fallback review count of `128` when prediction queries return empty.
5. `Reports.tsx`: Entire "Key findings" list is hardcoded static HTML.
6. `Layout.tsx`: Topbar notification badge is hardcoded to `"3"`.

### Dead or Unwired Controls
1. `Layout.tsx`: Header search input redirects to `/predict?q=...` instead of searching datasets or models.
2. `UploadData.tsx`: "Download error report" button triggers a JavaScript `alert()`.
3. `Reports.tsx`: Date range dropdown (`Oct 1 – Nov 14, 2026`) is not sent to the backend.
4. `Login.tsx`: "Forgot password?" triggers a JavaScript `alert()` with demo credentials.

### Backend Static Fallbacks
1. `reports.py` (`get_dashboard_summary`): If the database has no analyses, it injects fallback dictionaries for sentiment (`52% Positive, 28% Neutral, 20% Negative`) and categories (`38% Billing, 30% Delivery, 22% Product quality, 10% Support`).
2. `trends.py` (`compute_trend_forecast`): If no timestamped documents exist, it generates a synthetic 14-day sequence starting at 0.18.

### Pipeline Integrity: Real vs Synthetic
- Ingestion, embedding, classification, and forecasting algorithms execute real mathematical computations.
- The 0.85 macro F1 score target is met easily (achieving 0.87 - 0.99) solely because the sample dataset (`generate_data.py`) contains non-overlapping keyword sets across 4 classes. On real-world noisy feedback with ambiguous customer wording, TF-IDF classifiers without fine-tuning will likely drop below 0.80 F1.

### Test Suite Weaknesses
1. Background tasks are partially bypassed in tests: `test_e2e_flow.py` calls `train_model_sync()` directly rather than polling the background task thread.
2. Boundary assertions are missing: Ingestion tests upload 2 rows; they do not test the 20 MB size boundary or the 50,000 row rejection threshold.
3. Latency test only benchmarks TF-IDF + Logistic/XGBoost inference. Running single-text inference with BERT embeddings on CPU under load is not benchmarked.

---

## 5. Screen Discrepancies vs design/ PNGs

| Screen | Design PNG | Implementation Discrepancy |
|---|---|---|
| 01 Login | `01-login.png` | Matched closely; "Forgot password?" is an alert rather than a reset modal. |
| 02 Dashboard | `02-dashboard.png` | Layout matched; delta metrics (+12.4%) are hardcoded strings. |
| 03 Datasets | `03-datasets.png` | Matched closely; table actions and status pills functional. |
| 04 Upload Data | `04-upload-data.png` | Dropzone specifies XLSX, which backend rejects. |
| 05 Semantic Analysis | `05-semantic-analysis.png` | Summary tab lacks dynamic aggregated intent breakdown. |
| 06 Classify Text | `06-classify-text.png` | Matched closely; initial view shows mockup cards prior to search. |
| 07 Train Model | `07-train-model.png` | Progress card shows static text instead of actual training epochs. |
| 08 Model Evaluation | `08-model-evaluation.png` | Matched closely; matrix and class report render real metrics. |
| 09 Predict Trends | `09-predict-trends.png` | Matched closely; chart renders real XGBoost lag forecast. |
| 10 Review Feedback | `10-review-feedback.png` | Matched closely; draft saving is an in-memory timer. |
| 11 Reports | `11-reports.png` | Key findings are static HTML; date filter is unwired. |
| 12 Admin Users | `12-admin-users.png` | Matched closely; user modal functional. |
| 13 Admin Models | `13-admin-models.png` | Matched closely; model lifecycle and threshold controls functional. |
| 14 Empty Dashboard | `14-empty-dashboard.png` | Fully matched when database has 0 datasets. |
| 15 Upload Error | `15-upload-error.png` | Layout matched; error table data is mocked on upload failure. |

---

## 6. Prioritized Remediation List

1. High Priority (Data Integrity):
   - Fix topic assignment in `run_dataset_analysis_task` to map documents to their actual KMeans cluster index instead of round-robin `i % k`.
   - Update `feedback.py` so that reviewer corrections on ad-hoc predictions create or update labeled records in a dedicated retraining dataset.
   - Remove hardcoded fallback data in `reports.py` and `Dashboard.tsx` so the dashboard displays genuine zeros when empty rather than mockup numbers.

2. Medium Priority (Functional Completeness):
   - Add `.xlsx` support using `openpyxl` or remove XLSX references from the upload interface.
   - Wire the date range filter in `Reports.tsx` to pass start and end dates to `/reports/summary` and `/predict/trend`.
   - Implement real progress reporting (or WebSockets / SSE) for the training progress card instead of hardcoding "Epoch 6 of 10".

3. Low Priority (Polish):
   - Replace JavaScript `alert()` calls on "Forgot password" and "Download error report" with dedicated modal dialogs and file downloads.
   - Implement real document/model search for the top navigation bar.

---

## 7. Conclusion

InsightText is an advanced **demo prototype**. Its architecture, security, NLP pipelines, and classical ML routines are genuinely implemented and functional. However, the presence of hardcoded fallback numbers, static report insights, un-wired UI controls, and a synthetic evaluation dataset means it cannot be categorized as closer to production without resolving the data-integrity and UI-wiring items listed above.
