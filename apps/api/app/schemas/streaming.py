from typing import Literal

from pydantic import BaseModel


class StatusEvent(BaseModel):
    stage: Literal["retrieving", "generating", "verifying", "persisting", "done"]


class DeltaEvent(BaseModel):
    text: str


class ErrorEvent(BaseModel):
    message: str


def sse_event(event_type: str, data: BaseModel) -> dict:
    return {
        "event": event_type,
        "data": data.model_dump_json(),
    }
