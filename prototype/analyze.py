#!/usr/bin/env python3
"""Aggregate benchmark_raw.json -> summary.json (means + 95% bootstrap CIs)."""
import json, os, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "results", "benchmark_raw.json")))
rng = np.random.default_rng(0)
KEYS = ["success", "delivered_frac", "time_to_aid", "report_latency", "agents_lost", "agents_lost_non_injected",
        "coverage", "churn", "energy", "makespan", "wall_ms"]

def ci(vals, B=4000):
    v = np.array([x for x in vals if x is not None and not (isinstance(x, float) and math.isnan(x))], float)
    if len(v) == 0: return (float("nan"),) * 3
    idx = rng.integers(0, len(v), (B, len(v)))
    bs = v[idx].mean(1)
    return float(v.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

def summarize(rows):
    out = {k: ci([r[k] for r in rows]) for k in KEYS}
    aid = [a for r in rows for a in r["aid_times"]]
    out["n"] = len(rows)
    out["aid_times"] = aid
    return out

summary = {"main": {}, "stress": {}, "ablation": {}}
for p in ("concord", "greedy", "static"):
    summary["main"][p] = summarize([r for r in R if r["kind"] == "main" and r["policy"] == p])
for k in range(7):
    summary["stress"][k] = {p: summarize([r for r in R if r["kind"] == "stress" and r["k"] == k and r["policy"] == p])
                            for p in ("concord", "greedy", "static")}
summary["ablation"]["full"] = summary["main"]["concord"]
for kind in sorted(set(r["kind"] for r in R if r["kind"].startswith("ablation:"))):
    summary["ablation"][kind.split(":")[1]] = summarize([r for r in R if r["kind"] == kind])

# paired differences concord - greedy on main
main = {p: {r["seed"]: r for r in R if r["kind"] == "main" and r["policy"] == p} for p in ("concord", "greedy", "static")}
paired = {}
for k in ("time_to_aid", "report_latency", "agents_lost_non_injected", "success", "delivered_frac", "energy"):
    d = [main["concord"][s][k] - main["greedy"][s][k] for s in main["concord"]
         if not (isinstance(main["concord"][s][k], float) and math.isnan(main["concord"][s][k]))
         and not (isinstance(main["greedy"][s][k], float) and math.isnan(main["greedy"][s][k]))]
    paired[k] = ci(d)
summary["paired_concord_minus_greedy"] = paired
json.dump(summary, open(os.path.join(HERE, "results", "summary.json"), "w"), indent=1)

def fmt(t): return f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"
print("=== MAIN (300 random scenarios) ===")
for p in ("concord", "greedy", "static"):
    s = summary["main"][p]
    print(p, "| succ", fmt(s["success"]), "| deliv", fmt(s["delivered_frac"]), "| TTA", fmt(s["time_to_aid"]),
          "| rep_lat", fmt(s["report_latency"]), "| lost(avoidable)", fmt(s["agents_lost_non_injected"]),
          "| lost(all)", fmt(s["agents_lost"]), "| churn", fmt(s["churn"]), "| energy", fmt(s["energy"]), "| ms", fmt(s["wall_ms"]))
print("paired concord-greedy:", {k: fmt(v) for k, v in paired.items()})
print("=== STRESS ===")
for k in range(7):
    row = []
    for p in ("concord", "greedy", "static"):
        s = summary["stress"][k][p]
        row.append(f"{p}: succ {s['success'][0]:.2f} deliv {s['delivered_frac'][0]:.2f} tta {s['time_to_aid'][0]:.0f} lostA {s['agents_lost_non_injected'][0]:.2f}")
    print(k, " | ".join(row))
print("=== ABLATION ===")
for name, s in summary["ablation"].items():
    print(f"{name:24s} succ {s['success'][0]:.3f} deliv {s['delivered_frac'][0]:.3f} tta {s['time_to_aid'][0]:.1f} rep {s['report_latency'][0]:.1f} lostA {s['agents_lost_non_injected'][0]:.3f} churn {s['churn'][0]:.2f} energy {s['energy'][0]:.0f}")
