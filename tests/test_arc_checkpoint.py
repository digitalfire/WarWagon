import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from warwagon.arc import ROLES, main


REPO = Path(__file__).resolve().parents[1]
RECORD = {
    "status": "valid",
    "response_model": None,
    "review": {
        "verdict": "conditional", "strengths": [], "blockers": [],
        "experiments": [], "unknowns": [],
    },
}
INTERRUPTED_RUN = """
import json
import os
from warwagon import arc
record = json.loads(os.environ["ARC_TEST_RECORD"])
calls = []
def interrupted_review(model, role, proposal):
    calls.append(role)
    if len(calls) == 2:
        os._exit(93)
    return {**record, "role": role}
arc.review = interrupted_review
raise SystemExit(arc.main())
"""


class CheckpointTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.proposal = root / "proposal.md"
        self.proposal.write_bytes(b"Frozen documentation proposal\r\n")
        self.checkpoint = root / "arc.sqlite"
        self.output = root / "result.json"
        self.argv = [
            "arc", "--proposal", str(self.proposal), "--model", "stub-reviewer",
            "--checkpoint", str(self.checkpoint), "--output", str(self.output),
        ]

    def interrupt_after_first_attempt(self):
        with patch.dict("os.environ", {"ARC_TEST_RECORD": json.dumps(RECORD)}):
            process = subprocess.run(
                [sys.executable, "-B", "-c", INTERRUPTED_RUN, *self.argv[1:]],
                cwd=REPO, capture_output=True, text=True, timeout=15,
            )
        self.assertEqual(process.returncode, 93, process.stderr)
        self.assertFalse(self.output.exists())

    def test_abrupt_process_exit_resumes_only_uncommitted_roles(self):
        self.interrupt_after_first_attempt()
        with patch("sys.argv", self.argv), patch(
            "warwagon.arc.review", side_effect=lambda model, role, proposal: {**RECORD, "role": role},
        ) as reviewer:
            self.assertEqual(main(), 0)
        self.assertEqual([call.args[1] for call in reviewer.call_args_list], list(ROLES)[1:])
        report = json.loads(self.output.read_bytes())
        self.assertEqual([record["role"] for record in report["reviews"]], list(ROLES))
        self.assertEqual(report["valid_review_count"], len(ROLES))

    def test_refuses_changed_proposal_before_invoking_any_reviewers(self):
        self.interrupt_after_first_attempt()
        self.proposal.write_bytes(b"Edited proposal")
        with patch("sys.argv", self.argv), patch("warwagon.arc.review") as reviewer, patch(
            "sys.stderr", new_callable=io.StringIO,
        ) as stderr:
            with self.assertRaises(SystemExit) as error:
                main()
        self.assertEqual(error.exception.code, 2)
        self.assertIn("different ARC proposal or reviewer configuration", stderr.getvalue())
        reviewer.assert_not_called()
