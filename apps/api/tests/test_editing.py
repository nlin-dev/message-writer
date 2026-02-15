import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_db, init_db
from app.main import app
from app.models.chunk import Chunk
from app.models.reference import Reference
from app.models.working_set_item import WorkingSetItem
from app.routers.messages import get_llm_provider
from app.services.llm_provider import (
    LLMCitation,
    LLMClaim,
    LLMGenerationResult,
    MockProvider,
)


@pytest.fixture
def mock_llm_client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Seed test data
    session = TestSession()
    ref = Reference(id=1, title="Test Reference", source="test")
    session.add(ref)
    session.flush()
    chunk = Chunk(id=1, reference_id=1, content="Test evidence text about diabetes treatment.", chunk_index=0)
    session.add(chunk)
    session.add(WorkingSetItem(reference_id=1))
    session.commit()
    session.close()

    # Mock LLM returns a claim with enough word overlap to pass grounding
    mock_provider = MockProvider(
        fixed_result=LLMGenerationResult(
            claims=[
                LLMClaim(
                    text="Test evidence text about diabetes treatment.",
                    citations=[LLMCitation(reference_id=1, chunk_id=1)],
                )
            ]
        )
    )

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_provider] = lambda: mock_provider

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    test_engine.dispose()


def test_generate_then_refine(mock_llm_client):
    client = mock_llm_client

    # Generate
    resp = client.post("/messages/generate", json={"prompt": "Write about diabetes", "reference_ids": [1]})
    assert resp.status_code == 200
    message_id = resp.json()["message_id"]

    # Refine
    resp = client.post(
        f"/messages/{message_id}/refine",
        json={"instruction": "Make it shorter", "reference_ids": [1]},
    )
    assert resp.status_code == 200
    assert resp.json()["version_number"] == 2

    # Verify versions
    resp = client.get(f"/messages/{message_id}")
    assert resp.status_code == 200
    versions = resp.json()["versions"]
    assert len(versions) == 2
    assert versions[0]["source"] == "generated"
    assert versions[0]["version_number"] == 1
    assert versions[1]["source"] == "refined"
    assert versions[1]["version_number"] == 2


def test_direct_edit(mock_llm_client):
    client = mock_llm_client

    # Generate
    resp = client.post("/messages/generate", json={"prompt": "Write about diabetes", "reference_ids": [1]})
    assert resp.status_code == 200
    message_id = resp.json()["message_id"]

    # Direct edit
    resp = client.put(f"/messages/{message_id}", json={"message_text": "Manually edited text"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["version_number"] == 2
    assert data["message_text"] == "Manually edited text"
    assert isinstance(data["warnings"], list)
    assert len(data["warnings"]) > 0

    # Verify versions
    resp = client.get(f"/messages/{message_id}")
    assert resp.status_code == 200
    versions = resp.json()["versions"]
    assert len(versions) == 2
    assert versions[0]["source"] == "generated"
    assert versions[1]["source"] == "edited"


def test_finalized_message_rejects_refine(mock_llm_client):
    client = mock_llm_client

    # Generate
    resp = client.post("/messages/generate", json={"prompt": "Write about diabetes", "reference_ids": [1]})
    assert resp.status_code == 200
    message_id = resp.json()["message_id"]

    # Finalize
    resp = client.patch(f"/messages/{message_id}", json={"status": "finalized"})
    assert resp.status_code == 200

    # Attempt refine -> 409
    resp = client.post(
        f"/messages/{message_id}/refine",
        json={"instruction": "Make it shorter", "reference_ids": [1]},
    )
    assert resp.status_code == 409
