from sqlalchemy import text
from sqlalchemy.orm import Session


def test_chunk_insert_appears_in_fts(engine):
    with Session(engine) as session:
        from app.models.reference import Reference
        from app.models.chunk import Chunk

        ref = Reference(title="Test Paper", source="pubmed")
        session.add(ref)
        session.flush()

        chunk = Chunk(reference_id=ref.id, content="hello world test content", chunk_index=0)
        session.add(chunk)
        session.commit()

        result = session.execute(
            text("SELECT * FROM chunks_fts WHERE chunks_fts MATCH :q"),
            {"q": "hello"},
        ).fetchall()
        assert len(result) == 1


def test_chunk_delete_removes_from_fts(engine):
    with Session(engine) as session:
        from app.models.reference import Reference
        from app.models.chunk import Chunk

        ref = Reference(title="Test Paper", source="pubmed")
        session.add(ref)
        session.flush()

        chunk = Chunk(reference_id=ref.id, content="unique search term xyz", chunk_index=0)
        session.add(chunk)
        session.commit()

        session.delete(chunk)
        session.commit()

        result = session.execute(
            text("SELECT * FROM chunks_fts WHERE chunks_fts MATCH :q"),
            {"q": "unique"},
        ).fetchall()
        assert len(result) == 0
