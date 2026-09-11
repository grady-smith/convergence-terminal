# ⚡ ConvergenceTerminal

> **High-Signal Intelligence Terminal** at the nexus of **Bitcoin**, **Energy & Compute Grids**, and **Autonomous AI Agents** under the **Convergence First-Principles Engine**.

---

## 🏛️ Executive Philosophy
ConvergenceTerminal replaces the noise, algorithmic rage-bait, and dopamine trap of social feeds with curated, synthesized, and contextualized intelligence across 32 VIP leaders and thinkers.

### The Convergence First-Principles Standard:
1. **Thermodynamic & Physical Reality**: PoW and AI cluster scaling both collide with energy availability and electrical grid realities.
2. **Hard Monetary Physics & Bitcoin Scarcity**: Absolute mathematical truth and unforgeable energy-backed consensus over discretionary fiat accounting.
3. **Macro Plumbing & Global Liquidity**: Evaluation based on M2, sovereign debt rollover walls, fiscal dominance, and collateral scarcity.
4. **Agentic Rails & Protocol Topology**: Machine-to-machine streaming micro-settlement via Lightning L2 / L402 protocols and decentralized nodes.
5. **Zero Sludge**: Outrage bait, tribal flame wars, short-term price guessing, and engagement farming are strictly dropped at ingestion.

---

## 📂 Project Structure

```
convergence-terminal/
├── ARCHITECTURE.md              # Architecture documentation
├── requirements.txt             # Python deps (currently stdlib-only; see file for future additions)
├── .github/
│   └── workflows/
│       └── ingest.yml           # Automated CI/CD pipeline (runs 3x/day)
├── docs/
│   ├── convergence_terminal_handoff.md  # Master Architecture & Ingestion blueprint
│   └── deploy_guide.md          # Zero-cost Cloudflare / GitHub Pages deployment
├── public/                      # ← Static site served directly to the internet
│   ├── index.html               # Minimalist dark terminal UI (Tailwind CSS CDN)
│   ├── app.js                   # Feed renderer & inline SVG sparkline generator
│   ├── styles.css               # Custom dark styling & monospace chips
│   └── data.json                # Enriched signal feed produced by the pipeline
├── internal/                    # ← Operational backend (never served publicly)
│   ├── config/
│   │   ├── entities.json        # 32 tracked VIP thinkers + feed endpoints
│   │   └── crypto_twitter_watchlist.json
│   ├── data/
│   │   ├── mock_inputs.json     # 18 offline test records for staging
│   │   ├── sludge_quarantine.json
│   │   └── archive/             # Historical daily signal snapshots
│   ├── db/
│   │   ├── schema.sql           # SQLite schema (entities, raw_posts, sludge_log, signals)
│   │   └── terminal.db          # Live SQLite database (git-ignored in production)
│   ├── ledger/                  # Cost & budget ledger
│   └── scripts/                 # ← Canonical pipeline — all logic lives here
│       ├── ingest.py            # Stage 1: RSS + Twitter relay ingestion → SQLite
│       ├── pipeline.py          # Stage 2: Sludge filter + topic synthesis engine
│       ├── synthesize.py        # Standalone offline synthesizer (reads mock_inputs.json)
│       ├── db.py                # SQLite controller + public data exporter
│       └── test_pipeline.py     # Full unit test suite (13 tests)
└── scripts/                     # ← Thin dispatchers only — delegate to internal/
    ├── ingest.py                # → delegates to internal/scripts/ingest.py
    ├── synthesize.py            # → delegates to internal/scripts/synthesize.py
    └── mock_inputs.json         # Mirror of internal/data/mock_inputs.json
```

---

## 🚀 Quick Start

### Canonical Pipeline (Live Mode)

This is the path run by GitHub Actions and used in production:

```bash
# Stage 1: Ingest RSS feeds + Twitter relay → SQLite DB
python3 internal/scripts/ingest.py

# The pipeline automatically calls pipeline.py and db.py to filter, synthesize,
# and export public/data.json in a single run.
```

### Offline Staging (No API Keys Required)

Use this to test synthesis logic locally against mock data:

```bash
# Reads internal/data/mock_inputs.json → writes public/data.json
python3 internal/scripts/synthesize.py

# Or via the top-level dispatcher (same result):
python3 scripts/synthesize.py
```

### Local Web Terminal

```bash
python3 -m http.server 8080 --directory public
```
Open [http://localhost:8080](http://localhost:8080) in your browser.

### Run Tests

```bash
cd internal/scripts && python3 -m unittest test_pipeline -v
```

---

## 🔄 Data Flow

```
entities.json          mock_inputs.json (offline)
     │                        │
     ▼                        ▼
ingest.py  ──────────► pipeline.py
  (RSS + Twitter)       (Sludge filter + topic synthesis)
                               │
                               ▼
                             db.py
                       (SQLite storage + export)
                               │
                               ▼
                        public/data.json
                               │
                               ▼
                      public/index.html + app.js
                        (Static terminal UI)
```
