from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _ensure_db_dir(url: str) -> None:
    if url.startswith("sqlite:///"):
        db_path = Path(url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_db_dir(settings.database_url)
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _setup_fts(connection):
    connection.execute(text(
        "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(content, content=chunks, content_rowid=id)"
    ))
    connection.execute(text("""
        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
        END;
    """))
    connection.execute(text("""
        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES ('delete', old.id, old.content);
        END;
    """))
    connection.execute(text("""
        CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES ('delete', old.id, old.content);
            INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
        END;
    """))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(eng=None):
    target_engine = eng or engine
    import app.models  # noqa: F401 - ensure models are registered
    Base.metadata.create_all(bind=target_engine)
    with target_engine.connect() as conn:
        _setup_fts(conn)
        conn.commit()
