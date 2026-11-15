from app.services.preprocess import clean_text, preprocess_text

def test_clean_text_html_and_urls():
    raw = "<p>Hello <b>World</b>! Check https://example.com for info.</p>"
    cleaned = clean_text(raw)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "https://" not in cleaned
    assert "Hello World! Check for info." in cleaned

def test_clean_text_whitespace():
    raw = "   Multiple   spaces   and \n newlines \t here.   "
    cleaned = clean_text(raw)
    assert cleaned == "Multiple spaces and newlines here."

def test_preprocess_tokens_and_lemmas():
    raw = "The customer service representatives are delivering packages rapidly."
    cleaned, tokens, lemma_text = preprocess_text(raw)
    assert "customer" in tokens or "service" in tokens
    assert "the" not in tokens
    assert "are" not in tokens
    assert len(tokens) > 0

def test_preprocess_empty_text():
    cleaned, tokens, lemma_text = preprocess_text("    ")
    assert cleaned == ""
    assert tokens == []
    assert lemma_text == ""
