from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.database import init_db
from app.routers import references, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    yield
    await app.state.http_client.aclose()


app = FastAPI(title="Message Writer API", lifespan=lifespan)
app.include_router(search.router)
app.include_router(references.router)


@app.get("/health")
def health():
    return {"status": "ok"}
