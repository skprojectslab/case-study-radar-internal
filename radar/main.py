import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml
from langdetect import detect, LangDetectException

from .http import get
from .utils import normalize_url, content_hash
from .adapters import standard, discovery

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def load_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def detect_language(title, description, hint, fallback):
    if hint:
        return hint
    text = f"{title}. {description}".strip()
    if text:
        try:
            return detect(text)
        except LangDetectException:
            pass
    return fallback

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default="config/sources.yaml")
    args = parser.parse_args()

    with open(args.sources, "r", encoding="utf-8") as f:
        sources = yaml.safe_load(f)

    history = load_json(DATA / "history.json", {})
    current = {}
    changes = []
    run_time = utc_now()

    for source_id, cfg in sources.items():
        adapter = discovery if cfg.get("adapter") == "discovery" else standard

        for listing_url in cfg.get("listing_urls", []):
            try:
                listing_html = get(listing_url)
                seeds = adapter.extract_listing(listing_html, listing_url)
            except Exception as exc:
                changes.append({
                    "type": "ERROR",
                    "market": cfg["market"],
                    "url": listing_url,
                    "error": str(exc)
                })
                continue

            for seed in seeds:
                url = normalize_url(seed["url"])
                if not url.startswith("http"):
                    continue

                # Stay on the configured domain.
                if cfg["domain"] not in url:
                    continue

                try:
                    detail_html = get(url)
                    detail = adapter.extract_detail(detail_html, url, seed)
                except Exception:
                    detail = {
                        "title": seed["title"],
                        "description": seed.get("description", ""),
                        "canonical_url": url,
                        "language_hint": ""
                    }

                record = {
                    "market": cfg["market"],
                    "source_domain": cfg["domain"],
                    "source_url": listing_url,
                    "title": detail.get("title") or seed["title"],
                    "description": detail.get("description") or seed.get("description", ""),
                    "url": url,
                    "canonical_url": normalize_url(detail.get("canonical_url") or url),
                    "language": detect_language(
                        detail.get("title", ""),
                        detail.get("description", ""),
                        detail.get("language_hint", ""),
                        cfg.get("language", "")
                    ),
                    "categories": [],
                    "published_date": "",
                    "last_seen": run_time
                }

                record["content_hash"] = content_hash(record)
                key = record["canonical_url"] or record["url"]

                if key not in history:
                    status = "NEW"
                    record["first_seen"] = run_time
                    changes.append({"type": status, "record": record})
                else:
                    old = history[key]
                    status = "UPDATED" if old.get("content_hash") != record["content_hash"] else "EXISTING"
                    record["first_seen"] = old.get("first_seen", run_time)
                    if status == "UPDATED":
                        changes.append({"type": status, "record": record})

                record["status"] = status
                current[key] = record

    # Preserve historical records that were not found this run.
    next_history = dict(history)
    for key, record in current.items():
        next_history[key] = record

    save_json(DATA / "current.json", list(current.values()))
    save_json(DATA / "history.json", next_history)
    save_json(DATA / "changes.json", {
        "run_at": run_time,
        "summary": {
            "sources": len(sources),
            "discovered": len(current),
            "new": sum(1 for x in changes if x["type"] == "NEW"),
            "updated": sum(1 for x in changes if x["type"] == "UPDATED"),
            "errors": sum(1 for x in changes if x["type"] == "ERROR")
        },
        "changes": changes
    })

    summary = json.loads((DATA / "changes.json").read_text(encoding="utf-8"))["summary"]
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    run()
