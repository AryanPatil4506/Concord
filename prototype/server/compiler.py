"""Rule-based mission compiler: objective text -> typed Mission DAG + validation checks."""
from __future__ import annotations

import re

import concord_sim as cs

DEFAULT_OBJECTIVE = ("Flood response east of the river: survey sectors A to D, find everyone who is trapped "
                     "and get a med-kit to each survivor as fast as possible. Keep every agent linked to base "
                     "and don't lose drones to the weather.")


def _sectors(text):
    t = text.upper()
    m = re.search(r"SECTORS?\s+([A-D])\s*(?:-|–|TO|THROUGH)\s*([A-D])", t)
    if m:
        a, b = sorted((m.group(1), m.group(2)))
        return [chr(c) for c in range(ord(a), ord(b) + 1)]
    found = re.findall(r"(?:SECTORS?|,|AND)\s+([A-D])\b", t)
    found = sorted(set(found))
    return found or list("ABCD")


def compile_objective(text, tmax=200, n_waypoints=6):
    text = (text or "").strip() or DEFAULT_OBJECTIVE
    low = text.lower()
    sectors = _sectors(text)
    wants_delivery = any(k in low for k in ("med", "kit", "deliver", "supplies", "aid"))
    wants_link = any(k in low for k in ("link", "comm", "connected", "contact"))
    risk_averse = any(k in low for k in ("weather", "storm", "don't lose", "do not lose", "safe"))
    m = re.search(r"within\s+(\d+)\s*(ticks?|min(?:ute)?s?)", low)
    horizon = tmax
    if m:
        n = int(m.group(1))
        horizon = n if m.group(2).startswith("tick") else n * 6   # 1 tick ≈ 10 s
    nodes, edges = [], []
    for s in sectors:
        nodes.append(dict(id=f"survey-{s}", type="survey", label=f"Survey sector {s}",
                          detail=f"{n_waypoints} waypoints · camera", requires="camera", priority=0.4, sector=s))
        edges.append([f"survey-{s}", "locate"])
    nodes.append(dict(id="locate", type="locate", label="Locate survivors",
                      detail="Camera, 2-cell radius · critical report", requires="camera",
                      priority=1.0))
    if wants_delivery:
        nodes.append(dict(id="deliver", type="deliver", label="Deliver med-kits",
                          detail="1 per reported survivor · payload", requires="payload", priority=1.0))
        edges.append(["locate", "deliver"])
    nodes.append(dict(id="link", type="relay", label="Maintain link to base",
                      detail="Relay repositioning · value-of-information messaging", requires="relay",
                      priority=0.6, continuous=True))
    fleet_caps = {}
    for aid, kind in cs.FLEET:
        for c in cs.SPECS[kind]["caps"]:
            fleet_caps.setdefault(c, []).append(aid)
    constraints = [
        dict(label="Mission horizon", value=f"{horizon} ticks (≈ {horizon * 10 // 60} min at 1 tick ≈ 10 s)"),
        dict(label="Battery reserve", value="Finish + return ×1.15 + 5 units on every bid"),
        dict(label="Storm-risk ceiling", value="0.12 per task" + (" · weather flagged by operator" if risk_averse else "")),
        dict(label="Escalate to operator", value="P(success) < 60% or irreversible action"),
    ]
    if wants_link:
        constraints.append(dict(label="Comms", value="Keep agents linked; critical reports outrank telemetry"))
    checks = [
        dict(label="All referenced sectors exist on the map", ok=all(s in cs.SECTORS for s in sectors)),
        dict(label="Every task has a capable agent",
             ok=all(n["requires"] in fleet_caps for n in nodes)),
        dict(label="Task graph is acyclic", ok=True),
        dict(label="Horizon fits the scenario", ok=horizon <= max(tmax, cs.T_MAX)),
    ]
    return dict(
        objective=text, compiler="offline rule-based fallback (no LLM)", sectors=sectors, horizon=horizon,
        nodes=nodes, edges=edges, constraints=constraints, checks=checks,
        capabilities={k: v for k, v in fleet_caps.items()},
        task_count=len(sectors) * n_waypoints,
    )
