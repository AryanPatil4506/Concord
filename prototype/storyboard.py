#!/usr/bin/env python3
"""
Storyboard mission for the demo: one flood search-and-rescue run with scripted
disruptions (the random benchmark is in run_benchmark.py). Produces:
  results/storyboard.json   forecast timeline, escalation card, decision log
  frames/                   console frames (for the GIF / MP4 and slide stills)
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concord_sim as cs  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)


TMAX, NSURV = 200, 6
T_BRIDGE, T_BLACKOUT, T_DRAIN, T_STORM, T_FAIL, T_NEW = 25, 45, 35, 75, 85, 100


def script_events(storm_center, blackout_center, new_pos):
    return [
        (T_BRIDGE, "bridge_collapse", {"bridge": 0}),
        (T_BLACKOUT, "comm_blackout", {"center": blackout_center, "r": 4.0}),
        (T_DRAIN, "battery_drain", {"idx": 1, "frac": 0.20}),
        (T_STORM, "storm", {"center": storm_center, "r": 5.5, "dur": 80}),
        (T_FAIL, "agent_fail", {"idx": 3}),   # Rover-1 fails
    ]


def forecast_opts(w, K, flags):
    """Forecast with a forced re-plan so an option's policy takes effect immediately."""
    c = w.clone()
    c.pending_triggers.add("storm_end" if w.storm is None else "storm")
    return cs.forecast(c, K=K, seed=7, **flags)


def run(seed, K=40, every=10, verbose=True):
    w0 = cs.World(seed, n_surv=NSURV, tmax=TMAX)
    # scenario-specific placements derived from the seeded map
    storm_center = (25, 21)
    blackout_center = (33, 21)
    new_pos = cs.sample_land_in_sectors(np.random.default_rng(seed + 3), w0.terr, 1, avoid=[s.pos for s in w0.survivors])[0]
    events = script_events(storm_center, blackout_center, new_pos)
    w = cs.World(seed, events=events, record=True, n_surv=NSURV, tmax=TMAX)
    pol = cs.make_policy("concord")
    pol.init(w)
    timeline, escalation = [], None
    active_flags = {}
    while not w.finished():
        if w.t % every == 0:
            p = cs.forecast(w, K=K, seed=1, **active_flags)
            timeline.append((w.t, p))
            w.forecasts.append((w.t, p))
            if verbose:
                print(f"t={w.t:3d}  P(success)={p:.2f}", flush=True)
        cs.step(w, pol)
        # escalation check right after the storm/fault re-plans
        if escalation is None and w.t - 1 in (T_STORM, T_FAIL):
            p_now = cs.forecast(w, K=K, seed=2)
            timeline.append((w.t, p_now))
            if p_now < 0.6:
                p_hold = p_now
                p_risk = forecast_opts(w, K, {"risk_override": {"cargo": 1.0}})
                opts = [
                    {"key": "A", "text": "Hold: keep drones out of the storm until it clears", "p": p_hold},
                    {"key": "B", "text": "Fly Cargo-1 through the storm now (risk of losing it)", "p": p_risk},
                ]
                rec = max(opts, key=lambda o: o["p"])["key"]
                pend = [s.sid for s in w.survivors if s.delivered_t is None and cs.sector_of(s.pos) == "C"]
                sit = (f"Rover-1 failed at t={T_FAIL}; Cargo-1 is the last payload carrier. {len(pend)} survivors "
                       f"({', '.join(pend)}) wait in sector C under a storm cell. Forecast {p_now:.0%} < 60% threshold.")
                escalation = dict(t=w.t, situation=sit, options=opts, recommend=rec, p_now=p_now)
                w.log.append(dict(t=w.t, kind="escalation",
                                  text=f"ESCALATION: P(success) {p_now:.0%} < 60% -> operator card; recommended {rec}"))
                if rec == "B":
                    pol.risk_override = {"cargo": 1.0}
                    active_flags = {"risk_override": {"cargo": 1.0}}
                    w.pending_triggers.add("storm")
                if verbose:
                    print("ESCALATION", escalation, flush=True)
    m = cs.metrics(w)
    return w, m, timeline, escalation, events


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    w, m, timeline, esc, events = run(seed)
    print(m)
    import pickle
    with open(os.path.join(OUT, "storyboard_frames.pkl"), "wb") as f:
        pickle.dump(dict(frames=w.frames, log=w.log, timeline=timeline, escalation=esc,
                         bridges=w.bridges, terr0=cs.World(seed, n_surv=NSURV, tmax=TMAX).terr), f)
    with open(os.path.join(OUT, "storyboard.json"), "w") as f:
        json.dump(dict(seed=seed, metrics=m, timeline=timeline, escalation=esc,
                       events=[(e[0], e[1], {k: (list(v) if isinstance(v, tuple) else v) for k, v in e[2].items()})
                               for e in events],
                       log=w.log), f, indent=1, default=str)
