# ConvergenceTerminal: Complete Master Handoff & Architecture Blueprint

## 1. Executive Context & Core Mission
* **Project Name**: ConvergenceTerminal
* **Foundational Philosophy**: A dedicated, personal-to-public intelligence terminal replacing the noise, algorithmic rage-bait, and dopamine trap of social feeds (specifically X.com) with high-signal, synthesized, and contextualized intelligence.
* **The Core Intersection**:
  * **Bitcoin**: Sound money, sovereign balance sheets, treasury strategies, and the Lightning payment network.
  * **Energy & Compute Infrastructure**: Baseload power, thermodynamics, ERCOT/grid dynamics, nuclear deals, and data center scaling.
  * **Autonomous AI & Agents**: Machine-to-machine micropayments, local edge intelligence, and autonomous economic actors.
* **The Guiding Mindset**: High-density, high-agency curation. We track the thinkers and entities, not the raw, unfiltered timelines.

---

## 2. Strategic Insights & Architectural Decisions

### A. The Palantir Framing (Curing the "AI Intimidation")
* **The Insight**: AI is often intimidating when viewed as abstract models, codebases, and academic papers.
* **The Solution**: Adopt the Palantir Foundry/AIP approach: construct an **Ontology**. We do not track "all of AI." We track AI through an operational, infrastructure, and capital lens:
  1. AI as an energy sink (competing with and complementing Bitcoin miners on power grids).
  2. AI agents as economic actors needing instant, borderless, counterparty-free settlement rails (the Lightning Network).
  3. Bitcoin treasuries and AI firms as capital allocators managing balance sheet sovereignty against fiat debasement.

### B. The "Lyn Alden Standard" (The Editorial Filter)
* **Rule 1: Thermodynamic & Physical Reality**: Proof-of-Work and AI cluster scaling both collide with energy availability and electrical grid realities.
* **Rule 2: Macro Plumbing & Global Liquidity**: Evaluation based on M2, debt issuance, fiscal dominance, and monetary debasement—not speculative token trading.
* **Rule 3: Network Topology & Engineering**: Protocol-level engineering mechanics over hype or marketing promises.
* **Rule 4: Zero Sludge**: Outrage bait, tribal flame wars, price predictions, and personality drama are strictly dropped at the ingestion layer.

### C. Economics & Ingestion Reality
* **Official X API**: Pay-per-read tollbooth (\$0.005/post read). Polling 100 accounts daily costs ~\$300–\$750/month. **Verdict: Avoid for this phase.**
* **Developer Relays (e.g., TwitterAPI.io / Social Fetch)**: Wholesale developer rates (~\$0.15 per 1,000 reads). Tracking 100 accounts costs ~\$9–\$20/month. **Verdict: Primary social path.**
* **Free Long-Form RSS**: Substack feeds, personal blogs, technical whitepapers, and GitHub releases cost \$0.00. **Verdict: Essential anchor.**
* **Synthesis Cost**: Gemini 1.5/2.0 Flash API costs ~\$5–\$10/month for daily deduplication and analysis.
* **Total Annual Run-Rate**: Well within the \$500–\$1,000 target budget (~\$150–\$250/year total).

---

## 3. Seed Entities (Initial Tracking List)
1. **Lyn Alden**: Macro liquidity, fiscal dominance, energy physics, network topology.
2. **Jack Mallers / Lightning Labs**: Layer-2 settlement, machine-to-machine AI payments.
3. **Andrej Karpathy**: Autonomous agents, edge compute, core intelligence developments.
4. **Arthur Hayes**: Global sovereign debt, currency dynamics, macro liquidity cycles.
5. **Grid & Power Monitors (e.g., ERCOT, Clean Energy Trackers)**: Baseload energy, colocation of Bitcoin mining and AI data centers.

---

## 4. Technical Specifications & Schemas

### A. Directory Structure
```
convergence-terminal/
├── public/
│   ├── index.html           # Minimalist terminal UI (Tailwind CSS CDN)
│   ├── app.js               # Feed renderer & inline SVG sparkline generator
│   ├── styles.css           # Custom dark styling & monospace chips
│   └── data.json            # Enriched data feed produced by ingestion pipeline
├── scripts/
│   ├── ingest.py            # Aggregates RSS + social relay data
│   ├── synthesize.py        # Gemini intelligence enrichment pipeline
│   └── mock_inputs.json     # 10 test records for offline staging and verification
├── requirements.txt         # google-genai, requests, feedparser
└── README.md
```

### B. Standard Ingestion Data Contract (`data.json`)
```json
{
  "items": [
    {
      "id": "uuid-string",
      "timestamp": "2026-09-09T18:30:00Z",
      "entity": {
        "name": "Lyn Alden",
        "handle": "@LynAldenContact",
        "platform": "x",
        "avatar_url": "/avatars/lynalden.png"
      },
      "source_url": "https://...",
      "category": "Compute, Power & The Grid",
      "raw_summary": "ERCOT power auction prices show rising premium for flexible baseload curtailment.",
      "elevated_intelligence": {
        "signal_headline": "Baseload Grid Premium Escalates as Data Centers Compete with Miners",
        "alden_lens": "Thermodynamics and physical electricity contracts remain the true bottleneck for both AI compute clusters and PoW hashing.",
        "cross_reference": "Directly links to recent corporate nuclear power purchase agreements and miner colocation pivots.",
        "is_urgent_shift": true
      },
      "metrics": {
        "velocity_score": 8.7,
        "momentum_label": "+340% 6h spike",
        "sparkline_points": [12, 18, 15, 34, 60, 95, 130]
      }
    }
  ]
}
```

### C. Gemini System Prompt ("Alden Engine")
You are the Chief Intelligence Officer for ConvergenceTerminal, operating under the "Alden Standard."

**Mission**:
Ingest unstructured text feeds from tracked entities covering Bitcoin, energy grids, and AI systems. Discard engagement bait, short-term price gossip, and personal feuds. Synthesize signals into clear, actionable intelligence grounded in thermodynamics, macro liquidity (M2/fiscal dominance), and settlement infrastructure.

**For each valid item**:
1. Filter: Drop anything purely speculative or low-signal.
2. Categorize: Assign one of:
   - `"Compute, Power & The Grid"`
   - `"Agentic Rails & Settlement"`
   - `"Macro Plumbing & Balance Sheets"`
   - `"Autonomous Intelligence"`
3. Enrich: Formulate the Alden Lens explanation (1-2 sentences) on how physical limits or monetary architecture are affected.
4. Cross-Reference: Explicitly identify related historical macro movements or parallel corporate actions.
5. Score: Provide a velocity score (1.0 - 10.0), a spike label, and 7 integers representing relative 7-day momentum points.
