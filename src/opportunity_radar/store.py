import json
import os
import sqlite3
from pathlib import Path


DB_PATH = Path(os.getenv("RADAR_DB", "data/opportunity-radar.sqlite3"))


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
        organization TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT '',
        modified TEXT NOT NULL DEFAULT '', url TEXT NOT NULL DEFAULT '',
        keywords TEXT NOT NULL DEFAULT '[]', saved INTEGER NOT NULL DEFAULT 0,
        fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS analyses (
        dataset_id TEXT PRIMARY KEY REFERENCES datasets(id) ON DELETE CASCADE,
        content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    connection.commit()
    return connection


def save_datasets(datasets: list[dict], path: Path = DB_PATH) -> int:
    with connect(path) as db:
        for item in datasets:
            db.execute("""INSERT INTO datasets
                (id,title,description,organization,category,modified,url,keywords)
                VALUES (:id,:title,:description,:organization,:category,:modified,:url,:keywords)
                ON CONFLICT(id) DO UPDATE SET title=excluded.title, description=excluded.description,
                organization=excluded.organization, category=excluded.category, modified=excluded.modified,
                url=excluded.url, keywords=excluded.keywords, fetched_at=CURRENT_TIMESTAMP""",
                {**item, "keywords": json.dumps(item["keywords"], ensure_ascii=False)})
    return len(datasets)


def list_datasets(query: str = "", saved_only: bool = False, path: Path = DB_PATH) -> list[dict]:
    sql = "SELECT d.*, a.content AS analysis, a.created_at AS analyzed_at FROM datasets d LEFT JOIN analyses a ON a.dataset_id=d.id"
    terms, values = [], []
    if query.strip():
        terms.append("(d.title LIKE ? OR d.description LIKE ? OR d.organization LIKE ? OR d.category LIKE ?)")
        values.extend([f"%{query.strip()}%"] * 4)
    if saved_only:
        terms.append("d.saved=1")
    if terms:
        sql += " WHERE " + " AND ".join(terms)
    sql += " ORDER BY d.modified DESC, d.title COLLATE NOCASE LIMIT 300"
    with connect(path) as db:
        return [dict(row) for row in db.execute(sql, values)]


def set_saved(dataset_id: str, saved: bool, path: Path = DB_PATH) -> bool:
    with connect(path) as db:
        cursor = db.execute("UPDATE datasets SET saved=? WHERE id=?", (int(saved), dataset_id))
        return cursor.rowcount > 0


def save_analysis(dataset_id: str, content: str, path: Path = DB_PATH) -> None:
    with connect(path) as db:
        db.execute("INSERT INTO analyses(dataset_id,content) VALUES (?,?) ON CONFLICT(dataset_id) DO UPDATE SET content=excluded.content, created_at=CURRENT_TIMESTAMP", (dataset_id, content))


def stats(path: Path = DB_PATH) -> dict:
    with connect(path) as db:
        row = db.execute("SELECT COUNT(*) total, SUM(saved) saved, MAX(fetched_at) updated FROM datasets").fetchone()
        return {"total": row["total"], "saved": row["saved"] or 0, "updated": row["updated"]}
