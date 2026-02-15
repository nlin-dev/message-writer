import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.database import get_db, init_db
from app.main import app


@pytest.fixture
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    init_db(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def client():
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    init_db(test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    test_engine.dispose()
