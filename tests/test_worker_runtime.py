"""Model-driven local worker runtime tests; CI models here are test doubles only."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from warwagon.engagement_store import EngagementLedger
from warwagon.worker_runtime import (
    BudgetExhausted, LeaseLost, SlidingRateLimiter, TaskQueue, run_two_worker_lab,
)


class ScriptedToolModel:
    model = "scripted-test-double"

    def __init__(self, gate=None):
        self.calls = 0
        self.gate = gate

    def complete(self, messages, tools=None):
        self.calls += 1
        if self.calls == 1:
            if self.gate:
                self.gate.wait(timeout=5)
            return {
                "choices": [{"message": {
                    "role": "assistant", "content": None,
                    "tool_calls": [{
                        "id": "call-test-1", "type": "function",
                        "function": {
                            "name": "lab_http_get",
                            "arguments": '{"path":"/search?q=%3Cb%3EWW_MARKER%3C%2Fb%3E"}',
                        },
                    }],
                }}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 40,
                          "total_tokens": 140},
            }
        return {
            "choices": [{"message": {
                "role": "assistant",
                "content": "Observed unencoded reflected HTML markup on /search in the local fixture.",
            }}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20,
                      "total_tokens": 70},
        }


class BrokenModel:
    model = "broken-test-double"

    def complete(self, messages, tools=None):
        raise RuntimeError("inference unavailable")


class WorkerRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "workers.sqlite3"
        self.ledger = EngagementLedger(self.path)

    def test_two_concurrent_workers_use_shared_budget_and_save_real_tool_observations(self):
        # The barrier ensures two independently executed model calls overlap.
        barrier = threading.Barrier(2)
        result = run_two_worker_lab(
            lambda: ScriptedToolModel(barrier),
            self.ledger, workers=2, max_calls=8, max_tokens=2000,
            max_seconds=30, max_steps=3, lease_seconds=3,
        )
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["workerLimit"], 2)
        self.assertEqual(result["budget"]["modelCalls"], 4)
        self.assertEqual(result["budget"]["tokensReported"], 420)
        self.assertTrue(result["budget"]["usageComplete"])
        self.assertEqual(set(result["tasks"].values()), {"completed"})
        self.assertEqual(len(result["agentHeuristics"]), 2)
        eid = result["engagementId"]
        queue = TaskQueue(EngagementLedger(self.path))
        records = queue.tasks(eid)
        self.assertEqual(len(records), 2)
        self.assertEqual(set(row["attempt"] for row in records), {1})
        events = self.ledger.events(eid)
        kinds = [event["kind"] for event in events]
        self.assertEqual(kinds.count("task.claimed"), 2)
        self.assertEqual(kinds.count("task.completed"), 2)
        self.assertEqual(kinds.count("model.response"), 4)
        self.assertEqual(kinds.count("tool.invocation"), 2)
        self.assertEqual(kinds.count("tool.observation"), 2)
        for item in (event for event in events if event["kind"] == "tool.observation"):
            self.assertEqual(item["payload"]["result"]["status"], 200)
            self.assertIn("<b>WW_MARKER</b>", item["payload"]["result"]["body"])
            self.assertIn(item["payload"]["workerId"], ("worker-1", "worker-2"))
        self.assertEqual(self.ledger.get_engagement(eid)["state"], "completed")

    def test_atomic_claims_do_not_duplicate_single_task(self):
        e = self.ledger.create_engagement("Lab", "loopback")
        queue = TaskQueue(self.ledger)
        queue.configure(e["id"], [("only-task", "Observe the lab")],
                        max_calls=4, max_tokens=5000, max_seconds=30)
        def claim(index):
            return TaskQueue(EngagementLedger(self.path)).claim(e["id"], "worker-"+str(index))
        with ThreadPoolExecutor(max_workers=5) as executor:
            claims = list(executor.map(claim, range(5)))
        winners = [claim for claim in claims if claim is not None]
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0]["attempt"], 1)

    def test_lease_expiration_fences_stale_worker_and_supports_reclaim(self):
        eid = self.ledger.create_engagement("Reclaim", "local")["id"]
        queue = TaskQueue(self.ledger)
        queue.configure(eid, [("one", "Observe")], max_calls=2,
                        max_tokens=2000, max_seconds=30)
        first = queue.claim(eid, "worker-1", lease_seconds=.06)
        time.sleep(.09)
        second = TaskQueue(EngagementLedger(self.path)).claim(
            eid, "worker-2", lease_seconds=1
        )
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(second["attempt"], 2)
        with self.assertRaises(LeaseLost):
            queue.finish(eid, "one", "worker-1", first["attempt"],
                         status="completed", result={})
        with self.assertRaises(LeaseLost):
            queue.record(eid, "one", "worker-1", first["attempt"],
                         "agent.final", {}, ordinal=1)
        queue.finish(eid, "one", "worker-2", second["attempt"],
                     status="completed", result={"observed": True})
        self.assertEqual(queue.tasks(eid)[0]["status"], "completed")

    def test_global_call_limit_and_token_accounting_are_shared(self):
        result = run_two_worker_lab(
            ScriptedToolModel,self.ledger,workers=2,max_calls=1,
            max_tokens=100000,max_seconds=30,max_steps=3,
        )
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["budget"]["modelCalls"], 1)
        self.assertTrue(all(s == "blocked" for s in result["tasks"].values()))
        self.assertTrue(result["budget"]["usageComplete"])

    def test_token_cap_stops_new_calls_after_an_in_flight_overrun(self):
        result = run_two_worker_lab(
            ScriptedToolModel,self.ledger,workers=1,
            max_calls=5,max_tokens=100,max_seconds=30,max_steps=4,
        )
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["budget"]["modelCalls"], 1)
        self.assertEqual(result["budget"]["tokensReported"], 140)
        # Token usage is known only after a provider response and may overrun
        # by one in-flight call; all further invocations are blocked.

    def test_inference_failure_is_recorded_not_marked_verified(self):
        result = run_two_worker_lab(
            BrokenModel,self.ledger,workers=2,max_calls=4,
            max_tokens=1000,max_seconds=30,max_steps=2,
        )
        self.assertEqual(result["state"], "failed")
        self.assertFalse(result["budget"]["usageComplete"])
        eid = result["engagementId"]
        kinds = [event["kind"] for event in self.ledger.events(eid)]
        self.assertEqual(kinds.count("task.failed"), 2)
        self.assertEqual(kinds.count("budget.usage.recorded"), 2)
        self.assertNotIn("finding.verified", kinds)

    def test_duplicate_config_is_idempotent_and_mismatches_are_rejected(self):
        e = self.ledger.create_engagement("Idempotent", "training")
        queue = TaskQueue(self.ledger)
        config = {"tasks": [("t-1", "Inspect lab")], "max_calls": 3,
                  "max_tokens": 4000, "max_seconds": 10}
        queue.configure(e["id"], **config)
        before = self.ledger.events(e["id"])
        TaskQueue(EngagementLedger(self.path)).configure(e["id"], **config)
        self.assertEqual(before, self.ledger.events(e["id"]))
        with self.assertRaisesRegex(ValueError, "plan differs"):
            queue.configure(e["id"], tasks=[("t-1", "Different")],
                            max_calls=3, max_tokens=4000, max_seconds=10)
        with self.assertRaisesRegex(ValueError, "budget"):
            queue.configure(e["id"], tasks=[("t-1", "Inspect lab")],
                            max_calls=4, max_tokens=4000, max_seconds=10)

    def test_deadline_and_call_budget_are_atomic(self):
        eid = self.ledger.create_engagement("Deadline", "lab")["id"]
        queue = TaskQueue(self.ledger)
        queue.configure(eid, [("t-1", "Inspect")], max_calls=1,
                        max_tokens=2000, max_seconds=20)
        claim = queue.claim(eid, "worker")
        with ThreadPoolExecutor(max_workers=2) as executor:
            attempts = list(executor.map(
                lambda _: try_reserve(queue, eid, claim), range(2)
            ))
        self.assertEqual(sum(attempts), 1)
        self.assertEqual(queue.budget(eid)["used_calls"], 1)
        with self.ledger._connect() as db:
            db.execute("UPDATE agent_work_budgets SET deadline_epoch=? WHERE engagement_id=?",
                       (time.time()-1,eid))
        with self.assertRaises(BudgetExhausted):
            queue.reserve_model_call(eid,"t-1","worker",claim["attempt"])

    def test_invalid_workers_and_rate_limit_are_rejected(self):
        with self.assertRaises(ValueError):
            SlidingRateLimiter(0)
        with self.assertRaises(ValueError):
            run_two_worker_lab(ScriptedToolModel,self.ledger,workers=3)


def try_reserve(queue,eid,claim):
    try:
        queue.reserve_model_call(eid,claim["taskId"],claim["workerId"],claim["attempt"])
        return True
    except BudgetExhausted:
        return False


if __name__ == "__main__":
    unittest.main()
