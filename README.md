# Message Writer

Generate grounded HCP messages from PubMed articles and PDFs. Every claim is backed by retrieved evidence — unsupported claims get dropped.

## Architecture

```
apps/api/    FastAPI backend — SQLite + FTS5, OpenAI structured output
apps/web/    Next.js 16 frontend — App Router, Tailwind
scripts/     Eval harness for grounding quality
```

**Pipeline:** Search PubMed → import references → chunk + index (FTS5) → retrieve relevant chunks → generate claims → verify grounding → persist message

## Setup

```
cp .env.example .env
```

Add your OpenAI API key to `.env`.

### Docker 

```
docker compose up --build
```

API at `localhost:8000`, frontend at `localhost:3000`.

### Local

API:

```
cd apps/api
pip install -e .
uvicorn app.main:app --reload
```

Frontend:

```
cd apps/web
npm install
npm run dev
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | GET | PubMed search |
| `/references/from-pubmed` | POST | Import article by PMID |
| `/references/upload` | POST | Upload PDF |
| `/references/` | GET | List references |
| `/references/{id}` | DELETE | Remove reference |
| `/messages/generate` | POST | Generate grounded message |
| `/messages/generate/stream` | POST | SSE streaming generation |
| `/messages/` | GET | List messages |
| `/messages/{id}` | GET | Message detail with claims |
| `/messages/{id}/refine` | POST | Re-generate with updated evidence |

## Eval

```
python scripts/eval_grounding.py --message-id <id> --api-url http://localhost:8000
```

Outputs JSON grounding report. Exit codes: 0 = pass, 1 = fail, 2 = error.
