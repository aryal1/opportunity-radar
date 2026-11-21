# Opportunity Radar

A local research dashboard for finding and evaluating signals in Poland's public open data catalogue. It downloads real dataset metadata from `api.dane.gov.pl`, validates and stores it in SQLite, and lets you search, save, and optionally analyze entries with an OpenAI model.

## Run locally

Requires Python 3.12 or newer. From this directory:

```bash
uv sync
uv run python main.py
```

The dashboard opens at `http://127.0.0.1:8765`. Press `Ctrl+C` in the terminal to stop it. The SQLite database is created at `data/opportunity-radar.sqlite3` by default.

If you do not have `uv`, create a virtual environment and install the project with `pip install -e '.[dev]'`, then run `python main.py`.

## Find and investigate signals

Select **Refresh signals** to retrieve up to 400 recently modified catalogue records. Search filters the records already stored locally. Use the bookmark control to keep a shortlist; saved items and previous analyses persist between runs. Each entry links back to the source catalogue.

**Analyze** is optional. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` to enable it. The default model is `gpt-4.1-mini`; override it with `OPENAI_MODEL`. Analysis sends the dataset's public title, publisher identifier, category, description, and keywords to OpenAI. No API key is needed for browsing and saving records.

## Data and limits

The catalogue integration reads the JSON API at `https://api.dane.gov.pl/1.4/datasets`. Ingestion skips records without a usable identifier or title and tolerates missing optional fields. A failed sync leaves previously stored records intact. Opportunity assessments are hypotheses based on dataset metadata; verify market demand and source data before acting. The first version does not download or analyze the underlying dataset files.

The app binds to `127.0.0.1` and uses a local SQLite file. Keep `.env` private; it is excluded from Git.

## Tests

```bash
uv run pytest
```
