#!/usr/bin/env python3
"""
Seeded Monte-Carlo benchmark for CONCORD v0.

    python run_benchmark.py            # full run (writes results/*.json)

Experiments
  main     : 300 random disruption scenarios (default prior), 3 policies, paired seeds
  stress   : forced number of disruption types k = 0..6, 100 scenarios per k
  ablation : CONCORD with one component switched off, same 300 seeds as `main`
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concord_sim import World, run_mission, gen_events_k  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)

MAIN_SEEDS = list(range(1000, 1300))
STRESS_SEEDS = list(range(2000, 2100))
ABLATIONS = {
    "full": {},
    "no_battery_invariant": {"reserve": False},
    "no_risk_awareness": {"risk_aware": False},
    "no_relay_repositioning": {"dynamic_relay": False},
    "no_voi_messaging": {"voi": False, "report_seek": False},
    "no_hysteresis": {"sticky": 0.0},
}


def _job(args):
    kind, seed, policy, flags, k = args
    events = None
    if k is not None:
        w0 = World(seed)
        events = gen_events_k(np.random.default_rng(seed + 55_555), w0.terr, k)
    t0 = time.perf_counter()
    m, _ = run_mission(seed, policy, events=events, **flags)
    m["wall_ms"] = (time.perf_counter() - t0) * 1000
    m.update(kind=kind, policy=policy, k=k, flags=flags)
    return m


def main():
    jobs = []
    for s in MAIN_SEEDS:
        for p in ("concord", "greedy", "static"):
            jobs.append(("main", s, p, {}, None))
    for k in range(0, 7):
        for s in STRESS_SEEDS:
            for p in ("concord", "greedy", "static"):
                jobs.append(("stress", s, p, {}, k))
    for name, flags in ABLATIONS.items():
        if name == "full":
            continue
        for s in MAIN_SEEDS:
            jobs.append(("ablation:" + name, s, "concord", flags, None))
    t0 = time.time()
    with Pool(2) as pool:
        res = pool.map(_job, jobs, chunksize=8)
    print(f"{len(res)} missions in {time.time() - t0:.0f}s")
    with open(os.path.join(OUT, "benchmark_raw.json"), "w") as f:
        json.dump(res, f)


if __name__ == "__main__":
    main()
