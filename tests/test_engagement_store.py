"""Durable event-store contract tests; no model server or network target needed."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import unittest

from warwagon.engagement_store import EngagementLedger


class EngagementLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "engagements.db"
        self.store = EngagementLedger(self.path)

    def test_creation_restart_replay(self):
        created = self.store.create_engagement(
            "Local lab", "http://127.0.0.1:3000", model="tool-capable-local",
            engagement_id="eng-lab-test"
        )
        self.assertEqual(created["state"], "created")
        self.assertEqual(created["source"], "recorded")
        event = self.store.events("eng-lab-test")[0]
        self.assertEqual(event["kind"], "engagement.created")
        self.assertEqual(event["schemaVersion"], 1)
        reopened = EngagementLedger(self.path)
        self.assertEqual(reopened.get_engagement("eng-lab-test"), created)
        self.assertEqual(reopened.events("eng-lab-test"), [event])

    def test_atomic_idempotent_append_and_conflicting_retry(self):
        e = self.store.create_engagement("Demo", "local-fixture")
        eid = e["id"]
        self.store.transition(eid, "running")
        first = self.store.append(eid, "agent.tool.called", {"tool":"lab_http_get","path":"/"},
                                  event_id="call-001", origin="tool")
        retry = EngagementLedger(self.path).append(
            eid, "agent.tool.called", {"path":"/","tool":"lab_http_get"},
            event_id="call-001", origin="tool")
        self.assertEqual(retry, first)
        with self.assertRaisesRegex(ValueError, "idempotency key"):
            self.store.append(eid, "agent.tool.called", {"path":"/other"},
                              event_id="call-001", origin="tool")
        self.assertEqual(len(self.store.events(eid)), 3)

    def test_concurrent_append_monotonic_sequence_and_cursor(self):
        eid = self.store.create_engagement("Concurrency", "training").get("id")
        self.store.transition(eid, "running")
        def emit(i):
            return EngagementLedger(self.path).append(
                eid, "agent.observation.recorded", {"n":i},
                event_id="observation-" + str(i), origin="test"
            )
        with ThreadPoolExecutor(max_workers=5) as pool:
            events = list(pool.map(emit, range(30)))
        self.assertEqual(len(set(x["sequence"] for x in events)), 30)
        all_events = self.store.events(eid)
        self.assertEqual(len(all_events), 32)
        self.assertEqual([e["sequence"] for e in all_events],
                         sorted(e["sequence"] for e in all_events))
        after = all_events[12]["sequence"]
        suffix = self.store.events(eid, after=after, limit=3)
        self.assertEqual(suffix, all_events[13:16])
        self.assertTrue(all(e["sequence"] > after for e in suffix))

    def test_terminal_state_rejects_new_events_but_accepts_safe_retry(self):
        e = self.store.create_engagement("Finish", "test")
        eid = e["id"]
        self.store.transition(eid, "running")
        before = self.store.append(eid, "agent.final", {"content":"observed 200"},
                                   event_id="final-01")
        state = self.store.transition(eid, "completed")
        self.assertEqual(state["state"], "completed")
        with self.assertRaisesRegex(ValueError, "terminal"):
            self.store.append(eid, "agent.tool.called", {}, event_id="too-late")
        self.assertEqual(self.store.append(eid, "agent.final",
                                          {"content":"observed 200"}, event_id="final-01"), before)
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            self.store.transition(eid, "running")

    def test_cross_engagement_isolation_and_source_validity(self):
        a = self.store.create_engagement("A", "fixture-a")
        b = self.store.create_engagement("B", "fixture-b")
        self.store.append(a["id"], "agent.started", {"test":1}, event_id="same-key")
        self.store.append(b["id"], "agent.started", {"test":2}, event_id="same-key")
        self.assertEqual(len(self.store.events(a["id"])), 2)
        self.assertEqual(len(self.store.events(b["id"])), 2)
        self.assertNotEqual(self.store.events(a["id"])[-1]["sequence"],
                            self.store.events(b["id"])[-1]["sequence"])
        self.assertEqual(len(self.store.list_engagements()), 2)
        with self.assertRaises(KeyError):
            self.store.events("missing")

    def test_event_validation_and_transaction_rollback(self):
        e = self.store.create_engagement("Validation", "training")
        eid = e["id"]
        with self.assertRaises(ValueError):
            self.store.append(eid, "agent.tool.called", ["not","an","object"])
        with self.assertRaises(ValueError):
            self.store.append(eid, "bad kind", {})
        with self.assertRaises(ValueError):
            self.store.append(eid, "agent.final", {"huge": "x"*260000})
        with self.assertRaises(ValueError):
            self.store.events(eid, after=-1)
        with self.assertRaises(ValueError):
            self.store.events(eid, limit=0)
        self.assertEqual(len(self.store.events(eid)), 1)
        self.assertEqual(self.store.get_engagement(eid)["state"], "created")

    def test_stored_event_digest_checked_on_every_read_and_idempotent_retry(self):
        engagement = self.store.create_engagement("Integrity", "lab")
        eid = engagement["id"]
        self.store.append(eid, "tool.observation", {"status": 200}, event_id="original")
        with self.store._connect() as db:
            db.execute(
                "UPDATE engagement_events SET payload_json=? "
                "WHERE engagement_id=? AND event_id=?",
                ('{"status":201}', eid, "original"),
            )
        with self.assertRaisesRegex(ValueError, "stored event payload digest mismatch"):
            self.store.events(eid)
        with self.assertRaisesRegex(ValueError, "stored event payload digest mismatch"):
            self.store.append(eid, "tool.observation", {"status": 200}, event_id="original")


if __name__ == "__main__":
    unittest.main()
