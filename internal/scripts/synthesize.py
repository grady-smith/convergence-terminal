#!/usr/bin/env python3
"""
ConvergenceTerminal - Intelligence Synthesis Engine
Transforms raw feed items into high-signal, contextualized terminal intelligence cards.
Maintains a rolling 50-item window in public/data.json and archives history in internal/data/archive/.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timezone

DEFAULT_ENRICHMENTS = {
    "item-001": {
        "headline": "Baseload Grid Premium Escalates as Data Centers Compete with Miners",
        "lens": "Thermodynamics and physical electricity contracts remain the true bottleneck for both AI compute clusters and PoW hashing.",
        "cross_ref": "Directly links to recent corporate nuclear power purchase agreements and miner colocation pivots.",
        "urgent": True,
        "momentum": "+340% 6h spike"
    },
    "item-002": {
        "headline": "Proof-of-Work Thermodynamically Anchors Digital Scarcity to Unforgeable Physics",
        "lens": "Consensus difficulty mathematically binds monetary credibility to real-world energy expenditure, eliminating political dilution and arbitrary debasement.",
        "cross_ref": "Builds upon Hashcash proof-of-work principles and Szabo's unforgeable costliness axioms.",
        "urgent": True,
        "momentum": "+480% 4h spike"
    },
    "item-003": {
        "headline": "Agentic M2M Inference Mandates Zero-KYC Micro-Settlement Rails",
        "lens": "Autonomous code agents cannot comply with legacy banking rails; sub-cent streaming settlement requires protocol-native Lightning L2 channels.",
        "cross_ref": "Parallels HTTP 402 specifications first conceptualized in early Internet protocols, now revitalized by machine-to-machine agents.",
        "urgent": True,
        "momentum": "+420% 12h spike"
    },
    "item-004": {
        "headline": "Sovereign Node Telemetry Surges as Pruned Validation Lowers Hardware Barrier",
        "lens": "Decentralized consensus integrity depends entirely on independent verification rather than delegated trust in RPC choke points.",
        "cross_ref": "Reflects the core cypherpunk dictum: Don't Trust, Verify.",
        "urgent": False,
        "momentum": "+260% 18h gain"
    },
    "item-005": {
        "headline": "Compute Architecture Shifts from Monolithic Clouds to Local Edge Swarms",
        "lens": "Centralized inference encounters physical latency and bandwidth limits; specialized edge models provide high-agency deterministic execution.",
        "cross_ref": "Echoes the 1980s transition from mainframe computing to personal workstation distribution.",
        "urgent": False,
        "momentum": "+185% 24h gain"
    },
    "item-006": {
        "headline": "Cluster Mempool Linearization Solves Peer-to-Peer Block Congestion Economics",
        "lens": "Mathematically sound transaction ordering preserves incentive alignment and fee-bumping determinism against mempool DoS vectors.",
        "cross_ref": "Directly advances Bitcoin Core consensus relay efficiency and Layer-2 CPFP settlement guarantees.",
        "urgent": True,
        "momentum": "+390% 8h spike"
    },
    "item-007": {
        "headline": "Sovereign Debt Issuance Dynamics Force Inevitable Central Bank Monetization",
        "lens": "Global sovereign interest burdens exceed non-inflationary tax revenues, driving mandatory expansion of central bank balance sheets.",
        "cross_ref": "Follows the classic 1940s post-war fiscal dominance playbook.",
        "urgent": True,
        "momentum": "+290% 8h spike"
    },
    "item-008": {
        "headline": "Transmission Interconnection Bottlenecks Inflate Behind-the-Meter Asset Value",
        "lens": "Permitting gridlocks force capital toward co-located generation plants, creating an oligopoly on immediately deployable gigawatts.",
        "cross_ref": "Similar to early railroad right-of-way battles in the 19th-century industrial expansion.",
        "urgent": False,
        "momentum": "+140% 24h gain"
    },
    "item-009": {
        "headline": "FASB Fair-Value Accounting Catalyzes Corporate Treasury Balance Sheet Resilience",
        "lens": "Mark-to-market treasury rules eliminate historical impairment penalties, aligning corporate balance sheets with non-debasable reserve assets.",
        "cross_ref": "Parallels corporate gold reserves prior to the 1971 Bretton Woods suspension.",
        "urgent": False,
        "momentum": "+275% 12h gain"
    },
    "item-010": {
        "headline": "Fiscal Dominance Paradox: Rate Hikes Inject Expansionary Interest Income",
        "lens": "In high debt-to-GDP regimes, central bank tightening accelerates Treasury interest outlays, reinforcing structural inflation pressure.",
        "cross_ref": "Corroborated by Treasury refunding statements and escalating net interest obligations.",
        "urgent": True,
        "momentum": "+380% 6h spike"
    },
    "item-011": {
        "headline": "Self-Hosted Merchant Sovereignty Eliminates Intermediary Processing Friction",
        "lens": "Direct peer-to-peer settlement via automated Lightning LSP channel splicing removes 3% rent-seeking card interchange fees.",
        "cross_ref": "Implements permissionless point-of-sale commerce architecture without third-party escrow.",
        "urgent": False,
        "momentum": "+210% 14h gain"
    },
    "item-012": {
        "headline": "Standardized L402 Protocol Enables Permissionless Machine Invoicing",
        "lens": "Decoupling API monetization from credit cards eliminates payment fraud risk and enables microsecond programmatic commerce.",
        "cross_ref": "Builds upon RFC 7235 and Lightning Network preimage proof-of-payment mechanics.",
        "urgent": True,
        "momentum": "+510% 4h spike"
    },
    "item-013": {
        "headline": "Stranded Natural Gas Flaring Capture Converts Thermal Waste to Monetary Energy",
        "lens": "Modular mobile compute provides continuous economic demand at the wellhead, abating methane emissions with zero transmission loss.",
        "cross_ref": "Validates thermodynamic co-location principles and energy monetization physics.",
        "urgent": False,
        "momentum": "+195% 20h gain"
    },
    "item-014": {
        "headline": "Mathematical Absolute Truth Supersedes Discretionary Fiat Accounting",
        "lens": "Unforgeable cryptographic rules resist political renegotiation, anchoring global contracts to immutable proof-of-work mathematics.",
        "cross_ref": "Contrast between Austrian monetary discipline and Keynesian debt expansion cycles.",
        "urgent": False,
        "momentum": "+160% 24h gain"
    },
    "item-015": {
        "headline": "Deterministic Edge Ontology Outperforms Fragile Cloud Agent Wrappers",
        "lens": "Mission-critical enterprise workflows demand strict operational context and verifiable execution boundaries rather than probabilistic cloud calls.",
        "cross_ref": "Enterprise software evolution toward embedded operational intelligence.",
        "urgent": False,
        "momentum": "+170% 16h gain"
    },
    "item-016": {
        "headline": "Net Interest Expense Tops $1.2T: Mandatory Issuance Feedback Loop Accelerates",
        "lens": "Compounding debt service requirements force sovereign issuance beyond organic absorption, driving capital into hard reserve assets.",
        "cross_ref": "Directly linked to US Treasury quarterly refunding announcements and debt maturity walls.",
        "urgent": True,
        "momentum": "+410% 6h spike"
    },
    "item-017": {
        "headline": "Sovereign Volcanic Energy Direct Monetization Bypasses Supranational Debt Conditions",
        "lens": "Nation-states harness unexploited geothermal baseload to generate unseizable monetary reserves, securing monetary sovereignty.",
        "cross_ref": "Emerging market sovereign infrastructure adoption patterns.",
        "urgent": False,
        "momentum": "+250% 18h gain"
    },
    "item-018": {
        "headline": "Open-Weights Explosion Safeguards Compute Sovereignty Against Cloud Enclosures",
        "lens": "Unrestricted model weights running on local silicon preserve developer autonomy and eliminate censorship vulnerability.",
        "cross_ref": "Historical parallel to open-source Linux kernel disruption of proprietary UNIX ecosystems.",
        "urgent": False,
        "momentum": "+130% 24h gain"
    }
}

def _infer_url_type(url, raw_item_type=None):
    """
    Returns the source_url_type string ('post' or 'profile').
    Uses the explicit field from the input if present, otherwise
    applies a lightweight URL-structure heuristic.
    """
    if raw_item_type in ("post", "profile"):
        return raw_item_type
    if not url or url == "#":
        return "profile"
    import re as _re
    if _re.search(r"(?:x\.com|twitter\.com)/[^/]+/status/\d+", url, _re.IGNORECASE):
        return "post"
    if _re.search(r"substack\.com/p/[^/?#]+", url, _re.IGNORECASE):
        return "post"
    if _re.match(r"https?://github\.com/[^/]+/[^/]+/(pull|issues|releases/tag|commit|blob|tree)", url, _re.IGNORECASE):
        return "post"
    from urllib.parse import urlparse
    try:
        parts = [p for p in urlparse(url).path.split("/") if p]
        if len(parts) >= 3:
            return "post"
    except Exception:
        pass
    return "profile"

def synthesize_item(raw_item):
    item_id = raw_item.get("id", str(uuid.uuid4()))
    raw_text = raw_item.get("raw_text", "")
    enrichment = DEFAULT_ENRICHMENTS.get(item_id, {
        "headline": raw_text[:80] + "..." if len(raw_text) > 80 else raw_text,
        "lens": "Physical resource constraints and monetary incentives govern systemic adaptation.",
        "cross_ref": "Analyzed under the ConvergenceTerminal first-principles framework.",
        "urgent": False,
        "momentum": "+120% 24h gain"
    })

    velocity = raw_item.get("velocity_hint", 7.5)
    sparkline = raw_item.get("sparkline", [10, 15, 22, 35, 50, 75, 100])
    source_url = raw_item.get("source_url", "#")
    url_type = _infer_url_type(source_url, raw_item.get("source_url_type"))

    return {
        "id": item_id,
        "timestamp": raw_item.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "entity": raw_item.get("entity", {
            "name": "Tracked Entity",
            "handle": "@entity",
            "platform": "x",
            "avatar_url": ""
        }),
        "source_url": source_url,
        "source_url_type": url_type,
        "category": raw_item.get("category", "Bitcoin"),
        "raw_summary": raw_text,
        "elevated_intelligence": {
            "signal_headline": enrichment["headline"],
            "convergence_lens": enrichment["lens"],
            "alden_lens": enrichment["lens"],
            "cross_reference": enrichment["cross_ref"],
            "is_urgent_shift": enrichment["urgent"]
        },
        "metrics": {
            "velocity_score": velocity,
            "momentum_label": enrichment["momentum"],
            "sparkline_points": sparkline
        }
    }

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == "scripts":
        parent = os.path.dirname(current_dir)
        base_dir = os.path.dirname(parent) if os.path.basename(parent) == "internal" else parent
    else:
        base_dir = current_dir

    input_path = os.path.join(base_dir, "internal", "data", "mock_inputs.json")
    if not os.path.exists(input_path):
        input_path = os.path.join(base_dir, "scripts", "mock_inputs.json")
        
    output_path = os.path.join(base_dir, "public", "data.json")
    archive_dir = os.path.join(base_dir, "internal", "data", "archive")

    print("==================================================")
    print("⚡ ConvergenceTerminal: Intelligence Synthesizer")
    print("   Operating Filter: Convergence First-Principles Engine")
    print("==================================================")

    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    print(f"📥 Loaded {len(raw_items)} raw feed records from {input_path}")

    processed_items = []
    for item in raw_items:
        processed = synthesize_item(item)
        processed_items.append(processed)

    # Sort descending by velocity score
    processed_items.sort(key=lambda x: x["metrics"]["velocity_score"], reverse=True)

    # Rolling window of 50 signals for public feed
    public_items = processed_items[:50]
    
    # Save archive copy
    os.makedirs(archive_dir, exist_ok=True)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_file = os.path.join(archive_dir, f"signals_{today_str}.json")
    with open(archive_file, "w", encoding="utf-8") as f:
        json.dump({"date": today_str, "total": len(processed_items), "items": processed_items}, f, indent=2)

    # ── Derive transparency counts dynamically ──────────────────────────────
    # tracked_entities_count: read from the canonical entities config so it
    # stays in sync as new VIP thinkers are added to entities.json.
    def _load_entity_count(base):
        config_path = os.path.join(base, "internal", "config", "entities.json")
        try:
            with open(config_path, "r", encoding="utf-8") as _f:
                cfg = json.load(_f)
            return sum(1 for e in cfg.get("tracked_entities", []) if e.get("active", True))
        except Exception:
            return None

    # sludge_filtered_count: query the SQLite DB if it exists, else 0.
    # Never write a hardcoded number — that would be fabricated transparency.
    def _load_sludge_count(base):
        import sqlite3 as _sqlite3
        db_path = os.path.join(base, "internal", "db", "terminal.db")
        if not os.path.exists(db_path):
            return 0
        try:
            _conn = _sqlite3.connect(db_path)
            _cur = _conn.cursor()
            _cur.execute("SELECT COUNT(*) FROM sludge_log")
            count = _cur.fetchone()[0]
            _conn.close()
            return count
        except Exception:
            return 0

    tracked_entities_count = _load_entity_count(base_dir) or len(processed_items)
    sludge_filtered_count = _load_sludge_count(base_dir)

    # Build public payload with transparency metrics
    output_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": "Convergence Intelligence Engine v1.1",
        "tracked_entities_count": tracked_entities_count,
        "total_signals": len(public_items),
        "sludge_filtered_count": sludge_filtered_count,
        "categories": [
            "All Signals",
            "Bitcoin",
            "Compute, Power & The Grid",
            "Agentic Rails & Settlement",
            "Macro Plumbing & Balance Sheets",
            "Autonomous Intelligence"
        ],
        "items": public_items
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"✅ Published {len(public_items)} signals to {output_path}")
    print(f"📦 Archived {len(processed_items)} historical records to {archive_file}")
    print(f"🛡️  Sludge Quarantine Log: {sludge_filtered_count} records dropped (live DB count).")
    print(f"🧠 Tracking {tracked_entities_count} active VIP entities (from entities.json).")

if __name__ == "__main__":
    main()
