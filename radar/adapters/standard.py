from bs4 import BeautifulSoup
from ..utils import absolute_url, clean_text

CASE_SIGNALS = (
    "case study", "client story", "client stories", "success story",
    "success stories", "cas client", "storie di successo",
    "kundreferens", "kundreferenser", "referencer", "success story"
)

def _candidate_links(soup, base_url):
    # Prefer article/card-like containers, then fall back to headings containing links.
    containers = soup.select("article, li, .card, [class*='card'], [class*='story'], [class*='case']")
    seen = set()
    for container in containers:
        link = container.find("a", href=True)
        if not link:
            continue
        href = absolute_url(base_url, link["href"])
        title_el = container.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        title = clean_text(title_el.get_text(" ", strip=True) if title_el else link.get_text(" ", strip=True))
        if not title or href in seen:
            continue
        seen.add(href)
        description = ""
        p = container.find("p")
        if p:
            description = clean_text(p.get_text(" ", strip=True))
        yield {"title": title, "url": href, "description": description}

def extract_listing(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    candidates = list(_candidate_links(soup, base_url))

    # Fallback: links whose nearby text strongly suggests a story/case-study section.
    if not candidates:
        for a in soup.find_all("a", href=True):
            text = clean_text(a.get_text(" ", strip=True))
            parent_text = clean_text(a.parent.get_text(" ", strip=True)) if a.parent else ""
            combined = f"{text} {parent_text}".lower()
            if text and any(signal in combined for signal in CASE_SIGNALS):
                candidates.append({
                    "title": text,
                    "url": absolute_url(base_url, a["href"]),
                    "description": ""
                })
    return candidates

def extract_detail(html, url, seed=None):
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = clean_text(h1.get_text(" ", strip=True))
    if not title:
        og = soup.find("meta", attrs={"property": "og:title"})
        title = clean_text(og.get("content", "") if og else "")
    if not title and seed:
        title = seed.get("title", "")

    description = ""
    ogd = soup.find("meta", attrs={"property": "og:description"})
    if ogd:
        description = clean_text(ogd.get("content", ""))
    if not description:
        p = soup.find("p")
        if p:
            description = clean_text(p.get_text(" ", strip=True))

    lang = ""
    html_tag = soup.find("html")
    if html_tag:
        lang = (html_tag.get("lang") or "").split("-")[0].lower()

    canonical = soup.find("link", rel="canonical")
    canonical_url = clean_text(canonical.get("href", "")) if canonical else url

    return {
        "title": title,
        "description": description,
        "canonical_url": absolute_url(url, canonical_url) if canonical_url else url,
        "language_hint": lang,
    }
