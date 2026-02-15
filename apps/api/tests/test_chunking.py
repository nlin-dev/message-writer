from app.services.chunking import chunk_text


def test_empty_string_returns_empty_list():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_returns_single_chunk():
    text = "This is a short sentence."
    result = chunk_text(text)
    assert result == [text]


def test_long_text_splits_at_sentence_boundaries():
    sentences = [f"Sentence number {i} is here." for i in range(20)]
    text = " ".join(sentences)
    result = chunk_text(text, max_chunk_size=100)
    assert len(result) > 1
    recombined = " ".join(result)
    assert recombined == text


def test_text_without_sentence_punctuation():
    text = "This is a long block of text without any sentence ending punctuation " * 20
    result = chunk_text(text.strip(), max_chunk_size=100)
    # Without sentence boundaries, entire text becomes one chunk
    assert len(result) == 1
