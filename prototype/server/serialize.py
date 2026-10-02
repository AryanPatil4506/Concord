"""Engine state -> JSON for the console."""
from __future__ import annotations

import numpy as np

import concord_sim as cs

KIND_LABEL = {"scout": "Scout drone", "cargo": "Cargo drone", "rover": "Rover (UGV)", "relay": "Relay drone"}
EVENT_LABEL = {
    "agent_fail": "Agent hardware failure",
    "battery_drain": "Sudden battery drain",
    "bridge_collapse": "Bridge collapse",
    "comm_blackout": "Comm blackout",
    "storm": "Storm cell",
    "new_target": "Emergency call (new survivor)",
}


def _xy(p):
    return [int(p[0]), int(p[1])]


def static_info(w):
    return dict(
        grid=dict(w=cs.W, h=cs.H),
        base=_xy(cs.BASE),
        base_comm=cs.BASE_COMM,
        sectors={k: dict(x0=v[0], x1=v[1], y0=v[2], y1=v[3]) for k, v in cs.SECTORS.items()},
        tmax=w.tmax,
        seed=w.seed,
        fleet=[dict(id=a.id, kind=a.kind, kind_label=KIND_LABEL[a.kind], caps=list(a.caps), speed=a.speed,
                    battery=a.cap, comm=a.comm, kits=a.kit_cap, aerial=a.aerial, sensor=a.sensor)
               for a in w.agents],
        bridges=[[_xy(c) for c in cells] for cells in w.bridges],
        storm_hazard=cs.STORM_HAZARD,
    )


def terrain(w):
    return w.terr.astype(int).tolist()


def dead_cells(w):
    ys, xs = np.nonzero(w.dead)
    return [[int(x), int(y)] for x, y in zip(xs, ys)]


def bridge_state(w):
    return [all(w.terr[y, x] == cs.LAND for (x, y) in cells) for cells in w.bridges]


def item_label(w, it):
    if it == "BASE":
        return "Return to base · recharge / reload", _xy(cs.BASE)
    if isinstance(it, tuple):
        kind, cell = it
        return {"REPORT": f"Detour to reconnect at {tuple(cell)} · report finding",
                "STATION": f"Hold relay station {tuple(cell)}",
                "HOME": "Return to standby at base"}.get(kind, kind), _xy(cell)
    tk = w.tasks[it]
    return tk.label or tk.id, _xy(tk.pos)


def activity(w, a):
    if not a.alive:
        return f"Lost · {a.lost_why} at t={a.lost_t}"
    if a.status == "charging":
        return "Charging at base"
    if a.busy > 0 and a.plan:
        lab, _ = item_label(w, a.plan[0])
        return f"On task · {lab}"
    if not a.plan:
        return "Standby at base" if a.pos == cs.BASE else "Holding position"
    it = a.plan[0]
    if isinstance(it, tuple) and it[0] == "STATION":
        return f"Holding relay station {tuple(it[1])}" if a.pos == it[1] else f"Moving to relay station {tuple(it[1])}"
    lab, _ = item_label(w, it)
    return f"En route · {lab}"


def agent_state(w, a, conn):
    plan = [dict(label=lab, pos=pos, task=(it if isinstance(it, str) and it != "BASE" else None))
            for it in a.plan[:8] for (lab, pos) in [item_label(w, it)]]
    route = []
    for it in a.plan[:4]:
        route.append(item_label(w, it)[1])
    return dict(
        id=a.id, kind=a.kind, pos=_xy(a.pos), batt=round(max(0.0, a.batt) / a.cap, 4), alive=a.alive,
        conn=a.alive and a.id in conn, status=a.status, busy=a.busy, kits=a.kits, kit_cap=a.kit_cap,
        activity=activity(w, a), plan=plan, route=route,
        queued=len(a.outbox), queued_critical=sum(1 for m in a.outbox if m[0] >= 3),
        energy=round(a.energy_used, 1), lost_t=a.lost_t, lost_why=a.lost_why,
        storm_exposed=bool(a.alive and a.aerial and w.hazard[a.pos[1], a.pos[0]] > 0),
    )


def survivor_state(w, s):
    tk = w.tasks.get(f"DL-{s.sid}")
    return dict(sid=s.sid, pos=_xy(s.pos), appear_t=s.appear_t, detected_t=s.detected_t, reported_t=s.reported_t,
                delivered_t=s.delivered_t, by_call=s.by_call,
                assignee=(tk.assignee if tk is not None and tk.status == "assigned" else None),
                sector=cs.sector_of(s.pos))


def live_metrics(w, decisions):
    surv = w.survivors
    delivered = [s for s in surv if s.delivered_t is not None]
    reported = [s for s in surv if s.reported_t is not None]
    detected = [s for s in surv if s.detected_t is not None]
    rep_lat = [s.reported_t - s.detected_t for s in reported if not s.by_call]
    surveys = [t for t in w.tasks.values() if t.kind == "survey"]
    lost = [a for a in w.agents if not a.alive]
    return dict(
        aided=len(delivered), awaiting=len(reported) - len(delivered), found=len(detected),
        unreported=len(detected) - len(reported), total=len(surv),
        mean_tta=(round(float(np.mean([s.delivered_t - s.appear_t for s in delivered])), 1) if delivered else None),
        report_latency=(round(float(np.mean(rep_lat)), 2) if rep_lat else None),
        agents_up=sum(1 for a in w.agents if a.alive), agents_total=len(w.agents),
        lost_avoidable=sum(1 for a in lost if a.lost_why != "hardware failure"), lost_injected=sum(
            1 for a in lost if a.lost_why == "hardware failure"),
        surveyed=sum(1 for t in surveys if t.status == "done"), surveys_total=len(surveys),
        energy=round(sum(a.energy_used for a in w.agents), 1), reassignments=w.churn,
        disruptions=len([e for e in w.events if e[0] < w.t]), decisions=decisions,
        connected=sum(1 for a in w.agents if a.alive and a.connected),
    )


def task_labels(w):
    return {tid: (t.label or tid) for tid, t in w.tasks.items()}


def log_entry(w, i, e):
    out = dict(i=i, t=e["t"], kind=e["kind"], text=e["text"])
    for k in ("agent", "sid"):
        if k in e:
            out[k] = e[k]
    if "res" in e:
        rows = []
        for (tid, aid, score, opt, t_done, alts) in e["res"]:
            rows.append(dict(task=tid, label=w.tasks[tid].label if tid in w.tasks else tid, winner=aid,
                             bid=score, via_base=(opt == "via_base"), eta=t_done,
                             others=[dict(agent=o, bid=b) for (o, b) in (alts or [])]))
        out["bids"] = rows
    if "released" in e and e["released"]:
        out["released"] = [w.tasks[t].label if t in w.tasks else t for t in e["released"]]
    return out


def tick_state(w, decisions):
    conn = w.connected_nodes()
    relay = next(a for a in w.agents if a.kind == "relay")
    return dict(
        t=w.t,
        agents=[agent_state(w, a, conn) for a in w.agents],
        survivors=[survivor_state(w, s) for s in w.survivors],
        surveys=[dict(id=t.id, pos=_xy(t.pos), status=t.status, assignee=t.assignee)
                 for t in w.tasks.values() if t.kind == "survey"],
        storm=(dict(cx=w.storm[0], cy=w.storm[1], r=w.storm[2], t_end=w.storm[3]) if w.storm else None),
        relay_station=(_xy(relay.plan[0][1]) if relay.plan and isinstance(relay.plan[0], tuple) else None),
        metrics=live_metrics(w, decisions),
    )
