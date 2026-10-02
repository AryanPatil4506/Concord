"""Monte-Carlo feasibility forecasts split across worker processes.

Each rollout is seeded by its index, so results match concord_sim.forecast exactly.
"""
from __future__ import annotations

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor

import concord_sim as cs

K_DEFAULT = 40
_pool: ProcessPoolExecutor | None = None


def pool() -> ProcessPoolExecutor:
    global _pool
    if _pool is None:
        _pool = ProcessPoolExecutor(max_workers=max(2, min(8, (os.cpu_count() or 4) - 1)),
                                    mp_context=multiprocessing.get_context("spawn"))
    return _pool


def shutdown():
    global _pool
    if _pool is not None:
        _pool.shutdown(cancel_futures=True)
        _pool = None


def _wins(world, ks, seed, flags):
    return cs.forecast_wins(world, ks, seed, **flags)


def portable(world, force_trigger=None):
    """A lean clone that is cheap to send to a worker (distance-map caches dropped)."""
    c = world.clone()
    c._g, c._a = {}, {}
    if force_trigger:
        c.pending_triggers.add(force_trigger)
    return c


async def forecast(loop, world, K=K_DEFAULT, seed=1, flags=None, force_trigger=None):
    flags = flags or {}
    w = portable(world, force_trigger)
    n = min(8, K)
    chunks = [range(i, K, n) for i in range(n)]
    futs = [loop.run_in_executor(pool(), _wins, w, list(ks), seed, flags) for ks in chunks]
    wins = 0
    for f in futs:
        wins += await f
    return wins / K
