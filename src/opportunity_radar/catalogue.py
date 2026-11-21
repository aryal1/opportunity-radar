from datetime import datetime

import requests


API_URL = "https://api.dane.gov.pl/1.4/datasets"


class CatalogueError(RuntimeError):
    pass


def normalize_dataset(record: object) -> dict | None:
    if not isinstance(record, dict):
        return None
    attributes = record.get("attributes")
    if not isinstance(attributes, dict):
        return None
    title = attributes.get("title")
    identifier = record.get("id")
    if not isinstance(title, str) or not title.strip() or identifier is None:
        return None
    relationships = record.get("relationships") or {}
    organization = ""
    if isinstance(relationships, dict):
        org_data = (relationships.get("institution") or {}).get("data")
        if isinstance(org_data, dict):
            organization = str(org_data.get("id") or "")
    modified = attributes.get("modified") or attributes.get("created") or ""
    if modified:
        try:
            datetime.fromisoformat(str(modified).replace("Z", "+00:00"))
        except ValueError:
            modified = ""
    link = attributes.get("url") or f"https://dane.gov.pl/pl/dataset/{identifier}"
    keywords = attributes.get("keywords") or []
    if not isinstance(keywords, list):
        keywords = []
    return {
        "id": str(identifier), "title": title.strip(),
        "description": str(attributes.get("notes") or "").strip(),
        "organization": organization,
        "category": str(attributes.get("category") or "").strip(),
        "modified": str(modified), "url": str(link),
        "keywords": [str(word) for word in keywords if isinstance(word, (str, int, float))],
    }


def search_catalogue(query: str = "", pages: int = 4) -> list[dict]:
    found = []
    try:
        for page in range(1, max(1, min(pages, 10)) + 1):
            response = requests.get(API_URL, params={"page": page, "per_page": 100, "sort": "-modified", **({"q": query} if query else {})}, timeout=(5, 25))
            response.raise_for_status()
            payload = response.json()
            records = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(records, list):
                raise CatalogueError("The open data catalogue returned an unexpected response.")
            found.extend(item for record in records if (item := normalize_dataset(record)))
            if len(records) < 100:
                break
    except (requests.RequestException, ValueError, CatalogueError) as error:
        raise CatalogueError(f"Could not load the Polish open data catalogue: {error}") from error
    return found
