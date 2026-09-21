from bs4 import BeautifulSoup
from ..utils import absolute_url, clean_text

SIGNALS = (
    "case study", "case studies", "client story", "client stories",
    "success story", "success stories", "cas client", "storie di successo",
    "kundreferens", "kundreferenser", "referencer", "succesverhaal",
    "succesverhalen", "prosjekt", "prosjekter"
)

def extract_listing(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    results, seen = [], set()
    for a in soup.find_all("a", href=True):
        text = clean_text(a.get_text(" ", strip=True))
        parent = clean_text(a.parent.get_text(" ", strip=True)) if a.parent else ""
        haystack = f"{text} {parent}".lower()
        if not text or not any(s in haystack for s in SIGNALS):
            continue
        url = absolute_url(base_url, a["href"])
        if url in seen:
            continue
        seen.add(url)
        results.append({"title": text, "url": url, "description": ""})
    return results

def extract_detail(html, url, seed=None):
    from .standard import extract_detail
    return extract_detail(html, url, seed)
