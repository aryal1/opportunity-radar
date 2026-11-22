from types import SimpleNamespace

from opportunity_radar import retrieval, store
from opportunity_radar.retrieval import _cosine
from opportunity_radar.store import save_datasets


def test_cosine_similarity_handles_aligned_and_zero_vectors():
    assert _cosine([1, 0], [1, 0]) == 1
    assert _cosine([1, 0], [0, 1]) == 0
    assert _cosine([0, 0], [1, 1]) == 0


def test_investigation_retrieves_and_cites_records_without_external_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'rag.sqlite3'}")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    store._engine.cache_clear()
    save_datasets([
        {"id": "energy", "title": "Energy production", "description": "Solar electricity", "organization": "A", "category": "Energy", "modified": "2025-01-01", "url": "https://data.test/energy", "keywords": ["solar"]},
        {"id": "health", "title": "Health services", "description": "Hospital capacity", "organization": "B", "category": "Health", "modified": "2025-01-01", "url": "https://data.test/health", "keywords": ["hospital"]},
    ])

    class FakeClient:
        def __init__(self):
            self.embeddings = SimpleNamespace(create=self.create_embeddings)
            self.responses = SimpleNamespace(create=lambda **kwargs: SimpleNamespace(output_text="Evidence summary [1]."))

        @staticmethod
        def create_embeddings(model, input):
            vectors = [[1.0, 0.0] if "Energy" in text or "energy" in text.lower() else [0.0, 1.0] for text in input]
            return SimpleNamespace(data=[SimpleNamespace(embedding=vector) for vector in vectors])

    monkeypatch.setattr(retrieval, "OpenAI", lambda api_key: FakeClient())
    result = retrieval.investigate_query("energy", top_k=1)

    assert result["report"] == "Evidence summary [1]."
    assert result["sources"][0]["id"] == "energy"
    assert result["sources"][0]["url"] == "https://data.test/energy"
    store._engine.cache_clear()
