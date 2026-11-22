import json
import math
import os

from openai import OpenAI

from opportunity_radar.store import embedded_datasets, list_datasets, save_embeddings


def _client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY in .env to use semantic investigation.")
    return OpenAI(api_key=key)


def _document(row: dict) -> str:
    terms = json.loads(row["keywords"] or "[]")
    return "\n".join((f"Title: {row['title']}", f"Description: {row['description']}",
                      f"Category: {row['category']}", f"Keywords: {', '.join(terms)}"))[:6000]


def _cosine(left: list[float], right: list[float]) -> float:
    denominator = math.sqrt(sum(value * value for value in left) * sum(value * value for value in right))
    return sum(a * b for a, b in zip(left, right)) / denominator if denominator else 0.0


def investigate_query(query: str, top_k: int = 5) -> dict:
    client = _client()
    rows = list_datasets()
    if not rows:
        raise RuntimeError("Sync catalogue datasets before starting an investigation.")

    indexed = {row["id"]: row for row in embedded_datasets()}
    missing = [row for row in rows if row["id"] not in indexed]
    if missing:
        vectors = {}
        row_by_id = {row["id"]: row for row in missing}
        for start in range(0, len(missing), 48):
            batch = missing[start:start + 48]
            result = client.embeddings.create(
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                input=[_document(row) for row in batch],
            )
            vectors.update({row["id"]: data.embedding for row, data in zip(batch, result.data)})
        save_embeddings(vectors)
        indexed.update({dataset_id: {**row_by_id[dataset_id], "embedding": json.dumps(vector)}
                        for dataset_id, vector in vectors.items()})

    query_result = client.embeddings.create(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"), input=[query])
    query_vector = query_result.data[0].embedding
    ranked = sorted(((row, _cosine(query_vector, json.loads(row["embedding"]))) for row in indexed.values()),
                    key=lambda pair: pair[1], reverse=True)[:top_k]
    evidence = []
    sources = []
    for index, (row, score) in enumerate(ranked, start=1):
        sources.append({"id": row["id"], "title": row["title"], "url": row["url"], "similarity": round(score, 4)})
        evidence.append(f"[{index}] {row['title']}\nURL: {row['url']}\nMetadata: {row['description'][:2500]}")

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        instructions=("You are a cautious market investigator. Answer only from the retrieved catalogue metadata. "
                      "Separate verified statements from opportunity hypotheses. Cite each factual claim using source labels [1], [2]. "
                      "If the sources do not support an opportunity, say that clearly. State evidence gaps and a cheap validation step. "
                      "Do not infer that a dataset proves market demand."),
        input=f"Investigation question: {query}\n\nRetrieved public dataset records:\n" + "\n\n".join(evidence),
    )
    return {"query": query, "report": response.output_text, "sources": sources}
