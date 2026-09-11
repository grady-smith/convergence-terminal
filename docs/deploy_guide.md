# 🌐 ConvergenceTerminal: Zero-Cost Deployment Guide

**Total Monthly Hosting Cost**: **$0.00**

---

## 🏗️ Architecture Overview

ConvergenceTerminal is designed as a **decoupled static terminal**:

1. **Frontend (`public/`)**: Pure HTML5, Tailwind CSS, and Vanilla JavaScript — served statically.
2. **Backend Pipeline (`internal/scripts/`)**: Three-stage Python pipeline running entirely on stdlib.
   - **Stage 1 — Ingest** (`ingest.py`): Pulls RSS feeds and Twitter relay data → stores raw posts in SQLite.
   - **Stage 2 — Filter + Synthesize** (`pipeline.py`): Applies sludge bouncer rules, classifies topics, enriches signals under the Convergence First-Principles Engine.
   - **Stage 3 — Export** (`db.py`): Joins entities + signals from SQLite → writes clean `public/data.json`.
3. **Delivery**: The pipeline outputs `public/data.json`. Any static host serves the `public/` directory with zero server-side maintenance.

### Canonical Execution Path

```
python3 internal/scripts/ingest.py
          │
          ├─► ingest.py      (RSS + Twitter relay → SQLite raw_posts)
          ├─► pipeline.py    (sludge filter + Alden lens synthesis → SQLite signals)
          └─► db.py          (JOIN query + export → public/data.json)
```

> **Note**: `scripts/ingest.py` and `scripts/synthesize.py` at the project root are thin dispatchers that simply delegate to `internal/scripts/`. They exist for convenience; the canonical implementations are in `internal/scripts/`.

---

## 🚀 Option 1: Cloudflare Pages (Recommended — $0.00)

**Why Cloudflare Pages?**
- Unlimited bandwidth.
- Instant global edge caching across 300+ cities.
- Automatic SSL certificates and DDoS shielding.

**Setup Steps:**
1. Log into [Cloudflare Dashboard](https://dash.cloudflare.com/) → **Workers & Pages**.
2. Click **Create Application** → **Pages** → **Connect to Git**.
3. Select this repository.
4. Set **Build output directory** to: `public`
5. Leave **Build command** empty (pure static files).
6. Click **Save and Deploy**. Site goes live at `https://convergenceterminal.pages.dev`.

---

## 🐙 Option 2: GitHub Pages ($0.00)

1. Go to repository **Settings** → **Pages**.
2. Under **Build and deployment** → **Source**, select **Deploy from a branch**.
3. Set Branch to `main`, folder to `/public`.
4. Click **Save**. Site goes live at `https://<username>.github.io/<repo-name>/`.

---

## ⏱️ Automated Scheduling (GitHub Actions — $0.00)

The workflow at [`.github/workflows/ingest.yml`](../.github/workflows/ingest.yml) runs **3× daily** (06:00, 14:00, 22:00 UTC):

```yaml
# What the workflow does in sequence:
python3 internal/scripts/ingest.py   # Full pipeline: ingest → filter → synthesize → export
git add public/data.json internal/db/terminal.db internal/data/archive/
git commit -m "chore(feed): automated intelligence update [skip ci]"
git push
```

- Consumes ~90 minutes/month out of your **2,000 free monthly GitHub Actions minutes**.
- Cloudflare Pages / GitHub Pages auto-detects the commit and redeploys in seconds.

---

## 🔑 Secret Keys Configuration (Required for Live Mode)

When moving from offline staging to live data ingestion:

1. In your GitHub repository: **Settings** → **Secrets and variables** → **Actions**.
2. Add the following secrets:

| Secret Name | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key for AI-powered Alden lens synthesis |
| `TWITTER_API_KEY` | TwitterAPI.io relay key for live tweet ingestion |

> **Security Note**: Never commit `.env` to version control. The `.gitignore` lists `.env` — verify with `git check-ignore -v .env` that it is properly excluded before pushing to a remote.

---

## 🧪 Offline Staging (No API Keys Required)

Test the pipeline locally without any live API calls:

```bash
# Reads internal/data/mock_inputs.json and writes public/data.json
python3 internal/scripts/synthesize.py

# Run the full unit test suite (13 tests)
cd internal/scripts && python3 -m unittest test_pipeline -v
```
