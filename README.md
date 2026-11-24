# Opportunity Radar

**Can public data help someone find a business opportunity worth investigating?** Opportunity Radar is my attempt to turn that question into a testable research workflow. The current application collects descriptions of Polish public datasets, lets me search and save them, and can draft a source-linked investigation brief. It is a working prototype, not a validated opportunity detector.


## The problem I want to solve

Suppose a small company asks: *Where in Poland might energy-efficiency services be needed?* Public datasets might contain useful clues. Finding the right dataset is already work; understanding its units, geography, time period, and limitations is harder. The [OECD identifies data quality as a barrier to reliable reuse](https://www.oecd.org/en/publications/digital-government-outlook_0496b2bc-en/full-report/strengthening-digital-public-infrastructure-and-data-governance_2c7323c7.html). Even a real change in an economic indicator does not establish that customers have an unmet need or would pay for a solution.

My hypothesis is that a repeatable investigation workflow can help an analyst reach **verifiable leads** faster than searching a portal or asking a general AI assistant alone. A lead would need a traceable observation, a plausible mechanism, alternative explanations, and a cheap next test. If a controlled comparison cannot show better evidence quality or save meaningful research time, the hypothesis fails. I have not run that comparison yet.

## What I tried, and what changed

| Step | Observation | Decision |
| --- | --- | --- |
| Retrieve public material from PARP pages | An early request received an Incapsula anti-bot incident page rather than usable content. The remaining `collector.py` detects that response. | Stop treating arbitrary website scraping as a dependable foundation. PARP data is not integrated today. |
| Ask an early model to assess a weak opportunity claim | In one exploratory trial, it refused to endorse an unsupported hypothesis. | Keep explicit permission to say “insufficient evidence.” One prompt is encouraging behavior, not a measured hallucination rate; the trial output is not preserved as a benchmark. |
| Use the [official Polish open-data API](https://api.dane.gov.pl/1.4/doc?urls.primaryName=DANE.GOV.PL+RDF+API) | Structured dataset records could be fetched and stored reliably, so I could build a real ingestion and review loop. | Start with an official API and retain source links. |
| Inspect what “recent” means | On 24 November 2026, one of the newest returned records was [a developer's apartment asking-price dataset](https://api.dane.gov.pl/1.4/datasets/20737). Its modified timestamp says when that catalogue entry changed; it does not show a housing trend or unmet demand. | Treat freshness and semantic similarity as ways to find material to inspect, never as opportunity scores. |

This is the critical boundary of the project's current scope. The [catalogue API](https://api.dane.gov.pl/1.4/doc?urls.primaryName=DANE.GOV.PL+RDF+API) separates **datasets** from their **resources**; some resources expose actual rows. This prototype currently reads dataset *metadata* (title, description, category, keywords, dates and URL), not those underlying observations. It can tell an analyst where to look. It cannot yet demonstrate that a market is changing.

## What the prototype actually does

1. **Collect:** `POST /api/sync` requests up to four pages of recently modified records from `api.dane.gov.pl` (at most 400 per refresh), validates basic fields, and upserts them into a local database.
2. **Review:** The dashboard supports local text search, a saved shortlist, dataset descriptions, and links supplied by the catalogue. Each listing is capped at 300 matching records; an investigation considers at most 300 stored records.
3. **Investigate, optionally:** With an OpenAI API key, the app embeds stored metadata, ranks it against a question using cosine similarity, and sends the top records to a model with instructions to separate facts, hypotheses, and gaps. It returns a brief and numbered source links. A separate action generates and saves a review of one dataset.

```text
Polish open-data API → normalize metadata → SQLite / PostgreSQL
                                         ↓
Dashboard + FastAPI → local search / saved records
                   → embeddings → similarity ranking → AI brief + source URLs
```

The stack is **Python 3.12+, FastAPI, SQLAlchemy, SQLite locally, optional PostgreSQL via Docker Compose, plain HTML/CSS/JavaScript, and optional OpenAI embeddings and Responses API**. The API schema and interactive documentation are at `/openapi.json` and `/docs`. Automated tests use mocked provider calls and isolated databases.

There is a deliberate boundary around the AI output: source links show which records were supplied, but the software does not verify every sentence in the generated brief. A citation to a dataset description is not a citation to a measured result. Review the original source before using any claim.

## Does this deserve to become a product?

That remains open. The [public-data portal](https://dane.gov.pl/en) already offers discovery; [ChatGPT Deep Research](https://help.openai.com/en/articles/10500283-search-in-chatgpt) can produce cited research; and [AlphaSense](https://www.alpha-sense.com/) offers a mature market-intelligence workflow with substantial content. A nicer interface or an AI-generated idea list would be a weak reason to build another tool.

The potential wedge is a **narrow investigation engine for a specific decision**: preserve the exact observations behind a claim, show missing and conflicting evidence, compare places or periods, and record what happened after a human tested the lead. The present app is the ingestion and retrieval foundation for that experiment; it does not provide that full workflow. [Statistics Poland's Local Data Bank API](https://api.stat.gov.pl/Home/BdlApi?lang=en) is one plausible source of regional economic observations for a next iteration, but it is not integrated.

There is no evidence yet of customer demand, willingness to pay, superior results against ChatGPT, or reliable opportunity prediction. I would first interview people who actually make location, sector, or investment decisions: what question took them days to answer, which sources did they use, what decision depended on it, and who controls the research budget? A product is justified only if the answer reveals a recurring, costly task that this workflow measurably improves.

## Next experiments and decision criteria

1. **Choose one use case and interview users.** Recruit 5–10 relevant analysts or founders, observe a recent real investigation, and test whether they would commit time or budget to a narrower workflow. Record refusals and existing alternatives as carefully as positive feedback.
2. **Create a reviewed question set.** Include questions with useful public observations, questions with misleading catalogue matches, and questions where the correct answer is “insufficient evidence.” Save source versions, expected relevant records, and reviewer notes before changing retrieval.
3. **Compare the alternatives on the same tasks.** Have reviewers, blind to the method, assess portal search, ChatGPT Deep Research, the current app, and a later resource-level version. Measure time to a *verified* lead, relevant-source recall, factual claims supported by the cited source, and unsupported opportunity claims on negative cases. Include provider cost and analyst review time.
4. **Set a decision gate before seeing results.** A candidate gate is at least 20% less median analyst time than the strongest baseline, at least 95% of factual claims supported by their cited material, and no increase in unsupported opportunity claims. These are proposed thresholds, not achieved results. If reviewers cannot agree on the scoring rubric, fix the rubric before claiming progress.
5. **Only then deepen the system.** Fetch selected resources and regional time series, preserve units, dates, geography and provenance, invalidate embeddings when metadata changes, and test whether the added complexity improves the benchmark. If it does not, keep the simpler workflow or stop.

## Limits you should know before trying it

- Sync fetches a recent slice of **one** catalogue, not all Polish economic data. A modified record may reflect a metadata edit rather than new observations.
- Retrieval reads descriptions, and the local listing is capped at 300 records. It has no labeled relevance benchmark. Cached embeddings are not automatically refreshed when a dataset's metadata changes.
- The model's instructions encourage caution; they do not enforce source support. AI requests send the research question and public metadata to the configured provider and may incur charges.
- Saved records and dataset analyses persist locally. There are no accounts, team controls, automatic refresh jobs, resource-level measurements, or evidence of commercial adoption.

## Run it yourself

Install [uv](https://docs.astral.sh/uv/) and Python 3.12 or newer, then from the repository root:

```bash
uv sync --all-groups
uv run python main.py
```

Open `http://127.0.0.1:8765`, click **Refresh signals**, then search or save records. No API key is required for these actions. The default database is `data/opportunity-radar.sqlite3`. The server also exposes `/docs`.

For the optional **Analyze** and **Investigate** actions, copy `.env.example` to `.env` and set `OPENAI_API_KEY`. The defaults are `gpt-4.1-mini` and `text-embedding-3-small`; both can be changed in `.env`. If you prefer PostgreSQL, `docker compose up --build` starts the app and database with a persistent volume. Set `POSTGRES_PASSWORD` before using that setup outside local development.

Run the checks with:

```bash
uv run python -m pytest -q
uv run python -m ruff check src tests main.py
```

The current tests cover normalization, local storage, API validation, and retrieval with mocked AI responses. They do not test live model quality or customer value.
