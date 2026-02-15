import logging

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.models.chunk import Chunk

logger = logging.getLogger(__name__)


def _chunk_to_dict(c) -> dict:
    return {
        "id": c.id,
        "reference_id": c.reference_id,
        "content": c.content,
        "chunk_index": c.chunk_index,
    }


def retrieve(
    db: Session, query: str, reference_ids: list[int], top_k: int = 5
) -> list[dict]:
    if not reference_ids:
        return []

    safe_query = query.replace('"', "")
    if not safe_query.strip():
        return _fallback(db, reference_ids, top_k)

    placeholders = ",".join(f":ref_{i}" for i in range(len(reference_ids)))
    params = {f"ref_{i}": rid for i, rid in enumerate(reference_ids)}
    params["query"] = f'"{safe_query}"'
    params["top_k"] = top_k

    stmt = sql_text(f"""
        SELECT c.id, c.reference_id, c.content, c.chunk_index
        FROM chunks_fts
        JOIN chunks c ON c.id = chunks_fts.rowid
        WHERE chunks_fts MATCH :query
          AND c.reference_id IN ({placeholders})
        ORDER BY chunks_fts.rank
        LIMIT :top_k
    """)

    try:
        results = db.execute(stmt, params).fetchall()
    except Exception:
        logger.warning("FTS query failed, using fallback", exc_info=True)
        return _fallback(db, reference_ids, top_k)

    if not results:
        return _fallback(db, reference_ids, top_k)

    return [_chunk_to_dict(r) for r in results]


def _fallback(
    db: Session, reference_ids: list[int], top_k: int
) -> list[dict]:
    chunks = (
        db.query(Chunk)
        .filter(Chunk.reference_id.in_(reference_ids))
        .order_by(Chunk.chunk_index)
        .limit(top_k)
        .all()
    )
    return [_chunk_to_dict(c) for c in chunks]
