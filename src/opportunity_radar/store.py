import json
import os
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    create_engine,
    func,
    inspect,
    or_,
    select,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(180), primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")
    organization: Mapped[str] = mapped_column(String(500), default="")
    category: Mapped[str] = mapped_column(String(500), default="")
    modified: Mapped[str] = mapped_column(String(80), default="")
    url: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[str] = mapped_column(Text, default="[]")
    saved: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)


class Analysis(Base):
    __tablename__ = "analyses"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


@lru_cache(maxsize=8)
def _engine(path: Path | None = None):
    if path is not None:
        url = f"sqlite:///{path.resolve()}"
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        url = os.getenv("DATABASE_URL", "sqlite:///data/opportunity-radar.sqlite3")
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    options = {"check_same_thread": False} if url.startswith("sqlite:") else {}
    engine = create_engine(url, connect_args=options, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("datasets")}
    if "embedding" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE datasets ADD COLUMN embedding TEXT"))
    return engine


def _json_row(dataset: Dataset, analysis: Analysis | None = None) -> dict:
    return {
        "id": dataset.id, "title": dataset.title, "description": dataset.description,
        "organization": dataset.organization, "category": dataset.category,
        "modified": dataset.modified, "url": dataset.url, "keywords": dataset.keywords,
        "saved": dataset.saved, "fetched_at": dataset.fetched_at.isoformat() if dataset.fetched_at else None,
        "analysis": analysis.content if analysis else None,
        "analyzed_at": analysis.created_at.isoformat() if analysis else None,
    }


def save_datasets(datasets: list[dict], path: Path | None = None) -> int:
    engine = _engine(path)
    factory = sessionmaker(engine)
    with factory.begin() as session:
        for item in datasets:
            row = session.get(Dataset, str(item["id"]))
            if row is None:
                row = Dataset(id=str(item["id"]), title=item["title"])
                session.add(row)
            for field in ("title", "description", "organization", "category", "modified", "url"):
                setattr(row, field, str(item.get(field) or ""))
            row.keywords = json.dumps(item.get("keywords", []), ensure_ascii=False)
            row.fetched_at = datetime.now(UTC)
    return len(datasets)


def list_datasets(query: str = "", saved_only: bool = False, path: Path | None = None) -> list[dict]:
    engine = _engine(path)
    factory = sessionmaker(engine)
    statement = select(Dataset, Analysis).outerjoin(Analysis, Analysis.dataset_id == Dataset.id)
    if query.strip():
        needle = f"%{query.strip()}%"
        statement = statement.where(or_(Dataset.title.ilike(needle), Dataset.description.ilike(needle), Dataset.organization.ilike(needle), Dataset.category.ilike(needle)))
    if saved_only:
        statement = statement.where(Dataset.saved.is_(True))
    statement = statement.order_by(Dataset.modified.desc(), Dataset.title.asc()).limit(300)
    with factory() as session:
        result = [_json_row(dataset, analysis) for dataset, analysis in session.execute(statement)]
    return result


def set_saved(dataset_id: str, saved: bool, path: Path | None = None) -> bool:
    engine = _engine(path)
    factory = sessionmaker(engine)
    with factory.begin() as session:
        row = session.get(Dataset, dataset_id)
        if row is None:
            return False
        row.saved = saved
    return True


def save_analysis(dataset_id: str, content: str, path: Path | None = None) -> None:
    engine = _engine(path)
    factory = sessionmaker(engine)
    with factory.begin() as session:
        row = session.get(Analysis, dataset_id)
        if row is None:
            row = Analysis(dataset_id=dataset_id, content=content)
            session.add(row)
        else:
            row.content = content
            row.created_at = datetime.now(UTC)


def save_embeddings(embeddings: dict[str, list[float]], path: Path | None = None) -> None:
    engine = _engine(path)
    factory = sessionmaker(engine)
    with factory.begin() as session:
        for dataset_id, vector in embeddings.items():
            row = session.get(Dataset, dataset_id)
            if row is not None:
                row.embedding = json.dumps(vector)


def embedded_datasets(path: Path | None = None) -> list[dict]:
    engine = _engine(path)
    factory = sessionmaker(engine)
    with factory() as session:
        result = [{"id": row.id, "title": row.title, "description": row.description, "url": row.url, "embedding": row.embedding}
                  for row in session.scalars(select(Dataset).where(Dataset.embedding.is_not(None)))]
    return result


def stats(path: Path | None = None) -> dict:
    engine = _engine(path)
    factory = sessionmaker(engine)
    with factory() as session:
        total = session.scalar(select(func.count()).select_from(Dataset)) or 0
        saved = session.scalar(select(func.count()).select_from(Dataset).where(Dataset.saved.is_(True))) or 0
        updated = session.scalar(select(func.max(Dataset.fetched_at)))
    return {"total": total, "saved": saved, "updated": updated.isoformat(sep=" ") if updated else None}
