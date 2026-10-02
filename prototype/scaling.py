#!/usr/bin/env python3
"""
Allocator scaling test: how long does CONCORD take to (re)plan as the swarm grows?

For fleet sizes N in {5, 10, 20, 50, 100, 200} (mixed scouts / cargo drones / rovers,
2:1:1) and 3N open tasks (surveys + deliveries) on the 40x28 map:
  * global re-plan : every task re-auctioned from scratch (worst case)
  * repair re-plan : one agent fails, only its tasks are re-auctioned (common case)
Distance maps are warm (cached), as they are between terrain changes; the cold-cache
cost of recomputing ground maps after a terrain change is reported separately.
Single CPU core, pure Python.
"""
import json
import os
import statistics
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concord_sim as cs  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)


def build(seed, n):
    w = cs.World(seed)
    rng = np.random.default_rng(seed)
    kinds = (["scout", "scout", "cargo", "rover"] * n)[:n]
    land = [(x, y) for y in range(cs.H) for x in range(cs.W) if w.terr[y, x] == cs.LAND
            and w.gmap(cs.BASE)[y, x] < cs.INF]
    agents = []
    for i, k in enumerate(kinds):
        a = cs.Agent(f"{k}-{i}", i, k)
        a.pos = land[int(rng.integers(0, len(land)))]
        agents.append(a)
    w.agents = agents
    w.by_id = {a.id: a for a in agents}
    w.tasks = {}
    for j in range(3 * n):
        pos = land[int(rng.integers(0, len(land)))]
        if j % 3 == 2:
            w.tasks[f"D{j}"] = cs.Task(f"D{j}", "deliver", pos, 1.0, "payload", 2, True, 0, label=f"D{j}")
        else:
            w.tasks[f"V{j}"] = cs.Task(f"V{j}", "survey", pos, 0.4, "camera", 1, False, 0, label=f"V{j}")
    return w


def trial(seed, n):
    w = build(seed, n)
    pol = cs.Concord()
    ids = list(w.tasks)
    # cold cache: ground maps for every task target + base
    t0 = time.perf_counter()
    for tk in w.tasks.values():
        w.gmap(tk.pos)
    w.gmap(cs.BASE)
    cold = time.perf_counter() - t0
    # global re-plan (warm cache)
    t0 = time.perf_counter()
    pol.auction(w, ids, w.agents)
    glob = time.perf_counter() - t0
    assigned = sum(1 for t in w.tasks.values() if t.status == "assigned")
    # repair: fail the agent holding the most tasks, re-auction its tasks
    victim = max(w.agents, key=lambda a: sum(1 for it in a.plan if isinstance(it, str) and it != "BASE"))
    victim.status = "lost"
    rel = w.release_plan(victim)
    alive = [a for a in w.agents if a.alive]
    t0 = time.perf_counter()
    pol.auction(w, rel, alive)
    rep = time.perf_counter() - t0
    return dict(n=n, tasks=len(ids), assigned=assigned, cold_ms=cold * 1000, global_ms=glob * 1000,
                repair_ms=rep * 1000, repaired=len(rel))


def main():
    rows = []
    for n in (5, 10, 20, 50, 100, 200):
        trials = [trial(100 + r, n) for r in range(5 if n <= 100 else 3)]
        row = dict(n=n, tasks=3 * n,
                   global_ms=statistics.median(t["global_ms"] for t in trials),
                   repair_ms=statistics.median(t["repair_ms"] for t in trials),
                   cold_ms=statistics.median(t["cold_ms"] for t in trials),
                   assigned_frac=statistics.mean(t["assigned"] / t["tasks"] for t in trials),
                   repaired=statistics.mean(t["repaired"] for t in trials))
        rows.append(row)
        print(row, flush=True)
    with open(os.path.join(OUT, "scaling.json"), "w") as f:
        json.dump(rows, f, indent=1)


if __name__ == "__main__":
    main()
