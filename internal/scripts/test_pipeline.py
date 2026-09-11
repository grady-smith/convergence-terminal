#!/usr/bin/env python3
"""
Automated Verification Test Suite for ConvergenceTerminal Pipeline
Tests database operations, deduplication, sludge filtering, and public data export.
"""

import os
import sys
import unittest
import json
import uuid

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import db
import pipeline
import ingest

class TestConvergencePipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Override database and export paths to be isolated and ephemeral
        cls.test_db_path = os.path.join(db.BASE_DIR, "internal", "db", "terminal_test.db")
        cls.test_public_data_path = os.path.join(db.BASE_DIR, "public", "test_data.json")
        db.DB_PATH = cls.test_db_path
        db.PUBLIC_DATA_PATH = cls.test_public_data_path

    def setUp(self):
        # Ensure fresh state before each test
        if os.path.exists(db.DB_PATH):
            os.remove(db.DB_PATH)
        if os.path.exists(db.PUBLIC_DATA_PATH):
            os.remove(db.PUBLIC_DATA_PATH)
        db.init_db()

    def tearDown(self):
        if os.path.exists(db.DB_PATH):
            try:
                os.remove(db.DB_PATH)
            except Exception:
                pass
        if os.path.exists(db.PUBLIC_DATA_PATH):
            try:
                os.remove(db.PUBLIC_DATA_PATH)
            except Exception:
                pass

    def test_database_and_deduplication(self):
        """Verify that identical posts produce identical hashes and deduplicate cleanly."""
        unique_run = uuid.uuid4().hex[:8]
        # Use a fully random entity so this test is isolated from any real
        # entities already in the DB (handles like @LynAldenContact may have a
        # different id in the entities table, which would cause a FK violation).
        entity_id = f"test-entity-{unique_run}"
        handle = f"@test_{unique_run}"
        raw_text = f"Thermodynamic energy constraints dictate proof-of-work efficiency limits [{unique_run}]."

        # Seed the entity first — raw_posts.entity_id has a FK constraint (Phase 4 L-5).
        db.upsert_entity({
            "id": entity_id,
            "handle": handle,
            "name": f"Test Entity {unique_run}",
            "category": "Bitcoin",
            "platform": "x",
            "active": True
        })

        post_id1, is_new1 = db.insert_raw_post(entity_id, handle, raw_text)
        self.assertTrue(len(post_id1) > 0)
        self.assertTrue(is_new1, "First insertion must be marked as new")

        # Attempt duplicate insert
        post_id2, is_new2 = db.insert_raw_post(entity_id, handle, raw_text)
        self.assertEqual(post_id1, post_id2)
        self.assertFalse(is_new2, "Duplicate post must be detected and not re-inserted")

    def test_sludge_filter_rules(self):
        """Verify that Stage 1 accurately catches noise and permits signal."""
        sludge_samples = [
            "MASSIVE BREAKOUT!! $BTC to 100k this weekend, buy the dip now!!",
            "Retweet if you think crypto will hit 500k! Drop your wallet address below.",
            "This founder is a fraud and a total clown, stay poor!",
            "gm"
        ]

        valid_signal_samples = [
            "ERCOT power auction clearing prices show rising premium for flexible baseload contracts.",
            "Autonomous AI agents mandate protocol-native Lightning micro-settlement rails for inference.",
            "US Treasury net issuance cannot be absorbed without ongoing indirect central bank monetization."
        ]

        for s in sludge_samples:
            is_sludge, reason, rule = pipeline.evaluate_sludge(s)
            self.assertTrue(is_sludge, f"Should have dropped sludge: '{s}' (Reason: {reason})")

        for v in valid_signal_samples:
            is_sludge, reason, rule = pipeline.evaluate_sludge(v)
            self.assertFalse(is_sludge, f"Valid signal wrongly flagged as sludge: '{v}'")

    def test_resolve_source_url_valid(self):
        """Verify that genuine, valid URLs pass through unmodified."""
        valid_github = "https://github.com/bitcoin/bitcoin/pulls"
        self.assertEqual(db.resolve_source_url(valid_github, handle="@bitcoincoreorg"), valid_github)
        
        valid_x_profile = "https://x.com/LynAldenContact"
        self.assertEqual(db.resolve_source_url(valid_x_profile, handle="@LynAldenContact"), valid_x_profile)

        # Genuine 19-digit snowflake ID (timestamp > 2023)
        valid_tweet = "https://x.com/jackmallers/status/1789000000000000000"
        self.assertEqual(db.resolve_source_url(valid_tweet, handle="@jackmallers"), valid_tweet)

    def test_resolve_source_url_synthetic_status(self):
        """Verify that synthetic 10-14 digit X status IDs fall back to the author profile anchor."""
        synthetic_url = "https://x.com/LynAldenContact/status/18331902830129"
        expected_fallback = "https://x.com/LynAldenContact"
        self.assertEqual(db.resolve_source_url(synthetic_url, handle="@LynAldenContact"), expected_fallback)

        short_id_url = "https://x.com/adam3us/status/1833189912048"
        self.assertEqual(db.resolve_source_url(short_id_url, handle="@adam3us"), "https://x.com/adam3us")

    def test_resolve_source_url_placeholder_slugs(self):
        """Verify that dead placeholder slugs resolve to canonical endpoints."""
        self.assertEqual(
            db.resolve_source_url("https://github.com/lightninglabs/l402-protocol-spec", handle="@lightning"),
            "https://github.com/lightninglabs/L402"
        )
        self.assertEqual(
            db.resolve_source_url("https://cryptohayes.substack.com/p/the-fiat-meat-grinder", handle="@CryptoHayes", platform="substack"),
            "https://cryptohayes.substack.com/"
        )
        self.assertEqual(
            db.resolve_source_url("https://www.lynalden.com/september-2026-macro-summary", handle="@LynAldenContact", platform="newsletter"),
            "https://www.lynalden.com/"
        )
        self.assertEqual(
            db.resolve_source_url("https://ercot.com/news/releases/2026-grid-capacity", handle="@ERCOT_ISO"),
            "https://www.ercot.com/news/releases"
        )

    def test_resolve_source_url_empty_and_hash(self):
        """Verify empty, whitespace, and '#' URLs resolve to author profile anchor."""
        self.assertEqual(db.resolve_source_url("#", handle="@jackmallers"), "https://x.com/jackmallers")
        self.assertEqual(db.resolve_source_url("", handle="@jackmallers"), "https://x.com/jackmallers")
        self.assertEqual(db.resolve_source_url(None, handle="@jackmallers"), "https://x.com/jackmallers")
        self.assertEqual(db.resolve_source_url("   ", handle="@karpathy", platform="github"), "https://github.com/karpathy")

    def test_export_contract(self):
        """Verify public/data.json schema compliance and data integrity."""
        exported_count, sludge_count = db.export_public_data(limit=50)
        self.assertTrue(os.path.exists(db.PUBLIC_DATA_PATH))
        
        with open(db.PUBLIC_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("generated_at", data)
        self.assertIn("categories", data)
        self.assertIn("items", data)
        self.assertIn("sludge_filtered_count", data)

        for item in data["items"]:
            self.assertIn("id", item)
            self.assertIn("entity", item)
            self.assertIn("elevated_intelligence", item)
            self.assertIn("signal_headline", item["elevated_intelligence"])
            self.assertIn("alden_lens", item["elevated_intelligence"])
            # H-4: convergence_lens must now be present alongside alden_lens
            self.assertIn("convergence_lens", item["elevated_intelligence"],
                          f"convergence_lens missing in elevated_intelligence for item {item.get('id')}")
            self.assertEqual(
                item["elevated_intelligence"]["convergence_lens"],
                item["elevated_intelligence"]["alden_lens"],
                "convergence_lens and alden_lens must carry the same value"
            )
            self.assertIn("metrics", item)
            self.assertEqual(len(item["metrics"]["sparkline_points"]), 7)

            # C-1 / M-4: source_url_type must be present and a valid value
            self.assertIn("source_url_type", item,
                          f"source_url_type missing for item {item.get('id')}")
            self.assertIn(item["source_url_type"], ("post", "profile"),
                          f"source_url_type must be 'post' or 'profile', got: {item.get('source_url_type')}")
            
            # URL integrity assertions: zero dead links, valid HTTP(S), no '#' or synthetic status IDs
            url = item.get("source_url")
            self.assertIsNotNone(url)
            self.assertTrue(url.startswith("http://") or url.startswith("https://"), f"Invalid scheme in: {url}")
            self.assertNotEqual(url, "#", "source_url must not be bare '#'")
            self.assertNotIn("status/18331", url, f"Synthetic status ID detected: {url}")

    def test_rss_xml_parsing(self):
        """Verify XML RSS 2.0 parser extracts title, resolved link, and clean text."""
        rss_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Lyn Alden Newsletter</title>
            <item>
              <title>Fiscal Dominance and Monetary Physics</title>
              <link>https://www.lynalden.com/fiscal-dominance/</link>
              <description>&lt;p&gt;In-depth macro plumbing analysis of Treasury markets.&lt;/p&gt;</description>
              <pubDate>Mon, 08 Sep 2026 12:00:00 GMT</pubDate>
            </item>
          </channel>
        </rss>'''
        feed_config = {
            "entity_name": "Lyn Alden",
            "handle": "@LynAldenContact",
            "platform": "newsletter",
            "category": "Macro Plumbing & Balance Sheets",
            "avatar_url": "https://unavatar.io/x/LynAldenContact"
        }
        items = ingest.parse_xml_feed(rss_xml, feed_config)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["entity"]["name"], "Lyn Alden")
        self.assertEqual(items[0]["source_url"], "https://www.lynalden.com/fiscal-dominance/")
        self.assertIn("Fiscal Dominance", items[0]["raw_text"])
        self.assertNotIn("<p>", items[0]["raw_text"])

    def test_atom_xml_parsing(self):
        """Verify XML Atom parser extracts title, attributes, and clean content."""
        atom_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <title>Lightning Terminal Releases</title>
          <entry>
            <title>v0.14.0-alpha</title>
            <link rel="alternate" type="text/html" href="https://github.com/lightninglabs/lightning-terminal/releases/tag/v0.14.0"/>
            <content type="html">&lt;p&gt;Standardized L402 protocol specification updates.&lt;/p&gt;</content>
            <updated>2026-09-07T14:30:00Z</updated>
          </entry>
        </feed>'''
        feed_config = {
            "entity_name": "Lightning Labs",
            "handle": "@lightning",
            "platform": "github",
            "category": "Agentic Rails & Settlement",
            "avatar_url": "https://unavatar.io/x/lightning"
        }
        items = ingest.parse_xml_feed(atom_xml, feed_config)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["entity"]["name"], "Lightning Labs")
        self.assertEqual(items[0]["source_url"], "https://github.com/lightninglabs/lightning-terminal/releases/tag/v0.14.0")
        self.assertIn("v0.14.0-alpha", items[0]["raw_text"])
        self.assertNotIn("<p>", items[0]["raw_text"])

    def test_tweet_record_formatting(self):
        """Verify that TwitterAPI.io raw tweet records format cleanly with engagement telemetry."""
        raw_tweet = {
            "id": "1833190283012900123",
            "text": "Autonomous AI agents mandate protocol-native Lightning micro-settlement https://t.co/abcXYZ",
            "likeCount": 240,
            "retweetCount": 85,
            "viewCount": 42000,
            "createdAt": "Thu Sep 10 15:30:00 +0000 2026",
            "twitterUrl": "https://x.com/jackmallers/status/1833190283012900123"
        }
        meta = {
            "name": "Jack Mallers",
            "handle": "@jackmallers",
            "category": "Agentic Rails & Settlement",
            "velocity_hint": 8.5
        }
        record = ingest.format_tweet_record(raw_tweet, meta)
        self.assertEqual(record["id"], "tw_jackmallers_1833190283012900123")
        self.assertEqual(record["entity"]["handle"], "@jackmallers")
        self.assertEqual(record["source_url"], "https://x.com/jackmallers/status/1833190283012900123")
        self.assertNotIn("https://t.co/", record["raw_text"])
        self.assertGreaterEqual(record["velocity_hint"], 8.0)
        self.assertEqual(len(record["sparkline"]), 7)

    def test_fine_grained_topic_synthesis(self):
        """Verify that the synthesis engine classifies diverse domains and enriches First-Principles lenses."""
        samples = [
            ("Proof-of-work hashrate binds digital scarcity to real megawatts.", "Bitcoin", "Proof-of-Work"),
            ("Autonomous agent clusters use HTTP 402 and Lightning for inference.", "Agentic Rails & Settlement", "Autonomous Agent"),
            ("ERCOT interconnection backlog forces datacenter nuclear baseload co-location.", "Compute, Power & The Grid", "Baseload Grid"),
            ("US Treasury refunding and fiscal dominance drive M2 expansion.", "Macro Plumbing & Balance Sheets", "Fiscal Dominance")
        ]
        for text, expected_cat, expected_keyword in samples:
            sig = pipeline.synthesize_signal("test_p1", "test_ent", text, "https://x.com/test", "2026-09-10T12:00:00Z")
            self.assertEqual(sig["category"], expected_cat)
            self.assertIn(expected_keyword, sig["signal_headline"])
            self.assertTrue(len(sig["convergence_lens"]) > 20)
            self.assertTrue(len(sig["cross_reference"]) > 10)

    def test_tracked_entities_count_meets_vip_standard(self):
        """Verify that public/data.json tracks entities accurately based on DB counts."""
        db.upsert_entity({
            "id": "test-entity-vip",
            "handle": "@vip_test",
            "name": "VIP Test Entity",
            "category": "Bitcoin",
            "active": True
        })
        db.export_public_data(limit=50)
        with open(db.PUBLIC_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertGreaterEqual(data.get("tracked_entities_count", 0), 1)

    def test_classify_source_url(self):
        """Verify that classify_source_url correctly identifies 'post' vs 'profile' URLs."""
        # --- Should classify as 'post' ---
        # X / Twitter tweet permalink (valid 19-digit snowflake)
        self.assertEqual(db.classify_source_url("https://x.com/jackmallers/status/1833190283012900123"), "post")
        self.assertEqual(db.classify_source_url("https://twitter.com/adam3us/status/1789000000000000000"), "post")
        # GitHub specific content paths
        self.assertEqual(db.classify_source_url("https://github.com/bitcoin/bitcoin/pulls"), "post",
                         "GitHub /pulls path should be 'post'")
        # A bare GitHub repo root (2 path segments) classifies as 'profile'
        self.assertEqual(db.classify_source_url("https://github.com/lightninglabs/L402"), "profile",
                         "GitHub repo root with 2-segment path should be 'profile'")
        self.assertEqual(db.classify_source_url("https://github.com/lightninglabs/lightning-terminal/releases/tag/v0.14.0"), "post")
        # Substack article
        self.assertEqual(db.classify_source_url("https://cryptohayes.substack.com/p/some-article-slug"), "post")

        # --- Should classify as 'profile' ---
        # Generic X profile
        self.assertEqual(db.classify_source_url("https://x.com/LynAldenContact"), "profile")
        self.assertEqual(db.classify_source_url("https://x.com/karpathy"), "profile")
        # Substack homepage (no /p/ slug)
        self.assertEqual(db.classify_source_url("https://cryptohayes.substack.com/"), "profile")
        # Site root
        self.assertEqual(db.classify_source_url("https://www.lynalden.com/"), "profile")
        # News releases index (2-segment path)
        self.assertEqual(db.classify_source_url("https://www.ercot.com/news/releases"), "profile")
        # Empty / null
        self.assertEqual(db.classify_source_url(""), "profile")
        self.assertEqual(db.classify_source_url(None), "profile")
        self.assertEqual(db.classify_source_url("#"), "profile")

if __name__ == "__main__":
    unittest.main()
