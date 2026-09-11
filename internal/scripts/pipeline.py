#!/usr/bin/env python3
"""
ConvergenceTerminal Two-Stage Ingestion & Curation Pipeline

Stage 1: Sludge Filter (Fast Bouncer) -> Rejects noise, rage-bait, price predictions
Stage 2: Alden Engine (Synthesis) -> Contextualizes physical, monetary & settlement signals
"""

import os
import sys
import json
import re
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import db

# ==========================================
# STAGE 1: SLUDGE FILTER HEURISTICS & RULES
# ==========================================

SLUDGE_PATTERNS = [
    (r"\b(price target|moon soon|parabolic pump|100k incoming|easy 10x|buy the dip|sell target)\b", 
     "Speculative price target / hype without macro basis", "Rule 2 & Rule 4"),
    (r"\b(\$BTC to \$?[0-9]+k|\$ETH to \$?[0-9]+k|next 100x gem)\b", 
     "Short-term price guessing / token promotion", "Rule 2 & Rule 4"),
    (r"\b(retweet if|like and follow|drop your address|giveaway|tag 3 friends|drop your wallet)\b", 
     "Social engagement bait / algorithmic farm", "Rule 4 (Zero Sludge)"),
    (r"\b(is a fraud|total clown|get rekt|stay poor|cope and seethe|savage feud|ratio)\b", 
     "Personality drama / tribal flame war", "Rule 4 (Zero Sludge)")
]

def evaluate_sludge(text):
    clean_text = text.lower()
    for pattern, reason, rule in SLUDGE_PATTERNS:
        if re.search(pattern, clean_text, re.IGNORECASE):
            return True, reason, rule
            
    if len(text.strip().split()) < 5:
        return True, "Insufficient context / low-signal brevity", "Rule 4 (Zero Sludge)"
        
    return False, "", ""

# ==========================================
# STAGE 2: THE ALDEN ENGINE SYNTHESIS
# ==========================================

# Fine-grained topic synthesis matrix
TOPIC_SYNTHESIZERS = [
    (
        r"(hashcash|proof-of-work|pow\b|mining|hashrate|thermodynamic|energy-backed)",
        "Bitcoin",
        "Proof-of-Work Thermodynamically Anchors Digital Scarcity to Unforgeable Physics",
        "Consensus difficulty mathematically binds monetary credibility to real-world energy expenditure, eliminating political dilution and arbitrary debasement.",
        "Builds upon Hashcash proof-of-work principles and Szabo's unforgeable costliness axioms.",
        True
    ),
    (
        r"(mempool|node|utxo|full node|bitcoin core|cluster mempool)",
        "Bitcoin",
        "Cluster Mempool Linearization & Sovereign Node Telemetry Fortify Consensus Topology",
        "Decentralized consensus integrity depends entirely on independent verification rather than delegated trust in centralized RPC choke points.",
        "Directly advances Bitcoin Core peer-to-peer consensus relay and Layer-2 settlement guarantees.",
        True
    ),
    (
        r"(lightning|l402|cashu|ecash|micropayment|m2m|settlement|strike)",
        "Agentic Rails & Settlement",
        "Autonomous Agent Swarms Mandate Protocol-Native Micro-Settlement Rails",
        "Autonomous code agents cannot hold bank accounts or KYC cards; sub-cent streaming settlement requires protocol-native Lightning L2 channels.",
        "Parallels early HTTP 402 specifications now revitalized for machine-to-machine inference.",
        True
    ),
    (
        r"(ercot|grid|baseload|nuclear|power|megawatt|gw\b|substation|interconnection|curtailment)",
        "Compute, Power & The Grid",
        "Baseload Grid Interconnection Bottlenecks Accelerate Behind-the-Meter Power Co-Location",
        "Thermodynamics and physical power contracts remain the non-negotiable bottleneck for both AI compute clusters and Proof-of-Work hashing.",
        "Directly links to recent corporate nuclear power purchase agreements and miner colocation pivots.",
        True
    ),
    (
        r"(blackwell|gpu|nvidia|accelerated compute|silicon|jensen)",
        "Compute, Power & The Grid",
        "Accelerated Silicon Clusters Collide with Substation Transformer Availability",
        "Compute scaling is governed by electrical substation capacity and thermal dissipation physics rather than raw chip density.",
        "Echoes the historical transition from single-core CPU frequency scaling to massive parallel power-constrained architectures.",
        True
    ),
    (
        r"(treasury|debt|deficit|liquidity|m2\b|fiscal dominance|yield curve|refunding|fed\b|interest expense|rollover)",
        "Macro Plumbing & Balance Sheets",
        "Fiscal Dominance Paradox: Treasury Debt Refunding Forces Central Bank Monetization",
        "In high sovereign debt-to-GDP regimes, central bank interest outlays expand private liquidity, structurally forcing capital into scarce monetary assets.",
        "Follows the 1940s post-war fiscal dominance framework and ongoing Treasury refunding dynamics.",
        True
    ),
    (
        r"(karpathy|agent|swarm|distill|local model|edge compute|inference|open weight|hugging face)",
        "Autonomous Intelligence",
        "Compute Architecture Shifts from Cloud Monoliths to Distributed Edge Agents",
        "Physical latency and privacy constraints drive the unbundling of general intelligence into task-specific deterministic local models.",
        "Validates the historical transition from mainframe compute to personal workstation distribution.",
        False
    ),
    (
        r"(palantir|ontology|aip|operational|decision system|sankar)",
        "Autonomous Intelligence",
        "Operational Decision Systems Require Verifiable High-Agency Ontologies",
        "Enterprise autonomy demands strict deterministic operational bounds and verified semantic mapping rather than probabilistic general-purpose models.",
        "Validates the evolution of mission-critical command architectures in defense and enterprise systems.",
        False
    ),
    (
        r"(fasb|fair-value|balance sheet|treasury reserve|corporate treasury)",
        "Bitcoin",
        "Fair-Value Accounting Catalyzes Corporate Treasury Balance Sheet Sovereignty",
        "Mark-to-market treasury rules eliminate historical impairment penalties, aligning corporate balance sheets with non-debasable reserve assets.",
        "Parallels corporate gold reserves prior to the 1971 Bretton Woods suspension.",
        False
    ),
    (
        r"(btcpay|merchant|point-of-sale|non-custodial)",
        "Bitcoin",
        "Permissionless Point-of-Sale Architecture Eliminates Intermediary Friction",
        "Direct peer-to-peer settlement via automated Lightning LSP channel splicing removes 3% rent-seeking card interchange fees.",
        "Implements permissionless point-of-sale commerce architecture without third-party escrow.",
        False
    ),
    (
        r"(volcanic|geothermal|nation-state|aqua|jan3)",
        "Bitcoin",
        "Sovereign Volcanic Energy Direct Monetization Bypasses Supranational Debt",
        "Nation-states harness unexploited geothermal baseload to generate unseizable monetary reserves, securing economic sovereignty.",
        "Emerging market sovereign infrastructure adoption patterns.",
        False
    ),
    (
        r"(stranded gas|flaring|methane|oilfield)",
        "Compute, Power & The Grid",
        "Stranded Natural Gas Flaring Capture Converts Thermal Waste to Monetary Energy",
        "Modular mobile compute provides continuous economic demand at the wellhead, abating methane emissions with zero transmission loss.",
        "Validates thermodynamic co-location principles and energy monetization physics.",
        False
    )
]

def synthesize_signal(post_id, entity_id, raw_text, source_url, timestamp, velocity_hint=7.5, sparkline=None):
    clean_text = raw_text.lower()
    
    matched_category = None
    matched_headline = None
    matched_lens = None
    matched_cross_ref = None
    matched_urgent = False

    for pattern, cat, headline, lens, cross_ref, urgent in TOPIC_SYNTHESIZERS:
        if re.search(pattern, clean_text, re.IGNORECASE):
            matched_category = cat
            matched_headline = headline
            matched_lens = lens
            matched_cross_ref = cross_ref
            matched_urgent = urgent
            break

    if not matched_category:
        if any(k in clean_text for k in ["btc", "satoshi", "halving", "custody", "multisig"]):
            matched_category = "Bitcoin"
            matched_headline = "Cryptographic Consensus Guarantees Unchangeable Monetary Scarcity"
            matched_lens = "Immutable mathematical limits prevent sovereign debasement and preserve long-term purchasing power."
            matched_cross_ref = "Contrast between Austrian sound money principles and discretionary fiat credit expansion."
            matched_urgent = False
        elif any(k in clean_text for k in ["energy", "electricity", "watts", "joules"]):
            matched_category = "Compute, Power & The Grid"
            matched_headline = "Physical Power Constraints Anchor Modern Digital Infrastructure"
            matched_lens = "All computation is fundamentally an irreversible thermodynamic transformation of electrical potential."
            matched_cross_ref = "Landauer's principle and thermodynamic limits of computation."
            matched_urgent = True
        elif any(k in clean_text for k in ["model", "ai", "llm", "neural"]):
            matched_category = "Autonomous Intelligence"
            matched_headline = "Autonomous Edge Models Disrupt Centralized Cloud Monopoly"
            matched_lens = "Local model weights running on user hardware preserve sovereignty against centralized platform censorship."
            matched_cross_ref = "Parallel to open-source software disruption of proprietary computing architectures."
            matched_urgent = False
        else:
            # No regex pattern matched and no keyword heuristic applied.
            # Log a warning so operators can see which content is falling through,
            # then classify explicitly as Uncategorized rather than silently
            # routing to a misleading category.
            print(
                f"  [TOPIC WARN] synthesize_signal: no pattern matched for post_id={post_id!r}. "
                f"Text preview: {raw_text[:80]!r}. "
                f"Add a matching pattern to TOPIC_SYNTHESIZERS or the keyword fallbacks above."
            )
            matched_category = "Uncategorized"
            matched_headline = "Signal Awaiting Classification"
            matched_lens = "This signal did not match any first-principles topic pattern. Manual review recommended."
            matched_cross_ref = "See TOPIC_SYNTHESIZERS in pipeline.py to add a matching regex."
            matched_urgent = False

    spark = sparkline or [10, 15, 22, 35, 52, 75, 105]

    return {
        "id": f"sig_{post_id.replace('post_', '')}",
        "raw_post_id": post_id,
        "entity_id": entity_id,
        "category": matched_category,
        "signal_headline": matched_headline,
        "alden_lens": matched_lens,
        "convergence_lens": matched_lens,
        "cross_reference": matched_cross_ref,
        "velocity_score": velocity_hint,
        "momentum_label": f"+{int(velocity_hint * 40)}% 6h spike" if velocity_hint > 8.0 else f"+{int(velocity_hint * 25)}% 24h gain",
        "sparkline_points": spark,
        "is_urgent_shift": matched_urgent or (velocity_hint >= 8.8),
        "published_at": datetime.now(timezone.utc).isoformat()
    }

def run_pipeline(mock_inputs_path=None):
    print("==================================================")
    print("⚡ ConvergenceTerminal: Ingestion & Synthesis Engine")
    print("   Filter Standard: The Lyn Alden Standard")
    print("==================================================")

    db.init_db()

    config_path = os.path.join(os.path.dirname(SCRIPT_DIR), "config", "entities.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for ent in cfg.get("tracked_entities", []):
                db.upsert_entity(ent)
        print(f"👥 Synced VIP entities into SQLite database.")

    if not mock_inputs_path:
        mock_inputs_path = os.path.join(os.path.dirname(SCRIPT_DIR), "data", "mock_inputs.json")

    with open(mock_inputs_path, "r", encoding="utf-8") as f:
        incoming_posts = json.load(f)

    print(f"📥 Received {len(incoming_posts)} incoming posts to evaluate.")

    passed_count = 0
    quarantined_count = 0

    for item in incoming_posts:
        entity = item.get("entity", {})
        handle = entity.get("handle", "@unknown")
        entity_id = db.get_entity_id_by_handle(handle)
        raw_text = item.get("raw_text", "")
        raw_source_url = item.get("source_url", "#")
        platform = entity.get("platform", "x")
        source_url = db.resolve_source_url(raw_source_url, handle=handle, platform=platform, entity_id=entity_id)
        timestamp = item.get("timestamp", datetime.now(timezone.utc).isoformat())
        velocity_hint = item.get("velocity_hint", 7.5)
        sparkline = item.get("sparkline", None)

        db.upsert_entity({
            "id": entity_id,
            "handle": handle,
            "name": entity.get("name", handle),
            "category": item.get("category", "Macro Plumbing & Balance Sheets"),
            "platform": platform
        })

        post_id, is_new = db.insert_raw_post(entity_id, handle, raw_text, source_url, timestamp)
        
        is_sludge, drop_reason, rule_violated = evaluate_sludge(raw_text)
        if is_sludge:
            db.log_sludge(post_id, handle, raw_text, drop_reason, rule_violated)
            print(f"  🚫 [QUARANTINE] {handle}: \"{raw_text[:35]}...\" -> {drop_reason}")
            quarantined_count += 1
            continue

        signal = synthesize_signal(post_id, entity_id, raw_text, source_url, timestamp, velocity_hint, sparkline)
        db.insert_synthesized_signal(signal)
        print(f"  ✨ [SIGNAL PASSED] [{signal['category'][:20]:<20}] {signal['signal_headline'][:45]}...")
        passed_count += 1

    exported_signals, total_sludge = db.export_public_data(limit=50)

    print("\n--------------------------------------------------")
    print(f"✅ Pipeline Run Completed Successfully:")
    print(f"   - Passed High-Signal Items: {passed_count}")
    print(f"   - Quarantined Sludge Items: {quarantined_count}")
    print(f"   - Total Published to public/data.json: {exported_signals}")
    print(f"   - Cumulative Sludge Quarantined in DB: {total_sludge}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_pipeline()
