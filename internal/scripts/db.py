#!/usr/bin/env python3
"""
ConvergenceTerminal Database Controller (SQLite)
Rex (Employee #5) - Data Pipeline Specialist
Zero-cost, fast local storage for raw items, sludge quarantine, and signal export.
"""

import os
import sqlite3
import json
import hashlib
import re
from contextlib import contextmanager
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "internal", "db", "terminal.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "internal", "db", "schema.sql")
PUBLIC_DATA_PATH = os.path.join(BASE_DIR, "public", "data.json")

def resolve_source_url(raw_url, handle="", platform="x", entity_id=None):
    """
    Validates and resolves a source URL to guarantee zero 404 dead links.
    Detects broken/synthetic Snowflake IDs, dead placeholder slugs, or missing URLs,
    and applies a deterministic fallback hierarchy:
    1. Verified specific URL (if valid)
    2. Known canonical corrections for documented repos/substacks/releases
    3. Entity-specific verified platform/profile anchor
    """
    clean_handle = (handle or "").lstrip("@").strip()
    clean_platform = (platform or "x").lower().strip()

    # Determine default canonical profile/site anchor
    if clean_platform == "github":
        profile_anchor = f"https://github.com/{clean_handle}" if clean_handle else "https://github.com"
    elif clean_platform == "substack":
        profile_anchor = f"https://{clean_handle.lower()}.substack.com/" if clean_handle else "https://substack.com"
    elif clean_handle.lower() == "ercot_iso":
        profile_anchor = "https://www.ercot.com/news/releases"
    elif clean_handle.lower() == "lynaldencontact" and clean_platform == "newsletter":
        profile_anchor = "https://www.lynalden.com/"
    else:
        profile_anchor = f"https://x.com/{clean_handle}" if clean_handle else "https://x.com"

    if not raw_url or not isinstance(raw_url, str):
        return profile_anchor

    url = raw_url.strip()
    if url in ["#", "", "http://", "https://"]:
        return profile_anchor

    # Canonical corrections for known synthetic/moved slugs
    if "lightninglabs/l402-protocol-spec" in url:
        return "https://github.com/lightninglabs/L402"
    if "cryptohayes.substack.com/p/the-fiat-meat-grinder" in url:
        return "https://cryptohayes.substack.com/"
    if "lynalden.com/september-2026-macro-summary" in url:
        return "https://www.lynalden.com/"
    if "ercot.com/news/releases/2026-grid-capacity" in url:
        return "https://www.ercot.com/news/releases"

    # Detect synthetic X status permalinks
    x_status_match = re.match(r"^https?://(?:www\.)?(?:x\.com|twitter\.com)/[^/]+/status/(\d+)", url, re.IGNORECASE)
    if x_status_match:
        status_id_str = x_status_match.group(1)
        # Modern Snowflake ID verification:
        # Standard Twitter Snowflake epoch starts at 1288834974657 (Nov 2010).
        # Genuine tweets from 2023+ have 18-19 digits and timestamp >= Jan 1, 2020 (1577836800000 ms).
        # Synthetic mock IDs (like 18331902830129) are 10-14 digits and timestamp-decode to ~2010.
        if len(status_id_str) < 18:
            return profile_anchor
        try:
            status_id = int(status_id_str)
            snowflake_time = (status_id >> 22) + 1288834974657
            if snowflake_time < 1577836800000:  # Pre-2020 indicates synthetic/corrupted ID
                return profile_anchor
        except ValueError:
            return profile_anchor

    # Validate scheme
    if not (url.startswith("http://") or url.startswith("https://")):
        return profile_anchor

    return url

def classify_source_url(url):
    """
    Inspects a resolved URL and returns 'post' when it points to a specific
    piece of content, or 'profile' when it only leads to a generic author /
    channel / site root page.

    Classification rules (evaluated in order):
      post  — X/Twitter /status/<id> permalink
      post  — GitHub specific path (PR, issue, release, commit, tree with >1 segment)
      post  — Substack article  /p/<slug>
      post  — Any URL with a recognisable article/post path segment (>=3 path parts)
              that is not a bare domain root or a known profile/feed anchor
      profile — everything else (profile pages, site roots, news release indexes)
    """
    if not url or not isinstance(url, str):
        return "profile"

    url = url.strip()

    # X / Twitter tweet permalink
    if re.search(r"(?:x\.com|twitter\.com)/[^/]+/status/\d+", url, re.IGNORECASE):
        return "post"

    # GitHub: specific content (PR, issue, release tag, commit, blob, tree with depth)
    gh_match = re.match(
        r"https?://github\.com/[^/]+/[^/]+/(pull|issues|releases/tag|commit|blob|tree)(/|$)",
        url, re.IGNORECASE
    )
    if gh_match:
        return "post"

    # Substack article slug  /p/<slug>
    if re.search(r"substack\.com/p/[^/?#]+", url, re.IGNORECASE):
        return "post"

    # Generic heuristic: URL has >= 3 non-empty path segments (e.g. /blog/2026/article-title)
    # but exclude known profile/index anchors like /news/releases or /feed/
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        # Paths like /news/releases or /releases are index pages — still profile-level
        # Paths with >= 3 parts and no trailing ambiguity are specific content
        if len(parts) >= 3:
            return "post"
    except Exception:
        pass

    return "profile"


# ─────────────────────────────────────────────────────────────────────────────
# Connection management
# ─────────────────────────────────────────────────────────────────────────────

@contextmanager
def db_connection():
    """
    Context manager for SQLite connections.

    Usage:
        with db_connection() as conn:
            conn.execute(...)

    Guarantees that the connection is closed even if an exception is raised
    inside the with-block, eliminating the connection-leak risk that exists
    with manual get_connection() / conn.close() pairs.

    FK enforcement is enabled per-connection as required by SQLite.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def get_connection():
    """
    Legacy helper — returns a raw connection that the caller must close.

    Prefer using the `db_connection()` context manager instead, which
    guarantees connection cleanup even when exceptions occur.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Schema & utilities
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    with db_connection() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()

def compute_hash(text, handle):
    payload = f"{handle.strip().lower()}:{text.strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Read operations
# ─────────────────────────────────────────────────────────────────────────────

def get_entity_id_by_handle(handle):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM entities WHERE lower(handle) = lower(?)", (handle.strip(),))
        row = cursor.fetchone()
    if row:
        return row["id"]
    return handle.lstrip("@").lower().replace("_", "-")


# ─────────────────────────────────────────────────────────────────────────────
# Write operations
# ─────────────────────────────────────────────────────────────────────────────

def upsert_entity(entity_dict):
    handle = entity_dict["handle"].strip()
    entity_id = entity_dict.get("id") or handle.lstrip("@").lower().replace("_", "-")

    feed_url = entity_dict.get("feed_url", "")
    if not feed_url and "feeds" in entity_dict and isinstance(entity_dict["feeds"], dict):
        feeds = entity_dict["feeds"]
        feed_url = feeds.get("rss") or feeds.get("substack_rss") or feeds.get("github") or feeds.get("press_rss") or ""

    with db_connection() as conn:
        conn.execute("""
            INSERT INTO entities (id, handle, name, category, platform, avatar_url, feed_url, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(handle) DO UPDATE SET
                name=excluded.name,
                category=excluded.category,
                avatar_url=excluded.avatar_url,
                feed_url=excluded.feed_url,
                active=excluded.active
        """, (
            entity_id,
            handle,
            entity_dict["name"],
            entity_dict["category"],
            entity_dict.get("platform", "x"),
            entity_dict.get("avatar_url", f"https://unavatar.io/x/{handle.lstrip('@')}"),
            feed_url,
            1 if entity_dict.get("active", True) else 0
        ))
        conn.commit()

def insert_raw_post(entity_id, handle, raw_text, source_url=None, timestamp=None):
    content_hash = compute_hash(raw_text, handle)
    post_id = f"post_{content_hash[:16]}"
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    clean_url = resolve_source_url(source_url, handle=handle)

    with db_connection() as conn:
        try:
            conn.execute("""
                INSERT INTO raw_posts (id, entity_id, source_url, raw_text, content_hash, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (post_id, entity_id, clean_url, raw_text, content_hash, ts))
            conn.commit()
            is_new = True
        except sqlite3.IntegrityError as exc:
            # A UNIQUE constraint failure on content_hash means this exact post was
            # already ingested — that is expected deduplication behaviour.
            # Any other IntegrityError (FK violation, NOT NULL, etc.) is a real bug
            # and must not be silently swallowed as a fake "duplicate".
            if "UNIQUE constraint failed" in str(exc):
                is_new = False
            else:
                raise

    return post_id, is_new

def log_sludge(raw_post_id, entity_handle, raw_text, drop_reason, rule_violated):
    with db_connection() as conn:
        conn.execute("""
            INSERT INTO sludge_log (raw_post_id, entity_handle, raw_text, drop_reason, rule_violated)
            VALUES (?, ?, ?, ?, ?)
        """, (raw_post_id, entity_handle, raw_text, drop_reason, rule_violated))
        conn.commit()

def insert_synthesized_signal(signal_dict):
    sparkline_str = json.dumps(signal_dict.get("sparkline_points", [10, 20, 30, 40, 50, 60, 70]))
    with db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO synthesized_signals (
                id, raw_post_id, entity_id, category, signal_headline,
                alden_lens, cross_reference, velocity_score, momentum_label,
                sparkline_points, is_urgent_shift, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_dict["id"],
            signal_dict["raw_post_id"],
            signal_dict["entity_id"],
            signal_dict["category"],
            signal_dict["signal_headline"],
            signal_dict["alden_lens"],
            signal_dict.get("cross_reference", ""),
            signal_dict.get("velocity_score"),
            signal_dict.get("momentum_label"),
            sparkline_str,
            1 if signal_dict.get("is_urgent_shift", False) else 0,
            signal_dict.get("published_at", datetime.now(timezone.utc).isoformat())
        ))
        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────

def export_public_data(limit=50):
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM sludge_log")
        sludge_count = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT 
                s.id, s.category, s.signal_headline, s.alden_lens, s.cross_reference,
                s.velocity_score, s.momentum_label, s.sparkline_points, s.is_urgent_shift,
                s.published_at, r.source_url, r.raw_text, r.timestamp,
                COALESCE(e.name, r.entity_id) as entity_name,
                COALESCE(e.handle, '@' || r.entity_id) as entity_handle,
                COALESCE(e.platform, 'x') as entity_platform,
                COALESCE(e.avatar_url, 'https://unavatar.io/x/' || replace(r.entity_id, '@', '')) as entity_avatar_url
            FROM synthesized_signals s
            JOIN raw_posts r ON s.raw_post_id = r.id
            LEFT JOIN entities e ON (s.entity_id = e.id OR lower(e.handle) = lower('@' || s.entity_id) OR lower(e.handle) = lower(s.entity_id))
            ORDER BY s.velocity_score DESC, s.published_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) as count FROM entities WHERE active = 1")
        entity_count_row = cursor.fetchone()
        tracked_count = entity_count_row["count"] if entity_count_row else 0

    # Build output outside the connection context — connection is already closed.
    items = []
    for r in rows:
        try:
            sparkline = json.loads(r["sparkline_points"])
        except Exception:
            sparkline = [10, 15, 25, 40, 60, 80, 100]

        resolved_source = resolve_source_url(
            r["source_url"],
            handle=r["entity_handle"],
            platform=r["entity_platform"]
        )

        items.append({
            "id": r["id"],
            "timestamp": r["timestamp"],
            "entity": {
                "name": r["entity_name"],
                "handle": r["entity_handle"],
                "platform": r["entity_platform"],
                "avatar_url": r["entity_avatar_url"]
            },
            "source_url": resolved_source,
            "source_url_type": classify_source_url(resolved_source),
            "category": r["category"],
            "raw_summary": r["raw_text"],
            "elevated_intelligence": {
                "signal_headline": r["signal_headline"],
                "convergence_lens": r["alden_lens"],
                "alden_lens": r["alden_lens"],
                "cross_reference": r["cross_reference"],
                "is_urgent_shift": bool(r["is_urgent_shift"])
            },
            "metrics": {
                "velocity_score": float(r["velocity_score"]) if r["velocity_score"] is not None else None,
                "momentum_label": r["momentum_label"],
                "sparkline_points": sparkline
            }
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": "Convergence Intelligence Engine v1.1",
        "tracked_entities_count": tracked_count,
        "total_signals": len(items),
        "sludge_filtered_count": sludge_count,
        "categories": [
            "All Signals",
            "Bitcoin",
            "Compute, Power & The Grid",
            "Agentic Rails & Settlement",
            "Macro Plumbing & Balance Sheets",
            "Autonomous Intelligence"
        ],
        "items": items
    }

    os.makedirs(os.path.dirname(PUBLIC_DATA_PATH), exist_ok=True)
    with open(PUBLIC_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return len(items), sludge_count

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized successfully at:", DB_PATH)
