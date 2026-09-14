-- ConvergenceTerminal SQLite Schema
-- Designed for $0.00 local storage, deduplication, and public static export

-- Enable FK enforcement. Must be set per connection; this line runs via
-- executescript() in db.init_db() and also via PRAGMA in any raw connection.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    handle TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    platform TEXT DEFAULT 'x',
    avatar_url TEXT,
    feed_url TEXT,
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_posts (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    source_url TEXT,
    raw_text TEXT NOT NULL,
    content_hash TEXT UNIQUE NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(entity_id) REFERENCES entities(id)
);

CREATE TABLE IF NOT EXISTS sludge_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_post_id TEXT,
    entity_handle TEXT,
    raw_text TEXT NOT NULL,
    drop_reason TEXT NOT NULL,
    rule_violated TEXT NOT NULL,
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- raw_post_id is nullable: sludge is often logged before the raw_post write
    -- is committed, or for posts rejected before DB insertion. ON DELETE SET NULL
    -- preserves the quarantine record even if the parent post is purged.
    FOREIGN KEY(raw_post_id) REFERENCES raw_posts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS synthesized_signals (
    id TEXT PRIMARY KEY,
    raw_post_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    category TEXT NOT NULL,
    signal_headline TEXT NOT NULL,
    alden_lens TEXT NOT NULL,
    cross_reference TEXT,
    velocity_score REAL,
    momentum_label TEXT,
    sparkline_points TEXT NOT NULL, -- JSON array of 7 integers
    is_urgent_shift INTEGER DEFAULT 0,
    synthesis_source TEXT DEFAULT 'heuristic',  -- 'heuristic' or 'gemini'
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(raw_post_id) REFERENCES raw_posts(id),
    FOREIGN KEY(entity_id) REFERENCES entities(id)
);

CREATE INDEX IF NOT EXISTS idx_signals_velocity ON synthesized_signals(velocity_score DESC);
CREATE INDEX IF NOT EXISTS idx_signals_published ON synthesized_signals(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_hash ON raw_posts(content_hash);
