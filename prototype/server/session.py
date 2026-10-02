"""A live mission: the engine stepped in real time with injected disruptions and escalations."""
from __future__ import annotations

import asyncio
import logging
import time

import numpy as np

import concord_sim as cs
import storyboard as sb
from . import forecasting as fc
from . import serialize as ser

log = logging.getLogger("concord.session")

ESCALATE_BELOW = 0.6
DECISION_TIMEOUT_S = 30
INJECT_COOLDOWN_S = 2.0
FORECAST_EVERY = 10
BASE_TPS = 5.0          # ticks per second at 1x

SCENARIOS = {
    "storyboard": dict(
        title="Flood SAR · storyboard",
        blurb="Seed 6 · 6 survivors · 200 ticks · 5 scripted disruptions revealed as they happen "
              "(the mission in the demo video).",
        seed=6, n_surv=sb.NSURV, tmax=sb.TMAX),
    "random": dict(
        title="Flood SAR · random scenario",
        blurb="5 survivors · 320 ticks · disruptions drawn from the benchmark prior (unknown in advance).",
        seed=None, n_surv=5, tmax=cs.T_MAX),
    "sandbox": dict(
        title="Flood SAR · sandbox",
        blurb="6 survivors · 240 ticks · no scheduled disruptions — inject them yourself.",
        seed=None, n_surv=6, tmax=240),
}


def _events_for(scenario, seed):
    if scenario == "storyboard":
        return sb.script_events((25, 21), (33, 21), None)
    if scenario == "sandbox":
        return []
    return None  # random: World draws them from the prior


def _run_baseline(seed, n_surv, tmax, events, policy, flags):
    w = cs.World(seed, events=events, n_surv=n_surv, tmax=tmax)
    m, _ = cs.run_mission(seed, policy, world=w, **flags)
    return m


class MissionSession:
    def __init__(self, broadcast, scenario="storyboard", seed=None, objective=""):
        self.broadcast = broadcast
        spec = SCENARIOS[scenario]
        self.scenario = scenario
        self.seed = int(spec["seed"] if spec["seed"] is not None else (seed if seed is not None else
                                                                       np.random.default_rng().integers(1, 10_000)))
        self.n_surv, self.tmax = spec["n_surv"], spec["tmax"]
        self.objective = objective
        self.world = cs.World(self.seed, events=_events_for(scenario, self.seed), record=True,
                              n_surv=self.n_surv, tmax=self.tmax)
        self.events0 = list(self.world.events)
        self.policy = cs.make_policy("concord")
        self.policy.init(self.world)
        self.flags = {}                    # operator-approved policy overrides (also used by forecasts)
        self.phase = "paused"              # running | paused | assessing | escalation | complete
        self.tps = BASE_TPS
        self.timeline = []                 # [(t, p, kind)]
        self.escalation = None
        self.escalations = []
        self.decisions = 0
        self.injected = []
        self.last_inject = 0.0
        self.log_sent = 0
        self.summary = None
        self._sent_tver = self._sent_dead = None
        self._task = None
        self._timeout_task = None
        self._forecast_tasks = set()
        self._wake = asyncio.Event()
        self._lock = asyncio.Lock()

    def start(self):
        self._task = asyncio.create_task(self._loop())
        self._schedule_forecast()

    async def stop(self):
        for t in [self._task, self._timeout_task, *self._forecast_tasks]:
            if t:
                t.cancel()

    async def _loop(self):
        while True:
            if self.phase == "running":
                t0 = time.perf_counter()
                try:
                    await self._tick()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("tick failed at t=%s", self.world.t)
                    await self._set_phase("paused")
                    await self.broadcast(dict(type="notice", level="error",
                                              message="The engine hit an error and paused the mission."))
                await asyncio.sleep(max(0.0, 1.0 / self.tps - (time.perf_counter() - t0)))
            else:
                self._wake.clear()
                await self._wake.wait()

    def _set_phase(self, phase, **info):
        self.phase = phase
        self._wake.set()
        return self.broadcast(dict(type="phase", phase=phase, **info))

    def full_state(self):
        w = self.world
        self.log_sent = len(w.log)
        self._sent_tver, self._sent_dead = w.tver, int(w.dead.sum())
        return dict(
            type="mission", scenario=self.scenario, scenario_title=SCENARIOS[self.scenario]["title"],
            objective=self.objective, static=ser.static_info(w), terrain=ser.terrain(w), dead=ser.dead_cells(w),
            bridges=ser.bridge_state(w), labels=ser.task_labels(w), phase=self.phase, tps=self.tps,
            base_tps=BASE_TPS, state=ser.tick_state(w, self.decisions),
            log=[ser.log_entry(w, i, e) for i, e in enumerate(w.log)],
            timeline=[dict(t=t, p=p, kind=k) for (t, p, k) in self.timeline],
            escalation=self._escalation_public(), injected=self.injected, summary=self.summary,
            escalate_below=ESCALATE_BELOW, cooldown_s=INJECT_COOLDOWN_S,
            scheduled=len(self.events0),
        )

    def _tick_message(self):
        w = self.world
        msg = dict(type="tick", state=ser.tick_state(w, self.decisions),
                   log=[ser.log_entry(w, i, e) for i, e in enumerate(w.log[self.log_sent:], start=self.log_sent)])
        self.log_sent = len(w.log)
        if w.tver != self._sent_tver:
            self._sent_tver = w.tver
            msg["terrain"], msg["bridges"] = ser.terrain(w), ser.bridge_state(w)
        dsum = int(w.dead.sum())
        if dsum != self._sent_dead:
            self._sent_dead = dsum
            msg["dead"] = ser.dead_cells(w)
        if any(e.get("kind") == "event" and "new survivor" in e["text"] for e in msg["log"]) or any(
                e.get("kind") == "report" for e in msg["log"]):
            msg["labels"] = ser.task_labels(w)
        return msg

    async def _tick(self):
        async with self._lock:
            await self._tick_locked()

    async def _tick_locked(self):
        w = self.world
        if w.finished():
            await self._complete()
            return
        if w.t % FORECAST_EVERY == 0 and w.t > 0:
            self._schedule_forecast()
        disruptions = [e for e in w.events if e[0] == w.t]
        cs.step(w, self.policy)
        await self.broadcast(self._tick_message())
        if disruptions:
            await self._assess(disruptions)
        elif w.finished():
            await self._complete()

    def _schedule_forecast(self):
        if self._forecast_tasks:  # skip rather than queue up on small machines
            return
        w = self.world
        snap = fc.portable(w)
        t = w.t
        loop = asyncio.get_running_loop()

        async def run():
            p = await fc.forecast(loop, snap, seed=1, flags=self.flags)
            self.timeline.append((t, p, "periodic"))
            await self.broadcast(dict(type="forecast", t=t, p=p, kind="periodic"))

        task = asyncio.create_task(run())
        self._forecast_tasks.add(task)
        task.add_done_callback(self._forecast_tasks.discard)

    async def _assess(self, disruptions):
        w = self.world
        kinds = ", ".join(ser.EVENT_LABEL.get(e[1], e[1]).lower() for e in disruptions)
        prev = self.phase
        await self._set_phase("assessing", reason=f"Re-forecasting after {kinds}")
        loop = asyncio.get_running_loop()
        p_now = await fc.forecast(loop, w, seed=2, flags=self.flags)
        self.timeline.append((w.t, p_now, "assess"))
        await self.broadcast(dict(type="forecast", t=w.t, p=p_now, kind="assess"))
        if p_now >= ESCALATE_BELOW:
            await self._set_phase(prev if prev != "assessing" else "running")
            if w.finished():
                await self._complete()
            return
        await self._escalate(p_now, disruptions)

    def _options(self):
        w = self.world
        alive = {a.kind for a in w.agents if a.alive}
        ro = dict(self.flags.get("risk_override", {}))
        opts = [dict(key="A", title="Hold the current plan",
                     detail="Keep every safety limit; drones stay out of hazards until conditions change.",
                     flags=dict(self.flags), irreversible=False)]
        if w.storm is not None and "cargo" in alive and ro.get("cargo", 0) < 1.0:
            cargo = next(a.id for a in w.agents if a.kind == "cargo" and a.alive)
            opts.append(dict(key="B", title=f"Fly {cargo} through the storm now",
                             detail=f"Lifts the storm-risk ceiling for {cargo}. Risk of losing the airframe "
                                    f"({cs.STORM_HAZARD:.0%} per tick inside the cell).",
                             flags={**self.flags, "risk_override": {**ro, "cargo": 1.0}}, irreversible=True))
        undetected = any(s.detected_t is None for s in w.survivors)
        if w.storm is not None and "scout" in alive and ro.get("scout", 0) < 1.0 and undetected:
            opts.append(dict(key=chr(ord("A") + len(opts)), title="Send all drones through the storm",
                             detail="Lifts the storm-risk ceiling for scouts and the cargo drone. Fastest search, "
                                    "highest exposure.",
                             flags={**self.flags, "risk_override": {**ro, "cargo": 1.0, "scout": 1.0}},
                             irreversible=True))
        if self.flags.get("reserve", True):
            opts.append(dict(key=chr(ord("A") + len(opts)), title="Relax the battery-reserve invariant",
                             detail="Allow sorties that end without the 15% return reserve. More reach, "
                                    "risk of aborted sorties.",
                             flags={**self.flags, "reserve": False}, irreversible=False))
        return opts

    async def _escalate(self, p_now, disruptions):
        w = self.world
        loop = asyncio.get_running_loop()
        opts = self._options()
        opts[0]["p"] = p_now
        ps = await asyncio.gather(*[fc.forecast(loop, w, seed=7, flags=o["flags"], force_trigger="operator")
                                    for o in opts[1:]])
        for o, p in zip(opts[1:], ps):
            o["p"] = p
        best = max(opts, key=lambda o: o["p"])          # ties keep the earliest (most conservative) option
        rec = best["key"]
        pending = [s for s in w.survivors if s.reported_t is not None and s.delivered_t is None]
        undetected = sum(1 for s in w.survivors if s.detected_t is None)
        carriers = [a.id for a in w.agents if a.alive and "payload" in a.caps]
        cause = "; ".join(self._describe(e) for e in disruptions)
        parts = [f"{cause}."]
        parts.append(f"Payload carriers left: {', '.join(carriers) if carriers else 'none'}.")
        if pending:
            secs = sorted({cs.sector_of(s.pos) or '—' for s in pending})
            parts.append(f"{len(pending)} survivor{'s' if len(pending) != 1 else ''} "
                         f"({', '.join(s.sid for s in pending)}) await aid in sector{'s' if len(secs) > 1 else ''} "
                         f"{', '.join(secs)}" + (" under a storm cell." if w.storm else "."))
        if undetected:
            parts.append("Survey is still in progress.")
        parts.append(f"Forecast {p_now:.0%} is below the {ESCALATE_BELOW:.0%} threshold.")
        self.escalation = dict(id=len(self.escalations) + 1, t=w.t, p_now=p_now, situation=" ".join(parts),
                               options=opts, recommend=rec, deadline=time.time() + DECISION_TIMEOUT_S,
                               timeout_s=DECISION_TIMEOUT_S, k=fc.K_DEFAULT)
        w.log.append(dict(t=w.t, kind="escalation",
                          text=f"ESCALATION: P(success) {p_now:.0%} < {ESCALATE_BELOW:.0%} -> operator card; "
                               f"recommended {rec}"))
        await self.broadcast(self._tick_message())
        await self._set_phase("escalation", escalation=self._escalation_public())
        self._timeout_task = asyncio.create_task(self._decision_timeout(self.escalation["id"]))

    def _describe(self, e):
        t, kind, prm = e
        if kind == "agent_fail":
            return f"{self.world.agents[prm['idx']].id} suffered a hardware failure at t={t}"
        if kind == "battery_drain":
            return f"{self.world.agents[prm['idx']].id} lost battery to a cell fault at t={t}"
        if kind == "bridge_collapse":
            return f"The {'north' if prm['bridge'] == 0 else 'south'} bridge collapsed at t={t}"
        if kind == "storm":
            return f"A storm cell formed over sector {cs.sector_of(prm['center']) or 'the west bank'} at t={t}"
        if kind == "comm_blackout":
            return f"Comms blacked out around {tuple(prm['center'])} at t={t}"
        return f"An emergency call reported a new survivor at t={t}"

    def _escalation_public(self):
        if not self.escalation:
            return None
        e = dict(self.escalation)
        e["options"] = [{k: v for k, v in o.items() if k != "flags"} for o in e["options"]]
        e["remaining_s"] = max(0, round(e["deadline"] - time.time()))
        e.pop("deadline")
        return e

    async def _decision_timeout(self, esc_id):
        await asyncio.sleep(DECISION_TIMEOUT_S)
        if self.escalation and self.escalation["id"] == esc_id:
            await self.decide(self.escalation["recommend"], auto=True)

    async def decide(self, key, auto=False):
        esc = self.escalation
        if not esc or self.phase != "escalation":
            return
        opt = next((o for o in esc["options"] if o["key"] == key), None)
        if opt is None:
            return
        if self._timeout_task and not auto:
            self._timeout_task.cancel()
        w = self.world
        self.flags = dict(opt["flags"])
        self.policy.risk_override = dict(self.flags.get("risk_override", {}))
        self.policy.reserve = self.flags.get("reserve", True)
        if key != "A":
            w.pending_triggers.add("operator")
        self.decisions += 1
        how = "Safe default applied after 30 s without a response" if auto else "Operator approved"
        w.log.append(dict(t=w.t, kind="operator",
                          text=f"{how}: option {key} — {opt['title']} (P(success) {opt['p']:.0%})"))
        self.escalations.append(dict(t=esc["t"], p_now=esc["p_now"], chosen=key, recommended=esc["recommend"],
                                     auto=auto, title=opt["title"], p=opt["p"]))
        self.escalation = None
        await self.broadcast(dict(type="escalation_resolved", key=key, auto=auto))
        await self.broadcast(self._tick_message())
        await self._set_phase("running")

    async def play(self):
        if self.phase == "paused":
            await self._set_phase("running")

    async def pause(self):
        if self.phase == "running":
            await self._set_phase("paused")

    async def step_once(self):
        if self.phase == "paused":
            await self._tick()

    async def set_speed(self, mult):
        self.tps = BASE_TPS * max(0.25, min(8.0, float(mult)))
        await self.broadcast(dict(type="speed", tps=self.tps))

    async def inject(self, kind, params):
        w = self.world
        if self.phase in ("assessing", "escalation", "complete"):
            return "The mission is not accepting disruptions right now."
        now = time.time()
        if now - self.last_inject < INJECT_COOLDOWN_S:
            return "One disruption every 2 seconds — try again in a moment."
        if any(e[0] == w.t and e[1] == kind for e in w.events):
            return "That disruption is already queued for this tick."
        rng = np.random.default_rng(abs(hash((self.seed, w.t, kind))) % (2 ** 32))
        params = dict(params or {})
        if kind in ("agent_fail", "battery_drain"):
            ag = w.by_id.get(params.get("agent"))
            if ag is None or not ag.alive:
                return "Pick an operational agent."
            prm = {"idx": ag.idx}
            if kind == "battery_drain":
                prm["frac"] = 0.45
        elif kind == "bridge_collapse":
            intact = [i for i, cells in enumerate(w.bridges) if all(w.terr[y, x] == cs.LAND for (x, y) in cells)]
            if not intact:
                return "Both bridges are already down."
            b = params.get("bridge")
            prm = {"bridge": b if b in intact else int(rng.choice(intact))}
        elif kind in ("comm_blackout", "storm", "new_target"):
            if kind == "storm" and w.storm is not None:
                return "A storm cell is already active."
            pos = params.get("pos")
            if pos is None:
                s = cs.SECTORS["ABCD"[int(rng.integers(0, 4))]]
                pos = (int(rng.integers(s[0] + 2, s[1] - 2)), int(rng.integers(s[2] + 2, s[3] - 2)))
            x, y = int(np.clip(pos[0], 0, cs.W - 1)), int(np.clip(pos[1], 0, cs.H - 1))
            if kind == "new_target":
                if w.terr[y, x] != cs.LAND:
                    ys, xs = np.nonzero(w.terr == cs.LAND)
                    k = int(np.argmin(np.maximum(np.abs(xs - x), np.abs(ys - y))))
                    x, y = int(xs[k]), int(ys[k])
                prm = {"pos": (x, y)}
            elif kind == "storm":
                prm = {"center": (x, y), "r": 5.5, "dur": 70}
            else:
                prm = {"center": (x, y), "r": 4.0}
        else:
            return "Unknown disruption."
        self.last_inject = now
        w.events.append((w.t, kind, prm))
        rec = dict(t=w.t, kind=kind, label=ser.EVENT_LABEL[kind],
                   params={k: (list(v) if isinstance(v, tuple) else v) for k, v in prm.items()},
                   agent=params.get("agent"))
        self.injected.append(rec)
        await self.broadcast(dict(type="injected", event=rec))
        if self.phase == "paused":
            await self._tick()
        return None

    async def _complete(self):
        if self.phase == "complete":
            return
        w = self.world
        m = cs.metrics(w)
        await self._set_phase("complete")
        loop = asyncio.get_running_loop()
        events = list(w.events)
        runs = [("greedy", {}), ("static", {})]
        if self.decisions:
            runs.insert(0, ("concord", {}))
        res = await asyncio.gather(*[loop.run_in_executor(fc.pool(), _run_baseline, self.seed, self.n_surv,
                                                          self.tmax, events, pol, fl) for pol, fl in runs])
        baselines = []
        for (pol, _), r in zip(runs, res):
            name = {"concord": "CONCORD without the operator decision", "greedy": "Greedy dispatch",
                    "static": "Static plan"}[pol]
            baselines.append(dict(policy=pol, name=name, metrics=r))
        self.summary = dict(
            metrics=m, baselines=baselines, escalations=self.escalations, injected=self.injected,
            disruptions=[dict(t=e[0], kind=e[1], label=ser.EVENT_LABEL[e[1]]) for e in sorted(w.events)
                         if e[0] < w.t],
            last_aid_t=max((s.delivered_t for s in w.survivors if s.delivered_t is not None), default=None),
            replay=dict(seed=self.seed, scenario=self.scenario, n_surv=self.n_surv, tmax=self.tmax,
                        events=[[e[0], e[1], {k: (list(v) if isinstance(v, tuple) else v) for k, v in e[2].items()}]
                                for e in sorted(events)],
                        decisions=[dict(t=x["t"], option=x["chosen"], auto=x["auto"]) for x in self.escalations]),
        )
        await self.broadcast(dict(type="summary", summary=self.summary))
