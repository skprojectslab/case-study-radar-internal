import requests

HEADERS = {
    "User-Agent": "CaseStudyRadar/1.0 (+https://github.com/)"
}

def get(url, timeout=30):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text
