# Case Study Radar

Free, deterministic monitoring of Sopra Steria case studies/client stories.

## Principles

- No OpenAI/Gemini/Claude API
- No paid scraping service
- No translation API
- No LLM classification
- Original-language content is preserved
- URL + content hash drive NEW/UPDATED detection
- GitHub Actions runs the scraper on a schedule
- JSON files are the source for a future dashboard

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

Outputs:

- `data/current.json`
- `data/history.json`
- `data/changes.json`

## Important

The source selectors are intentionally conservative in V1. Website structures can change, so each market should be audited and given a dedicated adapter when the generic adapter is insufficient.

This repository is a scraper foundation, not a guarantee that every case study on every market site will be discovered on the first run.
