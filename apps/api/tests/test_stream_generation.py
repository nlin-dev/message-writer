import json

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


def parse_sse_events(text: str) -> list[dict]:
    events = []
    current = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith("event:"):
            current["event"] = line[len("event:"):].strip()
        elif line.startswith("data:"):
            current["data"] = line[len("data:"):].strip()
        elif line == "" and current:
            events.append(current)
            current = {}
    if current:
        events.append(current)
    return events


@pytest.fixture
def stream_client_no_evidence():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    mock_provider = MockProvider(
        fixed_result=LLMGenerationResult(claims=[])
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


@pytest.fixture
def stream_client_with_evidence():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    session = TestSession()
    ref = Reference(id=1, title="Test Reference", source="test")
    session.add(ref)
    session.flush()
    chunk = Chunk(
        id=1,
        reference_id=1,
        content="Test evidence text about diabetes treatment.",
        chunk_index=0,
    )
    session.add(chunk)
    session.add(WorkingSetItem(reference_id=1))
    session.commit()
    session.close()

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
        yield c, TestSession

    app.dependency_overrides.clear()
    test_engine.dispose()


def test_stream_no_evidence(stream_client_no_evidence):
    response = stream_client_no_evidence.post(
        "/messages/generate/stream",
        json={"prompt": "test", "reference_ids": []},
    )
    assert response.status_code == 200

    events = parse_sse_events(response.text)
    event_types = [e["event"] for e in events]

    assert event_types[0] == "status"
    assert json.loads(events[0]["data"])["stage"] == "retrieving"

    # Find final event
    final_events = [e for e in events if e["event"] == "final"]
    assert len(final_events) == 1
    final_data = json.loads(final_events[0]["data"])
    assert final_data["message_id"] is None
    assert "Insufficient evidence" in final_data["warnings"][0]

    # Last event should be status done
    assert event_types[-1] == "status"
    assert json.loads(events[-1]["data"])["stage"] == "done"


def test_stream_full_pipeline(stream_client_with_evidence):
    client, TestSession = stream_client_with_evidence
    response = client.post(
        "/messages/generate/stream",
        json={"prompt": "diabetes treatment", "reference_ids": [1]},
    )
    assert response.status_code == 200

    events = parse_sse_events(response.text)
    event_types = [e["event"] for e in events]

    # Check expected sequence
    assert "status" in event_types
    assert "delta" in event_types
    assert "final" in event_types

    # Check status progression
    status_stages = [
        json.loads(e["data"])["stage"]
        for e in events
        if e["event"] == "status"
    ]
    assert status_stages[0] == "retrieving"
    assert "generating" in status_stages
    assert "verifying" in status_stages
    assert "persisting" in status_stages
    assert status_stages[-1] == "done"

    # Check final event
    final_data = json.loads([e for e in events if e["event"] == "final"][0]["data"])
    assert final_data["message_id"] is not None
    assert len(final_data["claims"]) > 0
    assert final_data["message_text"] != ""

    # Verify message persisted and retrievable
    msg_id = final_data["message_id"]
    get_response = client.get(f"/messages/{msg_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == msg_id


