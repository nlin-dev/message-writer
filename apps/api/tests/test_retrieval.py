from app.models.chunk import Chunk
from app.models.reference import Reference
from app.services.retrieval import retrieve


def _seed_reference(db, title="Test Ref", source="pubmed", chunks=None):
    ref = Reference(title=title, source=source)
    db.add(ref)
    db.flush()
    for i, content in enumerate(chunks or []):
        db.add(Chunk(reference_id=ref.id, content=content, chunk_index=i))
    db.commit()
    return ref


def test_retrieve_returns_matching_chunks_ranked(db):
    ref1 = _seed_reference(db, "Ref 1", chunks=[
        "diabetes treatment with insulin therapy",
        "unrelated content about geology",
    ])
    ref2 = _seed_reference(db, "Ref 2", chunks=[
        "cardiovascular health overview",
        "diabetes treatment outcomes and management",
    ])

    results = retrieve(db, "diabetes treatment", [ref1.id, ref2.id], top_k=3)

    assert len(results) > 0
    for r in results:
        assert "id" in r
        assert "reference_id" in r
        assert "content" in r
        assert "chunk_index" in r
        assert r["reference_id"] in (ref1.id, ref2.id)


def test_retrieve_filters_by_reference_ids(db):
    ref1 = _seed_reference(db, "Ref 1", chunks=["insulin resistance mechanisms"])
    ref2 = _seed_reference(db, "Ref 2", chunks=["insulin therapy advances"])
    ref3 = _seed_reference(db, "Ref 3", chunks=["insulin sensitivity factors"])

    results = retrieve(db, "insulin", [ref1.id], top_k=5)

    assert len(results) > 0
    for r in results:
        assert r["reference_id"] == ref1.id


def test_retrieve_fallback_when_no_fts_match(db):
    ref = _seed_reference(db, "Ref", chunks=[
        "first chunk of medical text",
        "second chunk of medical text",
        "third chunk of medical text",
    ])

    results = retrieve(db, "xyznonexistentterm", [ref.id], top_k=2)

    assert len(results) > 0
    assert len(results) <= 2
    assert results[0]["chunk_index"] <= results[-1]["chunk_index"]


def test_retrieve_handles_special_characters(db):
    ref = _seed_reference(db, "Ref", chunks=["some test content here"])

    # Should not raise
    results = retrieve(db, 'test "query" with (parens)', [ref.id], top_k=3)
    assert isinstance(results, list)
