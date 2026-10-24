from __future__ import annotations

import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bt_knowledge import KnowledgeError, benchmark, export, ingest, query, stats


PACKAGE = Path(__file__).resolve().parents[1]
COMMIT_A = "a" * 40
COMMIT_B = "b" * 40


def delta(*, project="shop", repository="web", commit=COMMIT_A, contributor="explorer:one", observations=None,
          contradictions=None, stale=None):
    return {"schema": "knowledge-delta/1", "project": project, "repository": repository, "observed_commit": commit,
            "contributor": contributor, "observations": observations if observations is not None else [{"subject": "subplan:checkout",
            "relation": "CONSUMES", "object": "contract:auth", "status": "observed",
            "evidence": ["src/checkout.py:1"]}], "contradictions": contradictions or [], "stale": stale or []}


def _concurrent_ingest(db: str, item: dict) -> None:
    ingest(db, item)


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "knowledge.db"

    def tearDown(self):
        self.temp.cleanup()

    def test_duplicate_relation_and_same_evidence_from_two_explorers(self):
        first = ingest(self.db, delta())
        second = ingest(self.db, delta(contributor="explorer:two"))
        self.assertEqual(first["relations_added"], 1)
        self.assertEqual(second["evidence_added"], 0)
        result = query(self.db, "shop")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["evidence"][0]["contributors"], ["explorer:one", "explorer:two"])
        self.assertEqual(stats(self.db, "shop")["evidence"], 1)

    def test_independent_evidence_and_commit_are_preserved(self):
        ingest(self.db, delta())
        ingest(self.db, delta(commit=COMMIT_B, contributor="explorer:two",
                              observations=[{"subject": "subplan:checkout", "relation": "CONSUMES",
                                             "object": "contract:auth", "status": "inferred",
                                             "evidence": ["src/checkout-other.py:2"]}]))
        rows = query(self.db, "shop", commit=COMMIT_B)
        self.assertEqual(len(rows), 1)
        self.assertEqual({item["validity"] for item in rows[0]["evidence"]}, {"current", "historical"})
        self.assertEqual(len(rows[0]["evidence"]), 2)

    def test_new_consumer_adds_a_relation_and_fingerprints_are_project_scoped(self):
        ingest(self.db, delta())
        consumer = delta(observations=[{"subject": "subplan:profile", "relation": "CONSUMES",
            "object": "contract:auth", "status": "observed", "evidence": ["src/profile.py:4"]}])
        ingest(self.db, consumer)
        ingest(self.db, delta(project="other-project"))
        self.assertEqual(stats(self.db, "shop")["relations"], 2)
        self.assertEqual(stats(self.db, "other-project")["evidence"], 1)

    def test_exact_retry_is_idempotent_and_restart_persists(self):
        ingest(self.db, delta())
        before = stats(self.db, "shop")
        result = ingest(self.db, delta())
        self.assertEqual(result["added"], 0)
        self.assertEqual(stats(self.db, "shop"), before)
        self.assertEqual(len(query(self.db, "shop")), 1)

    def test_contradiction_keeps_both_relations_and_disputes_them(self):
        ingest(self.db, delta())
        item = delta(contradictions=[{"subject": "subplan:checkout", "relation": "CONSUMES",
            "object": "contract:other", "evidence": ["src/other.py:1"], "reason": "different contract"}])
        ingest(self.db, item)
        rows = query(self.db, "shop", commit=COMMIT_A)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["disputed"] and row["status"] == "disputed" for row in rows))
        self.assertTrue(all(row["validity"] == "current" for row in rows))
        self.assertEqual(sum(len(row["evidence"]) for row in rows), 2)
        self.assertEqual(stats(self.db, "shop")["conflicts"], 1)

    def test_explicit_contradiction_without_known_peer_is_retained_as_disputed(self):
        item = delta(observations=[], contradictions=[{"subject": "subplan:checkout", "relation": "CONSUMES",
            "object": "contract:auth", "evidence": ["src/checkout.py:1"], "reason": "explicit dispute"}])
        ingest(self.db, item)
        self.assertTrue(query(self.db, "shop")[0]["disputed"])

    def test_git_verification_and_revision_validity(self):
        repo = Path(self.temp.name) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
        (repo / "src").mkdir()
        (repo / "src" / "checkout.py").write_text("first\nsecond\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "first"], check=True)
        first = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        (repo / "README.md").write_text("unrelated\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "unrelated"], check=True)
        second = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        item = delta(commit=first, observations=[{"subject": "module:checkout", "relation": "DEFINES",
            "object": "symbol:session", "status": "observed", "evidence": ["src/checkout.py:2"]}])
        ingest(self.db, item, repo)
        rows = query(self.db, "shop", commit=second, repo_path=repo)
        self.assertEqual(rows[0]["evidence"][0]["verification"], "verified")
        self.assertEqual(rows[0]["validity"], f"unchanged_since:{first}")
        invalid = delta(commit=first, observations=[{"subject": "module:checkout", "relation": "DEFINES",
            "object": "symbol:missing", "status": "observed", "evidence": ["src/checkout.py:20"]}])
        ingest(self.db, invalid, repo)
        result = query(self.db, "shop", status="unverified")
        self.assertEqual(len(result), 1)

    def test_missing_repo_is_unverified_and_zero_deltas_are_valid(self):
        empty = delta(observations=[])
        self.assertEqual(ingest(self.db, empty)["added"], 0)
        ingest(self.db, delta())
        self.assertEqual(query(self.db, "shop")[0]["evidence"][0]["verification"], "unverified")

    def test_secret_values_and_sensitive_paths_reject_without_echo(self):
        secret = delta(observations=[{"subject": "module:a", "relation": "CONSUMES", "object": "contract:b",
                                     "status": "observed", "evidence": ["src/a.py"], "note": "ghp_" + "A" * 36}])
        with self.assertRaises(KnowledgeError) as caught:
            ingest(self.db, secret)
        self.assertNotIn("ghp_", str(caught.exception))
        self.assertEqual(caught.exception.code, "SECRET_SHAPE")
        for path in (".env", "config/.env.production", "keys/server.pem", "secrets.json", "id_rsa.pub"):
            with self.subTest(path=path), self.assertRaises(KnowledgeError):
                ingest(self.db, delta(observations=[{"subject": "module:a", "relation": "CONSUMES",
                    "object": "contract:b", "status": "observed", "evidence": [path]}]))

    def test_closed_vocabularies_and_safe_paths(self):
        for mutation, code in (({"relation": "UNKNOWN"}, "INVALID_RELATION"),
                               ({"status": "disputed"}, "INVALID_STATUS"),
                               ({"subject": "bad id"}, "INVALID_ENTITY")):
            item = delta()
            item["observations"] = [dict(item["observations"][0], **mutation)]
            with self.subTest(code=code), self.assertRaises(KnowledgeError) as caught:
                ingest(self.db, item)
            self.assertEqual(caught.exception.code, code)

    def test_filters_and_labels_inferred_unknown_unverified_and_stale(self):
        obs = [{"subject": "module:checkout", "relation": "CONSUMES", "object": "contract:auth",
                "status": "inferred", "evidence": ["src/checkout/session.py:3"]},
               {"subject": "module:profile", "relation": "CONSUMES", "object": "contract:profile",
                "status": "unknown", "evidence": ["src/profile.py"]}]
        ingest(self.db, delta(observations=obs))
        marked = delta(observations=[], stale=[{"subject": "module:checkout", "relation": "CONSUMES", "object": "contract:auth",
                               "reason": "superseded"}])
        ingest(self.db, marked)
        self.assertEqual(len(query(self.db, "shop", area="src/checkout")), 1)
        self.assertEqual(len(query(self.db, "shop", area="module:profile")), 1)
        self.assertEqual(len(query(self.db, "shop", status="inferred")), 1)
        self.assertEqual(len(query(self.db, "shop", status="unknown")), 1)
        self.assertEqual(len(query(self.db, "shop", status="unverified")), 2)
        self.assertEqual(len(query(self.db, "shop", status="stale")), 1)

    def test_parallel_overlapping_ingests_match_sequential_state(self):
        items = [delta(contributor=f"explorer:{index}") for index in range(6)]
        with multiprocessing.get_context("fork").Pool(6) as pool:
            pool.starmap(_concurrent_ingest, [(str(self.db), item) for item in items])
        result = query(self.db, "shop")
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]["evidence"][0]["contributors"]), 6)
        self.assertEqual(stats(self.db, "shop")["relations"], 1)

    def test_exports_and_benchmark_are_compact_without_codegraph(self):
        ingest(self.db, delta())
        for fmt in ("md", "mermaid", "json"):
            self.assertTrue(export(self.db, "shop", fmt))
        self.assertIn("unverified", export(self.db, "shop", "md"))
        measured = benchmark(Path(self.temp.name) / "benchmark.db")
        print("knowledge benchmark:", json.dumps(measured, sort_keys=True))
        self.assertEqual(measured["relations"], measured["correct_relations"])
        self.assertLess(measured["query_json_bytes"], measured["raw_delta_bytes"])
        self.assertGreater(measured["duplicates_avoided"], 0)
        self.assertGreater(measured["stale_labelled"], 0)
        self.assertGreaterEqual(measured["elapsed_seconds"], 0)

    def test_cli_ingest_query_runs_from_unrelated_working_directory(self):
        package_root = PACKAGE.parent
        env = {**os.environ, "PYTHONPATH": str(package_root)}
        payload = json.dumps(delta())
        result = subprocess.run([sys.executable, "-m", "bt_knowledge", "--db", str(self.db), "ingest", "-", "--json"],
                                input=payload, text=True, capture_output=True, cwd=self.temp.name, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"added": 1', result.stdout)


if __name__ == "__main__":
    unittest.main()
