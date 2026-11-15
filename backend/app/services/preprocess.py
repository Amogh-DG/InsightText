import re
from typing import List, Tuple
import spacy

nlp = spacy.load("en_core_web_sm")

def clean_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([?.!,:;])", r"\1", text)
    return text.strip()

def preprocess_text(raw_text: str) -> Tuple[str, List[str], str]:
    cleaned = clean_text(raw_text)
    if not cleaned:
        return "", [], ""
    doc = nlp(cleaned.lower())
    tokens = [
        token.lemma_
        for token in doc
        if not token.is_stop and not token.is_punct and not token.is_space and len(token.text.strip()) > 1
    ]
    lemma_text = " ".join(tokens)
    return cleaned, tokens, lemma_text

def get_spacy_nlp():
    return nlp
