# Opportunity Radar

An evidence-led market investigation dashboard built around Poland's public open data catalogue. It syncs and validates dataset metadata, persists it through SQLAlchemy, supports keyword search and saved signals, and provides semantic retrieval with a cited AI brief.

## Quick start

Requires Python 3.12+. SQLite is the default local database, so no database server is required:

```bash
uv sync --all-groups
uv run python main.py
```

Open `http://127.0.0.1:8765`. The REST API schema and interactive docs are at `/openapi.json` and `/docs`. SQLite data is stored in `data/opportunity-radar.sqlite3`.

## PostgreSQL with Docker Compose

Copy `.env.example` to `.env`, configure the optional AI key, then start the app and PostgreSQL:

```bash
docker compose up --build
```

Compose uses PostgreSQL 16 and persists database files in a named volume. Set `POSTGRES_PASSWORD` before exposing this setup beyond a trusted local environment. Docker must be installed to use this profile.

## Data and investigation flow

1. **Refresh signals** reads up to 400 recently updated records from `https://api.dane.gov.pl/1.4/datasets` and upserts valid records.
2. Search and saved signals work with locally persisted catalogue metadata.
3. **Investigate** embeds metadata from stored records, retrieves the most similar records, and asks the configured model to generate a brief with numbered source citations. Embeddings are cached in the database.
4. **Analyze** generates a focused review of one record and stores it alongside that record.

AI features require `OPENAI_API_KEY` in `.env`. The default chat model is `gpt-4.1-mini`; the default embedding model is `text-embedding-3-small`. Semantic investigation makes embedding and response API calls, which may incur provider charges. Dataset metadata is sent to the configured AI provider when these features are used. The service does not claim a measured opportunity-prediction accuracy.

The app ranks retrieved records by cosine similarity. This transparent retrieval baseline is not a trained market prediction model. TensorFlow is intentionally not wired into production scoring yet: there is no labeled history of successful/unsuccessful opportunities from which to train or validate a meaningful model. Flask is also omitted because FastAPI already serves the API and generated OpenAPI documentation; running both frameworks would add a second server without improving the product.

This version analyzes catalogue metadata only; it does not download or inspect the underlying files. A dataset's existence is not evidence of market demand. Use the brief as a research lead and verify its cited source and commercial assumptions.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///data/opportunity-radar.sqlite3` |
| `OPENAI_API_KEY` | Enables AI analysis and semantic investigation | unset |
| `OPENAI_MODEL` | AI brief model | `gpt-4.1-mini` |
| `OPENAI_EMBEDDING_MODEL` | Metadata/query embedding model | `text-embedding-3-small` |
| `HOST` / `PORT` | Local web server bind and port | `127.0.0.1` / `8765` |

## API highlights

- `GET /api/datasets?q=energy&saved=false`
- `GET /api/stats`
- `POST /api/sync` with `{"query":"energy"}`
- `POST /api/investigate` with `{"query":"What signals relate to energy efficiency?","top_k":5}`
- `POST /api/analyze` with `{"id":"dataset-id"}`
- `POST /api/save` with `{"id":"dataset-id","saved":true}`

FastAPI validates request bodies and publishes the interactive schema at `/docs`.

## Tests and CI

```bash
uv run python -m pytest -q
uv run python -m ruff check src tests main.py
```

GitHub Actions runs tests and Ruff on pushes and pull requests. The suite uses a temporary SQLite database and does not call external APIs.
