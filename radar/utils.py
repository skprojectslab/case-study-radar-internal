import hashlib
import re
from urllib.parse import urljoin, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid"
}

def normalize_url(url: str) -> str:
    p = urlparse(url.strip())
    query_parts = []
    if p.query:
        for part in p.query.split("&"):
            key = part.split("=", 1)[0].lower()
            if key and key not in TRACKING_PARAMS:
                query_parts.append(part)
    path = re.sub(r"/+", "/", p.path or "/")
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", "&".join(query_parts), ""))

def absolute_url(base: str, href: str) -> str:
    return normalize_url(urljoin(base, href))

def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()

def content_hash(record: dict) -> str:
    payload = "||".join([
        clean_text(record.get("title", "")),
        clean_text(record.get("description", "")),
        clean_text(record.get("client_name", "")),
        clean_text(record.get("published_date", "")),
        "|".join(sorted(record.get("categories", []) or [])),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
