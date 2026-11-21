from opportunity_radar.catalogue import normalize_dataset


def test_normalize_dataset_preserves_evidence_and_validates_fields():
    item = normalize_dataset({
        "id": "42",
        "attributes": {
            "title": "  Air quality  ", "notes": "Hourly measurements", "category": "Environment",
            "modified": "2025-02-01T12:30:00Z", "keywords": ["air", "health", None],
        },
    })
    assert item == {
        "id": "42", "title": "Air quality", "description": "Hourly measurements",
        "organization": "", "category": "Environment", "modified": "2025-02-01T12:30:00Z",
        "url": "https://dane.gov.pl/pl/dataset/42", "keywords": ["air", "health"],
    }


def test_normalize_dataset_rejects_missing_title_or_id():
    assert normalize_dataset({"id": "1", "attributes": {"title": " "}}) is None
    assert normalize_dataset({"attributes": {"title": "Dataset"}}) is None
    assert normalize_dataset({"id": "1", "attributes": "invalid"}) is None


def test_normalize_dataset_discards_invalid_dates():
    item = normalize_dataset({"id": 1, "attributes": {"title": "Dataset", "modified": "soon"}})
    assert item["modified"] == ""
