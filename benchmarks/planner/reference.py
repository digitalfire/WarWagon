"""Deterministic reference planner simulation. Standard library only.

This is NOT a real security assessment or an upstream-framework benchmark.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path

STRATEGIES = ('single', 'hierarchical', 'blackboard', 'hybrid')
FIXTURES = ('linear', 'wide', 'deep', 'ambiguous', 'contradictory', 'dynamic', 'failure', 'long_context')

@dataclass(frozen=True)
class Node:
    id: str
    parent: str | None
    reward: int
    signal: int
    family: int
    reliable: bool = True

@dataclass
class Result:
    fixture: str
    strategy: str
    seed: int
    action_budget: int
    workers: int
    verified_reward: int
    verified_count: int
    actions: int
    elapsed_ticks: int
    wasted_actions: int
    duplicates: int
    messages: int
    retries: int
    opportunity_count: int
    trace_digest: str

def fixture(name: str, seed: int, count: int = 24) -> dict[str, Node]:
    if name not in FIXTURES:
        raise ValueError(f'unknown fixture {name}')
    rng = random.Random(f'{name}:{seed}')
    nodes: dict[str, Node] = {}
    for i in range(count):
        ident = f'n{i:03d}'
        if name == 'linear':
            parent = f'n{i-1:03d}' if i else None
        elif name == 'deep':
            parent = f'n{(i-1)//2:03d}' if i else None
        else:
            parent = f'n{(i-1)//4:03d}' if i >= 4 else None
        family = i % 4
        value = rng.randrange(1, 9)
        signal = max(0, min(10, value + rng.randint(-4, 4)))
        reliable = rng.random() > (0.45 if name in ('ambiguous','contradictory') else 0.17)
        if name == 'wide':
            parent = None
        if name == 'long_context':
            signal = rng.randrange(0, 11)
        if name == 'dynamic' and i % 7 == 0:
            reliable = False
        nodes[ident] = Node(ident, parent, value, signal, family, reliable)
    return nodes

def rank_candidates(strategy: str, candidates: list[Node], completed: set[str], iteration: int) -> list[Node]:
    if strategy == 'single':
        return sorted(candidates, key=lambda n: n.id)
    if strategy == 'hierarchical':
        return sorted(candidates, key=lambda n: (-n.signal, n.id))
    if strategy == 'blackboard':
        counts = {f: sum(1 for x in completed if int(x[1:]) % 4 == f) for f in range(4)}
        return sorted(candidates, key=lambda n: (counts[n.family], -n.signal, n.id))
    if strategy == 'hybrid':
        counts = {f: sum(1 for x in completed if int(x[1:]) % 4 == f) for f in range(4)}
        return sorted(candidates, key=lambda n: (-(n.signal - 2*counts[n.family]), n.id))
    raise ValueError(strategy)

def simulate(name: str, strategy: str, seed: int, action_budget: int, workers: int = 4) -> Result:
    if action_budget < 1 or workers < 1:
        raise ValueError('budget and workers must be positive')
    nodes = fixture(name, seed)
    complete: set[str] = set()
    visited: set[str] = set()
    trace: list[dict] = []
    ticks = verified = waste = messages = retries = 0
    capacity = 1 if strategy == 'single' else workers
    while len(visited) < len(nodes) and len(visited) < action_budget:
        possible = [n for n in nodes.values() if n.id not in visited and (n.parent is None or n.parent in complete)]
        if not possible:
            break
        chosen = rank_candidates(strategy, possible, complete, ticks)[:min(capacity, action_budget-len(visited))]
        if not chosen:
            break
        ticks += 1
        if strategy != 'single':
            messages += len(chosen) + 1
        for n in chosen:
            visited.add(n.id)
            failed = name == 'failure' and (int(n.id[1:]) + seed) % 11 == 0
            if failed:
                retries += 1
                waste += 1
                trace.append({'tick':ticks,'node':n.id,'outcome':'failed-worker'})
                continue
            if n.reliable:
                complete.add(n.id)
                verified += n.reward
                outcome = 'verified'
            else:
                waste += 1
                outcome = 'unverified'
            trace.append({'tick':ticks,'node':n.id,'outcome':outcome})
    digest = hashlib.sha256(json.dumps(trace,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return Result(name,strategy,seed,action_budget,workers,verified,len(complete),len(visited),ticks,waste,0,messages,retries,len(nodes),digest)

def run(seeds: list[int], budget: int, workers: int, fixtures: tuple[str,...] = FIXTURES) -> list[Result]:
    return [simulate(f,s,seed,budget,workers) for f in fixtures for seed in seeds for s in STRATEGIES]

def main() -> None:
    parser = argparse.ArgumentParser(description='WarWagon synthetic planner comparison harness')
    parser.add_argument('--seeds',type=int,default=5)
    parser.add_argument('--budget',type=int,default=16)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--output',type=Path,default=Path('planner-results.json'))
    args = parser.parse_args()
    if min(args.seeds,args.budget,args.workers) < 1:
        parser.error('seeds, budget, and workers must be positive')
    results = run(list(range(args.seeds)),args.budget,args.workers)
    payload = {'schema_version':'0.1.0','kind':'synthetic_scheduler_smoke_test',
        'warning':'Deterministic simulator only; no LLMs, tools, real target testing, or framework comparisons',
        'config':{'seeds':args.seeds,'budget':args.budget,'workers':args.workers},
        'runs':[asdict(x) for x in results]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {len(results)} synthetic runs to {args.output}')
    for s in STRATEGIES:
        subset = [r for r in results if r.strategy == s]
        print(f'{s:12} mean_verified_reward={sum(r.verified_reward for r in subset)/len(subset):.2f} mean_ticks={sum(r.elapsed_ticks for r in subset)/len(subset):.2f}')

if __name__ == '__main__':
    main()
