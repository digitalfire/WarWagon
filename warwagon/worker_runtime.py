"""Concurrent model-driven local-lab agents with durable task leases and shared budgets.

This is a bounded experimental runtime, NOT a general target-scanning engine.
The only HTTP test tool is LabTool's allowlisted loopback fixture.
"""
from __future__ import annotations

import argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import threading
import time
from uuid import uuid4

from warwagon.agent import AgentRunner
from warwagon.engagement_store import EngagementLedger, DEFAULT_PATH, _now
from warwagon.lab import FixtureServer, LabTool, verify_finding
from warwagon.model import ChatModel
from warwagon.scoring import score_discovery


class BudgetExhausted(RuntimeError):
    pass


class LeaseLost(RuntimeError):
    pass


# Independently reasoned goal contexts, not two copies of a single checklist.
LAB_TASKS = (
    ("map-surface", "Map the local lab using HTTP observations. Inspect the home page, the search function, and the profile function. Explain the evidence and limits of your observations."),
    ("test-html-encoding", "Investigate the local lab's HTML output encoding. Compare /search and /profile using a non-destructive HTML marker. Cite actual tool observations, not guesses."),
)


class TaskQueue:
    def __init__(self, ledger: EngagementLedger):
        self.ledger = ledger
        with ledger._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS agent_work_tasks (
                    engagement_id TEXT NOT NULL REFERENCES engagements(id),
                    task_id TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed','blocked')),
                    lease_owner TEXT,
                    lease_until REAL,
                    attempt INTEGER NOT NULL DEFAULT 0,
                    result_json TEXT,
                    PRIMARY KEY(engagement_id,task_id)
                );
                CREATE INDEX IF NOT EXISTS agent_work_claims
                  ON agent_work_tasks(engagement_id,status,lease_until,task_id);
                CREATE TABLE IF NOT EXISTS agent_work_budgets (
                    engagement_id TEXT PRIMARY KEY REFERENCES engagements(id),
                    max_calls INTEGER NOT NULL CHECK(max_calls > 0),
                    used_calls INTEGER NOT NULL DEFAULT 0,
                    max_tokens INTEGER NOT NULL CHECK(max_tokens > 0),
                    used_tokens INTEGER NOT NULL DEFAULT 0,
                    usage_complete INTEGER NOT NULL DEFAULT 1,
                    deadline_epoch REAL NOT NULL
                );
            """)

    def _write_event(self, db, eid, event_id, kind, payload, origin="worker"):
        return self.ledger._insert_event(db, eid, event_id, kind, origin, payload, _now())

    @staticmethod
    def _transaction(db):
        db.execute("BEGIN IMMEDIATE")

    @staticmethod
    def _commit(db):
        db.execute("COMMIT")

    def configure(self, eid, tasks=LAB_TASKS, *, max_calls=20, max_tokens=100000, max_seconds=120):
        if (not tasks or len({t[0] for t in tasks}) != len(tasks)
            or any(not isinstance(t[0],str) or not isinstance(t[1],str)
                   or not t[0] or not t[1] for t in tasks)):
            raise ValueError("tasks must have distinct nonblank IDs and goals")
        if (type(max_calls) is not int or not 1<=max_calls<=10000
            or type(max_tokens) is not int or not 1<=max_tokens<=50000000
            or type(max_seconds) is not int or not 1<=max_seconds<=86400):
            raise ValueError("invalid budget")
        with self.ledger._connect() as db:
            self._transaction(db)
            try:
                engagement=db.execute("SELECT state FROM engagements WHERE id=?",(eid,)).fetchone()
                if engagement is None or engagement["state"] not in ("created","running"):
                    raise ValueError("engagement missing or terminal")
                budget=db.execute("SELECT * FROM agent_work_budgets WHERE engagement_id=?",(eid,)).fetchone()
                if budget is None:
                    db.execute("""INSERT INTO agent_work_budgets
                      (engagement_id,max_calls,max_tokens,deadline_epoch) VALUES (?,?,?,?)""",
                      (eid,max_calls,max_tokens,time.time()+max_seconds))
                elif budget["max_calls"]!=max_calls or budget["max_tokens"]!=max_tokens:
                    raise ValueError("cannot silently change an existing budget")
                current={row["task_id"]:row["goal"] for row in db.execute(
                    "SELECT task_id,goal FROM agent_work_tasks WHERE engagement_id=?",(eid,))}
                if current and current!={tid:goal for tid,goal in tasks}:
                    raise ValueError("task plan differs from the frozen persisted plan")
                for task_id,goal in tasks:
                    if task_id in current:continue
                    self.ledger._validate_id(task_id)
                    db.execute("""INSERT INTO agent_work_tasks
                        (engagement_id,task_id,goal,status) VALUES (?,?,?,'queued')""",
                        (eid,task_id,goal))
                    self._write_event(db,eid,"task.queued."+task_id,"task.queued",
                                      {"taskId":task_id,"goal":goal},"scheduler")
                self._commit(db)
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def tasks(self,eid):
        with self.ledger._connect() as db:
            rows=db.execute("""SELECT * FROM agent_work_tasks
                WHERE engagement_id=? ORDER BY task_id""",(eid,)).fetchall()
        return [dict(r) for r in rows]

    def budget(self,eid):
        with self.ledger._connect() as db:
            row=db.execute("SELECT * FROM agent_work_budgets WHERE engagement_id=?",(eid,)).fetchone()
        if row is None:raise KeyError("budget missing")
        return dict(row)

    def claim(self,eid,owner,*,lease_seconds=30):
        self.ledger._validate_id(owner)
        if lease_seconds<=0:raise ValueError("lease_seconds must be positive")
        now=time.time()
        with self.ledger._connect() as db:
            self._transaction(db)
            try:
                row=db.execute("""SELECT * FROM agent_work_tasks
                    WHERE engagement_id=? AND
                      (status='queued' OR (status='running' AND lease_until < ?))
                    ORDER BY CASE status WHEN 'queued' THEN 0 ELSE 1 END,task_id
                    LIMIT 1""",(eid,now)).fetchone()
                if row is None:
                    self._commit(db)
                    return None
                attempt=row["attempt"]+1
                db.execute("""UPDATE agent_work_tasks SET
                    status='running',lease_owner=?,lease_until=?,attempt=?
                    WHERE engagement_id=? AND task_id=?""",
                    (owner,now+lease_seconds,attempt,eid,row["task_id"]))
                self._write_event(db,eid,f"task.claim.{row['task_id']}.{attempt}",
                    "task.claimed",{"taskId":row["task_id"],"workerId":owner,
                    "attempt":attempt,"reclaimed":row["status"]=="running"},"scheduler")
                self._commit(db)
                return {"taskId":row["task_id"],"goal":row["goal"],
                        "workerId":owner,"attempt":attempt}
            except BaseException:
                db.execute("ROLLBACK")
                raise

    @staticmethod
    def _assert_lease(db,eid,task,owner,attempt):
        row=db.execute("""SELECT * FROM agent_work_tasks
            WHERE engagement_id=? AND task_id=?""",(eid,task)).fetchone()
        if (row is None or row["status"]!="running" or
            row["lease_owner"]!=owner or row["attempt"]!=attempt or
            (row["lease_until"] or 0)<=time.time()):
            raise LeaseLost("task lease expired or worker was superseded")
        return row

    def renew(self,eid,task,owner,attempt,*,lease_seconds=30):
        if lease_seconds<=0:raise ValueError("lease_seconds must be positive")
        with self.ledger._connect() as db:
            self._transaction(db)
            try:
                self._assert_lease(db,eid,task,owner,attempt)
                db.execute("""UPDATE agent_work_tasks SET lease_until=?
                    WHERE engagement_id=? AND task_id=?""",
                    (time.time()+lease_seconds,eid,task))
                self._commit(db)
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def record(self,eid,task,owner,attempt,kind,payload,*,ordinal):
        if type(ordinal) is not int or ordinal<0:raise ValueError("invalid event ordinal")
        with self.ledger._connect() as db:
            self._transaction(db)
            try:
                self._assert_lease(db,eid,task,owner,attempt)
                data={"taskId":task,"workerId":owner,"attempt":attempt,**payload}
                self._write_event(db,eid,
                    f"worker.{task}.{attempt}.{ordinal}",kind,data,origin="local-agent")
                self._commit(db)
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def reserve_model_call(self,eid,task,owner,attempt):
        with self.ledger._connect() as db:
            self._transaction(db)
            try:
                self._assert_lease(db,eid,task,owner,attempt)
                budget=db.execute("SELECT * FROM agent_work_budgets WHERE engagement_id=?",
                                  (eid,)).fetchone()
                if (budget is None or budget["used_calls"]>=budget["max_calls"] or
                    budget["used_tokens"]>=budget["max_tokens"] or
                    time.time()>=budget["deadline_epoch"]):
                    raise BudgetExhausted("shared model-call, token, or time budget exhausted")
                number=budget["used_calls"]+1
                db.execute("""UPDATE agent_work_budgets SET used_calls=?
                    WHERE engagement_id=?""",(number,eid))
                self._write_event(db,eid,f"budget.call.{number}","budget.call.reserved",
                    {"callNumber":number,"taskId":task,"workerId":owner},"runtime")
                self._commit(db)
                return number
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def record_usage(self,eid,call_number,usage):
        count=usage.get("total_tokens") if isinstance(usage,dict) else None
        reported=type(count) is int and count>=0
        with self.ledger._connect() as db:
            self._transaction(db)
            try:
                row=db.execute("SELECT 1 FROM agent_work_budgets WHERE engagement_id=?",
                               (eid,)).fetchone()
                if row is None:raise KeyError("engagement budget missing")
                db.execute("""UPDATE agent_work_budgets
                    SET used_tokens=used_tokens+?,usage_complete=usage_complete AND ?
                    WHERE engagement_id=?""",
                    (count if reported else 0,1 if reported else 0,eid))
                self._write_event(db,eid,f"budget.usage.{call_number}",
                    "budget.usage.recorded",
                    {"callNumber":call_number,"totalTokens":count if reported else None,
                     "usageReported":reported},"runtime")
                self._commit(db)
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def finish(self,eid,task,owner,attempt,*,status,result):
        if status not in ("completed","failed","blocked"):
            raise ValueError("invalid terminal task status")
        if not isinstance(result,dict):
            raise ValueError("result must be an object")
        with self.ledger._connect() as db:
            self._transaction(db)
            try:
                self._assert_lease(db,eid,task,owner,attempt)
                db.execute("""UPDATE agent_work_tasks SET
                  status=?,lease_owner=NULL,lease_until=NULL,result_json=?
                  WHERE engagement_id=? AND task_id=?""",
                    (status,json.dumps(result,sort_keys=True),eid,task))
                self._write_event(db,eid,f"task.{status}.{task}.{attempt}",
                    "task."+status,{"taskId":task,"workerId":owner,"attempt":attempt,
                                     "result":result},"scheduler")
                self._commit(db)
            except BaseException:
                db.execute("ROLLBACK")
                raise


class SlidingRateLimiter:
    """Shared process-local sliding-window HTTP rate limiter for loopback GETs."""
    def __init__(self,rps=30):
        if type(rps) is not int or not 1<=rps<=1000:
            raise ValueError("rps must be between 1 and 1000")
        self.rate=rps
        self.lock=threading.Lock()
        self.starts=deque()

    def acquire(self):
        while True:
            with self.lock:
                now=time.monotonic()
                while self.starts and now-self.starts[0]>=1:
                    self.starts.popleft()
                if len(self.starts)<self.rate:
                    self.starts.append(now)
                    return
                delay=max(.001,1-(now-self.starts[0]))
            time.sleep(delay)


class BoundedTool:
    def __init__(self,underlying,limiter):
        self.tool=underlying
        self.limiter=limiter

    def get(self,path):
        self.limiter.acquire()
        return self.tool.get(path)


class BudgetedModel:
    """Hard call reservation, observed-token accounting; token cap is soft per call."""
    def __init__(self,model,queue,eid,task,owner,attempt):
        self.upstream=model
        self.model=model.model
        self.queue=queue
        self.eid,self.task,self.owner,self.attempt=eid,task,owner,attempt

    def complete(self,messages,tools=None):
        call=self.queue.reserve_model_call(self.eid,self.task,self.owner,self.attempt)
        try:
            result=self.upstream.complete(messages,tools=tools)
        except BaseException:
            self.queue.record_usage(self.eid,call,None)
            raise
        self.queue.record_usage(self.eid,call,result.get("usage"))
        return result


def run_two_worker_lab(model_factory,ledger:EngagementLedger,*,workers=2,
                       max_calls=20,max_tokens=100000,max_seconds=120,
                       max_steps=8,lease_seconds=30,http_rps=30):
    """Concurrent genuine-model investigations of the same allowlisted lab fixture.

    Two distinct specialist goals are fixed in this first slice; this is not
    autonomous task decomposition or a multi-target assessment API.
    """
    if type(workers) is not int or not 1<=workers<=2:
        raise ValueError("prototype supports 1 or 2 workers")
    if type(max_steps) is not int or not 1<=max_steps<=60:
        raise ValueError("max_steps must be 1..60")
    if lease_seconds<=0:
        raise ValueError("lease_seconds must be positive")
    with FixtureServer() as fixture:
        e=ledger.create_engagement(
            "Concurrent local HTML lab",f"http://127.0.0.1:{fixture.port}",
            model="per-worker provider model",
        )
        eid=e["id"]
        queue=TaskQueue(ledger)
        queue.configure(eid,max_calls=max_calls,max_tokens=max_tokens,max_seconds=max_seconds)
        ledger.transition(eid,"running")
        limiter=SlidingRateLimiter(http_rps)
        completed=[]

        def worker(index):
            owner="worker-"+str(index+1)
            model=model_factory()
            while True:
                claim=queue.claim(eid,owner,lease_seconds=lease_seconds)
                if claim is None:
                    return
                task,attempt=claim["taskId"],claim["attempt"]
                stop=threading.Event()
                lease_failed=threading.Event()
                counter=0

                def renew():
                    while not stop.wait(max(.02,lease_seconds/3)):
                        try:queue.renew(eid,task,owner,attempt,lease_seconds=lease_seconds)
                        except LeaseLost:
                            lease_failed.set()
                            return

                thread=threading.Thread(target=renew,daemon=True)
                thread.start()

                def sink(kind,payload):
                    nonlocal counter
                    if lease_failed.is_set():
                        raise LeaseLost("lease renewal failed")
                    counter+=1
                    queue.record(eid,task,owner,attempt,kind,payload,ordinal=counter)

                try:
                    bounded=BudgetedModel(model,queue,eid,task,owner,attempt)
                    tools=BoundedTool(LabTool(fixture.port),limiter)
                    result=AgentRunner(bounded,tools,max_steps,event_sink=sink).run(claim["goal"])
                    stop.set()
                    thread.join(timeout=1)
                    queue.finish(eid,task,owner,attempt,status="completed",
                        result={"toolSteps":sum(x["kind"]=="tool" for x in result["trace"]),
                                "usage":result["usage"],"stoppedAtStepLimit":
                                bool(result["trace"] and result["trace"][-1]["kind"]=="limit")})
                    completed.append({"taskId":task,"trace":result["trace"]})
                except LeaseLost:
                    stop.set()
                    thread.join(timeout=1)
                    # Fenced stale worker cannot complete or overwrite the reclaimed task.
                    return
                except BudgetExhausted as exc:
                    stop.set()
                    thread.join(timeout=1)
                    queue.finish(eid,task,owner,attempt,status="blocked",
                                 result={"reason":"shared_budget_exhausted","detail":str(exc)})
                    return
                except Exception as exc:
                    stop.set()
                    thread.join(timeout=1)
                    queue.finish(eid,task,owner,attempt,status="failed",
                                 result={"errorType":type(exc).__name__,"detail":str(exc)[:300]})
                    return

        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(worker,range(workers)))

        oracle=verify_finding(fixture.port)
        # Any test result must be trace-derived; fixture oracle alone gives no credit.
        results=[{"taskId":item["taskId"],
                  "heuristic":score_discovery(item["trace"],oracle)} for item in completed]
        ledger.append(eid,"lab.fixture.oracle",oracle,origin="fixture-verifier")
        ledger.append(eid,"lab.task.heuristics",{"tasks":results},origin="lab-scorer")
        tasks=queue.tasks(eid)
        budget=queue.budget(eid)
        finished=all(t["status"]=="completed" for t in tasks)
        ledger.append(eid,"runtime.run.finished",
                      {"allTasksCompleted":finished,"taskStatuses":
                       {t["task_id"]:t["status"] for t in tasks},
                       "callsReserved":budget["used_calls"],"tokensReported":budget["used_tokens"],
                       "usageComplete":bool(budget["usage_complete"])},
                      origin="runtime")
        ledger.transition(eid,"completed" if finished else "failed",
                          reason="" if finished else "incomplete_or_budget_exhausted")
    return {"engagementId":eid,"state":ledger.get_engagement(eid)["state"],
            "workerLimit":workers,
            "tasks":{t["task_id"]:t["status"] for t in tasks},
            "budget":{"modelCalls":budget["used_calls"],"tokensReported":budget["used_tokens"],
                      "usageComplete":bool(budget["usage_complete"])},
            "fixtureOracle":oracle,
            "agentHeuristics":results,
            "disclaimer":"A completed run is not proof of real-world vulnerability assessment efficacy."}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model",default=os.getenv("WW_MODEL",""))
    parser.add_argument("--base-url",default=os.getenv("WW_MODEL_BASE_URL","http://127.0.0.1:11434/v1"))
    parser.add_argument("--database",type=Path,default=DEFAULT_PATH)
    parser.add_argument("--workers",type=int,default=2,choices=(1,2))
    parser.add_argument("--model-calls",type=int,default=20)
    parser.add_argument("--tokens",type=int,default=100000)
    parser.add_argument("--seconds",type=int,default=120)
    parser.add_argument("--max-steps",type=int,default=8)
    parser.add_argument("--http-rps",type=int,default=30)
    args=parser.parse_args()
    if not args.model:parser.error("--model or WW_MODEL is required")
    result=run_two_worker_lab(
        lambda:ChatModel(args.base_url,args.model),EngagementLedger(args.database),
        workers=args.workers,max_calls=args.model_calls,max_tokens=args.tokens,
        max_seconds=args.seconds,max_steps=args.max_steps,http_rps=args.http_rps,
    )
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
