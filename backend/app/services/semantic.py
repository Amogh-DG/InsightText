from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from app.config import settings
from app.services.preprocess import clean_text, get_spacy_nlp

nlp = get_spacy_nlp()
embedder = SentenceTransformer("all-MiniLM-L6-v2")
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", truncation=True, max_length=512)

default_intent_labels = settings.INTENT_LABELS
default_intent_embeddings = embedder.encode(default_intent_labels, normalize_embeddings=True)

def analyze_sentiment(text: str) -> Dict[str, Any]:
    cleaned = clean_text(text)
    if not cleaned:
        return {"label": "Neutral", "score": 0.5}
    truncated = cleaned[:512]
    result = sentiment_pipeline(truncated)[0]
    raw_label = result["label"].upper()
    score = float(result["score"])
    
    if score < 0.58:
        mapped_label = "Neutral"
    elif "POS" in raw_label:
        mapped_label = "Positive"
    else:
        mapped_label = "Negative"
        
    return {"label": mapped_label, "score": round(score, 4)}

def extract_entities(text: str) -> List[Dict[str, str]]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    doc = nlp(cleaned)
    entities = []
    seen = set()
    for ent in doc.ents:
        normalized = ent.text.strip()
        if normalized and (normalized, ent.label_) not in seen:
            seen.add((normalized, ent.label_))
            entities.append({"text": normalized, "label": ent.label_})
    return entities

def classify_intent(text: str, intent_labels: Optional[List[str]] = None) -> Dict[str, Any]:
    cleaned = clean_text(text)
    if not cleaned:
        return {"intent": "other", "score": 0.0}
    
    if not intent_labels or intent_labels == default_intent_labels:
        labels = default_intent_labels
        intent_embeds = default_intent_embeddings
    else:
        labels = intent_labels
        intent_embeds = embedder.encode(labels, normalize_embeddings=True)
        
    text_embed = embedder.encode([cleaned], normalize_embeddings=True)[0]
    similarities = np.dot(intent_embeds, text_embed)
    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])
    
    return {
        "intent": labels[best_idx],
        "score": round(max(0.0, min(1.0, best_score)), 4)
    }

def get_text_embeddings(texts: List[str]) -> np.ndarray:
    cleaned_texts = [clean_text(t) if clean_text(t) else "empty" for t in texts]
    return embedder.encode(cleaned_texts, normalize_embeddings=True, show_progress_bar=False)

def extract_topics_with_assignments(texts: List[str], num_topics: int = 6) -> Tuple[List[Dict[str, Any]], List[int]]:
    valid_texts = [clean_text(t) if clean_text(t) else "empty feedback" for t in texts]
    if not valid_texts:
        return [], []
    
    n_samples = len(valid_texts)
    k = max(1, min(num_topics, n_samples))
    if k == 1 or n_samples < 3:
        topics = [{"topic_id": 0, "keywords": ["general", "feedback", "service"], "size": n_samples}]
        assignments = [0] * n_samples
        return topics, assignments
    
    embeddings = embedder.encode(valid_texts, normalize_embeddings=True, show_progress_bar=False)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
    cluster_labels = kmeans.fit_predict(embeddings)
    
    vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform(valid_texts)
        feature_names = np.array(vectorizer.get_feature_names_out())
    except Exception:
        feature_names = np.array(["feedback", "service", "system", "request", "issue"])
        tfidf_matrix = None

    topics = []
    for cluster_id in range(k):
        indices = np.where(cluster_labels == cluster_id)[0]
        cluster_size = int(len(indices))
        keywords = []
        if tfidf_matrix is not None and cluster_size > 0 and len(feature_names) > 0:
            cluster_tfidf = tfidf_matrix[indices].mean(axis=0)
            cluster_tfidf_arr = np.asarray(cluster_tfidf).flatten()
            top_kw_indices = cluster_tfidf_arr.argsort()[::-1][:5]
            keywords = [str(feature_names[i]) for i in top_kw_indices if cluster_tfidf_arr[i] > 0]
        if not keywords:
            keywords = [f"topic_{cluster_id + 1}", "issue", "feedback"]
        topics.append({
            "topic_id": cluster_id,
            "keywords": keywords,
            "size": cluster_size
        })
    return topics, cluster_labels.tolist()

def extract_topics(texts: List[str], num_topics: int = 6) -> List[Dict[str, Any]]:
    topics, _ = extract_topics_with_assignments(texts, num_topics)
    return topics

def analyze_single_text(text: str, threshold: float = settings.CONFIDENCE_THRESHOLD, intent_labels: Optional[List[str]] = None) -> Dict[str, Any]:
    cleaned = clean_text(text)
    sentiment = analyze_sentiment(cleaned)
    entities = extract_entities(cleaned)
    intent = classify_intent(cleaned, intent_labels)
    low_confidence = (sentiment["score"] < threshold) or (intent["score"] < threshold)
    
    return {
        "text": cleaned,
        "sentiment_label": sentiment["label"],
        "sentiment_score": sentiment["score"],
        "entities": entities,
        "intent": intent["intent"],
        "intent_score": intent["score"],
        "low_confidence": low_confidence
    }
