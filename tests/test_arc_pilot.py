import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from benchmarks.arc.pilot import run_pilot


class PilotTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.proposal = self.root / "proposal.md"
        self.proposal.write_bytes(b"Evaluate a proposed documentation refresh.")
        self.case = {
            "kind": "arc_review_quality_checklist",
            "schema_version": 1,
            "role": "evaluation-science",
            "proposal_sha256": hashlib.sha256(self.proposal.read_bytes()).hexdigest(),
            "items": [{"id": "parity", "criterion": "ASSESSOR ONLY: require matched workloads."}],
        }
        (self.root / "checklist.json").write_text(json.dumps(self.case), encoding="utf-8")
        self.output = self.root / "run"

    @patch("benchmarks.arc.pilot.ChatModel")
    def test_masks_metadata_and_never_sends_the_checklist(self, constructor):
        seen = []

        class Reviewer:
            base_url = "http://127.0.0.1:11434/v1"

            def __init__(self, tag):
                self.model = tag

            def complete(self, messages):
                seen.append(messages)
                content = "invalid" if self.model == "candidate-b" else json.dumps({
                    "verdict": "conditional", "strengths": [], "blockers": [],
                    "experiments": [], "unknowns": [],
                })
                return {
                    "model": self.model, "usage": {"total_tokens": 20},
                    "choices": [{"message": {"content": content}}],
                }

        constructor.side_effect = lambda url, model, api_key: Reviewer(model)
        self.assertEqual(run_pilot(self.root, ["candidate-a", "candidate-b"], self.output, seed=7), 1)
        self.assertEqual(seen[0], seen[1])
        self.assertEqual(seen[0][1]["content"], self.proposal.read_text())
        self.assertNotIn("ASSESSOR ONLY", json.dumps(seen))

        operator = json.loads((self.output / "operator-run.json").read_bytes())
        packet = json.loads((self.output / "assessment-packet.json").read_bytes())
        self.assertEqual(operator["order_seed"], 7)
        self.assertEqual(len(operator["records"]), 2)
        self.assertEqual([record["attempt"]["status"] for record in operator["records"]],
                         ["valid", "invalid_response"])
        self.assertEqual(len(packet["reviews"]), 1)
        self.assertEqual(packet["reviews"][0]["candidate"], operator["records"][0]["candidate"])
        self.assertNotIn("candidate-a", json.dumps(packet))
        self.assertNotIn("total_tokens", json.dumps(packet))
        self.assertNotIn("order_seed", packet)
        with self.assertRaises(FileExistsError):
            run_pilot(self.root, ["candidate-a", "candidate-b"], self.output, seed=7)
        self.assertEqual(constructor.call_count, 2)

    @patch("benchmarks.arc.pilot.ChatModel")
    def test_rejects_changed_proposal_before_model_calls_or_output(self, constructor):
        self.proposal.write_bytes(b"Edited proposal")
        with self.assertRaisesRegex(ValueError, "proposal digest"):
            run_pilot(self.root, ["candidate-a", "candidate-b"], self.output)
        constructor.assert_not_called()
        self.assertFalse(self.output.exists())
