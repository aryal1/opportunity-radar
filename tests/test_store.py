from opportunity_radar.store import list_datasets, save_analysis, save_datasets, set_saved, stats


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
