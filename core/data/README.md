# Where does this “data” come from?

These files are **curated notes for your Senso knowledge base**, not a live API.

1. **You create them** — policies, FAQs, brand voice, product docs, transcripts, anything you want the agent to *ground* answers in.
2. **You pull from the web** — industry blogs, official creator newsrooms, docs (always check dates and bias).
3. **This repo includes starters** — `kb_*.md` files were built from **public web search summaries (March 2026)** with **source links** at the bottom of each file so you can verify or replace them.

## Ingest into Senso

From `core/`:

```bash
cd core
source .venv/bin/activate
uv run ingest_senso.py data/kb_shortform_trends_2026.md data/kb_hooks_and_openers.md
```

Then `POST /org/search` in qwkly can return answers grounded in this content.

## Refreshing

Trends and algorithms change. Re-run web research periodically, edit the markdown, and re-ingest or update documents in the Senso UI per your org’s workflow.
