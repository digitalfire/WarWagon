import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from benchmarks.triage.queue_score import score_queue
from benchmarks.triage.reference import run_guarded_candidate
from benchmarks.triage.review_queue import build_queue


FIXTURES = Path(__file__).resolve().parents[1] / "benchmarks/triage/guarded-held-out"


class QueueScoreTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.alerts = FIXTURES / "alerts.json"
        self.labels = FIXTURES / "labels.json"
        self.decisions = root / "decisions.json"
        self.queue = root / "queue.json"
        self.decisions.write_text(json.dumps(run_guarded_candidate(self.alerts)), encoding="utf-8")
        self.packet = build_queue(self.alerts, self.decisions)

    def score(self):
        self.queue.write_text(json.dumps(self.packet), encoding="utf-8")
        return score_queue(self.alerts, self.decisions, self.labels, self.queue)

    def test_counts_review_burden_separately_from_misses_surfaced(self):
        results = self.score()
        self.assertEqual(results["queue_size"], 3)
        self.assertEqual(results["surfaced_miss_ids"], ["G14", "G08"])
        self.assertEqual(results["unsurfaced_miss_ids"], [])
        self.assertEqual(results["benign_review_ids"], ["G09"])
        self.assertEqual(results["miss_coverage"], 1)
        self.assertAlmostEqual(results["queue_precision"], 2 / 3)

    def test_rejects_wrong_artifact_link_and_already_escalated_items(self):
        digest = self.packet["decisions_sha256"]
        self.packet["decisions_sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "exact guarded decisions"):
            self.score()
        self.packet["decisions_sha256"] = digest
        self.packet["items"].append({"id": "G01"})
        with self.assertRaisesRegex(ValueError, "deferred alerts"):
            self.score()

    def test_empty_queue_has_no_precision_and_does_not_recover_misses(self):
        self.packet["items"] = []
        result = self.score()
        self.assertIsNone(result["queue_precision"])
        self.assertEqual(result["miss_coverage"], 0)
        self.assertEqual(result["unsurfaced_miss_ids"], ["G08", "G14"])
