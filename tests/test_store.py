import sqlite3

from opportunity_radar.store import (
    list_datasets,
    save_analysis,
    save_datasets,
    set_saved,
    stats,
)


def test_persist_search_save_and_analysis(tmp_path):
    path = tmp_path / "radar.sqlite3"
    dataset = {"id": "x1", "title": "Local energy", "description": "Solar production", "organization": "City", "category": "Energy", "modified": "2025-01-01", "url": "https://dane.gov.pl", "keywords": ["solar"]}
    assert save_datasets([dataset], path) == 1
    assert save_datasets([dataset], path) == 1
    assert len(list_datasets("solar", path=path)) == 1
    assert list_datasets("unknown", path=path) == []
    assert set_saved("x1", True, path)
    save_analysis("x1", "Evidence review", path)
    row = list_datasets(saved_only=True, path=path)[0]
    assert row["saved"] == 1
    assert row["analysis"] == "Evidence review"
    assert stats(path)["total"] == 1
    assert stats(path)["saved"] == 1


def test_existing_sqlite_database_gets_embedding_column(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("""CREATE TABLE datasets (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
            organization TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT '',
            modified TEXT NOT NULL DEFAULT '', url TEXT NOT NULL DEFAULT '',
            keywords TEXT NOT NULL DEFAULT '[]', saved INTEGER NOT NULL DEFAULT 0,
            fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("INSERT INTO datasets (id,title) VALUES ('legacy','Earlier signal')")
        db.execute("CREATE TABLE analyses (dataset_id TEXT PRIMARY KEY, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")

    assert list_datasets(path=path)[0]["title"] == "Earlier signal"
    with sqlite3.connect(path) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(datasets)")}
    assert "embedding" in columns
