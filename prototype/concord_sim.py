#!/usr/bin/env python3
"""
CONCORD v0 - headless mission-orchestration simulator (prototype).

A deliberately simple 2D grid world (no physics) used to test mission-level
decision making for a heterogeneous swarm:

    2 x Scout drone  (aerial, camera, fast, short battery, weather-sensitive)
    1 x Cargo drone  (aerial, carries 1 med-kit, weather-sensitive)
    1 x Rover (UGV)  (ground, carries 3 med-kits, slow, long battery, terrain-bound)
    1 x Relay drone  (aerial, long comm range, no sensors)

Mission: survey sectors A-D, find hidden survivors, deliver a med-kit to each
survivor before T_MAX, keep a communication link to base.

Disruptions (seeded, random per scenario): agent failure, sudden battery drain,
bridge collapse, comm blackout zone, storm cell, new high-priority target.

Policies compared
-----------------
concord : event-driven auction re-planning (CBBA-style sequential auction with
          time-discounted rewards), battery-reserve invariant, risk-aware routing,
          dynamic relay placement, value-of-information (VoI) messaging, hysteresis.
greedy  : nearest capable idle agent takes the nearest open task (reactive
          dispatch), smart return-to-home, FIFO messaging, relay parked at a
          fixed station.
static  : one-shot initial allocation, agents execute their list with smart
          return-to-home, new tasks appended to the nearest capable agent, no
          re-allocation after failures, fixed relay, FIFO messaging.

All randomness is seeded; run_mission(seed, policy) is fully reproducible.
Common random numbers are used across policies so comparisons are paired.
"""
from __future__ import annotations

import math
import heapq
from collections import deque

import numpy as np

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
W, H = 40, 28
BASE = (2, 14)
T_MAX = 320
BASE_COMM = 14.0
LAND, WATER, BUILDING = 0, 1, 2
INF = float("inf")
NEI8 = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
STORM_HAZARD = 0.04          # per-tick loss probability for an aerial agent inside a storm cell
MSG_BANDWIDTH = 2            # messages per tick an agent can uplink when connected
RTH_FACTOR, RTH_MARGIN = 1.15, 5.0   # smart return-to-home: batt < dist*rate*1.15 + 5

SPECS = {
    "scout": dict(aerial=True, caps=("camera",), speed=2.0, battery=110.0, e_move=1.0,
                  e_idle=0.3, comm=7.0, sensor=2, kits=0, charge=6.0),
    "cargo": dict(aerial=True, caps=("payload",), speed=1.5, battery=120.0, e_move=1.2,
                  e_idle=0.4, comm=7.0, sensor=0, kits=1, charge=6.0),
    "rover": dict(aerial=False, caps=("payload",), speed=1.0, battery=500.0, e_move=0.8,
                  e_idle=0.0, comm=6.0, sensor=0, kits=3, charge=20.0),
    "relay": dict(aerial=True, caps=("relay",), speed=1.5, battery=220.0, e_move=0.8,
                  e_idle=0.35, comm=16.0, sensor=0, kits=0, charge=8.0),
}
FLEET = (("Scout-1", "scout"), ("Scout-2", "scout"), ("Cargo-1", "cargo"),
         ("Rover-1", "rover"), ("Relay-1", "relay"))
SECTORS = {"A": (20, 30, 0, 14), "B": (30, 40, 0, 14), "C": (20, 30, 14, 28), "D": (30, 40, 14, 28)}
FIXED_RELAY_STATION = (16, 14)


def cheb(p, q):
    return max(abs(p[0] - q[0]), abs(p[1] - q[1]))


def eucl(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def sgn(v):
    return (v > 0) - (v < 0)


def disc_mask(cx, cy, r):
    yy, xx = np.mgrid[0:H, 0:W]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r


def sector_of(pos):
    for name, (x0, x1, y0, y1) in SECTORS.items():
        if x0 <= pos[0] < x1 and y0 <= pos[1] < y1:
            return name
    return None


# ----------------------------------------------------------------------------
# Scenario generation
# ----------------------------------------------------------------------------
def gen_terrain(rng):
    terr = np.zeros((H, W), np.int8)
    phase = rng.uniform(0, 2 * np.pi)
    river_x = {}
    for y in range(H):
        cx = 17 + int(round(1.6 * np.sin(y / 4.5 + phase)))
        river_x[y] = cx
        terr[y, cx - 1:cx + 2] = WATER
    bridges = []
    for by in (int(rng.integers(5, 9)), int(rng.integers(19, 23))):
        cells = [(x, by) for x in range(river_x[by] - 1, river_x[by] + 2)]
        for (x, y) in cells:
            terr[y, x] = LAND
        bridges.append(cells)
    # flood pockets on the east bank
    for _ in range(3):
        cx, cy = int(rng.integers(23, 38)), int(rng.integers(2, 26))
        r = rng.uniform(1.4, 2.6)
        m = disc_mask(cx, cy, r)
        m[:, :21] = False
        terr[m] = WATER
    # buildings (impassable for ground agents, overflown by aerial agents)
    for _ in range(18):
        bw, bh = int(rng.integers(2, 4)), int(rng.integers(2, 4))
        x0, y0 = int(rng.integers(4, W - bw)), int(rng.integers(0, H - bh))
        if abs(x0 - BASE[0]) < 5 and abs(y0 - BASE[1]) < 5:
            continue
        if (terr[y0:y0 + bh, x0:x0 + bw] != LAND).any():
            continue
        if any(abs(x - river_x[yy]) <= 3 for yy in range(y0, y0 + bh) for x in range(x0, x0 + bw)):
            continue
        terr[y0:y0 + bh, x0:x0 + bw] = BUILDING
    return terr, bridges, river_x


def sample_land_in_sectors(rng, terr, n, avoid=(), min_sep=3):
    pts = []
    tries = 0
    while len(pts) < n and tries < 5000:
        tries += 1
        x, y = int(rng.integers(20, 40)), int(rng.integers(0, 28))
        if terr[y, x] != LAND:
            continue
        if any(cheb((x, y), p) < min_sep for p in list(pts) + list(avoid)):
            continue
        pts.append((x, y))
    return pts


EVENT_PRIOR = {  # type: (probability, t_lo, t_hi)
    "agent_fail": (0.6, 40, 200),
    "battery_drain": (0.6, 40, 200),
    "bridge_collapse": (0.5, 30, 180),
    "comm_blackout": (0.5, 30, 180),
    "storm": (0.5, 40, 170),
    "new_target": (0.6, 40, 220),
}


def gen_events(rng, terr, t_from=0, exclude=()):
    """Sample a disruption schedule from the prior (each type at most once)."""
    ev = []
    for kind, (p, lo, hi) in EVENT_PRIOR.items():
        draw = rng.random()
        t = int(rng.integers(lo, hi))
        params = {}
        if kind == "agent_fail":
            params = {"idx": int(rng.integers(0, len(FLEET)))}
        elif kind == "battery_drain":
            params = {"idx": int(rng.choice([0, 1, 2, 4])), "frac": 0.45}
        elif kind == "bridge_collapse":
            params = {"bridge": int(rng.integers(0, 2))}
        elif kind == "comm_blackout":
            s = SECTORS["ABCD"[int(rng.integers(0, 4))]]
            params = {"center": (int(rng.integers(s[0] + 2, s[1] - 2)), int(rng.integers(s[2] + 2, s[3] - 2))), "r": 4.0}
        elif kind == "storm":
            s = SECTORS["ABCD"[int(rng.integers(0, 4))]]
            params = {"center": (int(rng.integers(s[0] + 1, s[1] - 1)), int(rng.integers(s[2] + 2, s[3] - 2))),
                      "r": 5.5, "dur": 70}
        elif kind == "new_target":
            pts = sample_land_in_sectors(rng, terr, 1)
            params = {"pos": pts[0] if pts else (35, 14)}
        if draw < p and t >= t_from and kind not in exclude:
            ev.append((t, kind, params))
    ev.sort(key=lambda e: e[0])
    return ev


def gen_events_k(rng, terr, k):
    """Exactly k distinct disruption types, times/params drawn from the prior windows."""
    full = []
    # draw every type deterministically (force inclusion), then keep a random subset of size k
    for kind, (p, lo, hi) in EVENT_PRIOR.items():
        sub = gen_events(np.random.default_rng(int(rng.integers(0, 2 ** 31))), terr)
        pool = [e for e in sub if e[1] == kind]
        if not pool:  # force it: re-draw until present
            for _ in range(50):
                sub = gen_events(np.random.default_rng(int(rng.integers(0, 2 ** 31))), terr)
                pool = [e for e in sub if e[1] == kind]
                if pool:
                    break
        if pool:
            full.append(pool[0])
    idx = rng.choice(len(full), size=min(k, len(full)), replace=False) if k > 0 else []
    ev = [full[i] for i in sorted(idx)]
    ev.sort(key=lambda e: e[0])
    return ev


# ----------------------------------------------------------------------------
# Entities
# ----------------------------------------------------------------------------
class Task:
    __slots__ = ("id", "kind", "pos", "prio", "req", "dur", "critical", "status", "assignee",
                 "release_t", "label", "sid")

    def __init__(self, tid, kind, pos, prio, req, dur, critical, release_t, label=None, sid=None):
        self.id, self.kind, self.pos, self.prio, self.req = tid, kind, pos, prio, req
        self.dur, self.critical, self.release_t, self.label, self.sid = dur, critical, release_t, label, sid
        self.status, self.assignee = "open", None

    def copy(self):
        t = Task(self.id, self.kind, self.pos, self.prio, self.req, self.dur, self.critical,
                 self.release_t, self.label, self.sid)
        t.status, t.assignee = self.status, self.assignee
        return t


class Survivor:
    __slots__ = ("sid", "pos", "appear_t", "detected_t", "reported_t", "delivered_t", "by_call")

    def __init__(self, sid, pos, appear_t=0, by_call=False):
        self.sid, self.pos, self.appear_t, self.by_call = sid, pos, appear_t, by_call
        self.detected_t = self.reported_t = self.delivered_t = None

    def copy(self):
        s = Survivor(self.sid, self.pos, self.appear_t, self.by_call)
        s.detected_t, s.reported_t, s.delivered_t = self.detected_t, self.reported_t, self.delivered_t
        return s


class Agent:
    __slots__ = ("id", "idx", "kind", "aerial", "caps", "speed", "cap", "batt", "e_move", "e_idle",
                 "comm", "sensor", "kit_cap", "kits", "charge", "pos", "status", "plan", "budget",
                 "busy", "outbox", "connected", "energy_used", "charge_target", "lost_t", "lost_why")

    def __init__(self, aid, idx, kind):
        s = SPECS[kind]
        self.id, self.idx, self.kind = aid, idx, kind
        self.aerial, self.caps, self.speed = s["aerial"], s["caps"], s["speed"]
        self.cap = self.batt = s["battery"]
        self.e_move, self.e_idle, self.comm, self.sensor = s["e_move"], s["e_idle"], s["comm"], s["sensor"]
        self.kit_cap = self.kits = s["kits"]
        self.charge = s["charge"]
        self.pos = BASE
        self.status = "active"          # active | charging | lost
        self.plan = []                  # items: task id (str) | 'BASE' | ('REPORT', cell) | ('STATION', cell)
        self.budget = 0.0
        self.busy = 0
        self.outbox = []                # [prio, tick, kind, payload]
        self.connected = True
        self.energy_used = 0.0
        self.charge_target = self.cap
        self.lost_t, self.lost_why = None, None

    def copy(self):
        a = Agent.__new__(Agent)
        for k in Agent.__slots__:
            setattr(a, k, getattr(self, k))
        a.plan = list(self.plan)
        a.outbox = [list(m) for m in self.outbox]
        return a

    def rate(self, kits=None):
        k = self.kits if kits is None else kits
        return self.e_move * (1.25 if (self.kind == "cargo" and k > 0) else 1.0)

    @property
    def alive(self):
        return self.status != "lost"


# ----------------------------------------------------------------------------
# World
# ----------------------------------------------------------------------------
class World:
    def __init__(self, seed, events=None, n_surv=5, record=False, tmax=T_MAX):
        self.seed = seed
        self.tmax = tmax
        rng = np.random.default_rng(seed)
        self.terr, self.bridges, self.river_x = gen_terrain(rng)
        self.dead = np.zeros((H, W), bool)
        s = SECTORS["ABCD"[int(rng.integers(0, 4))]]
        self.dead |= disc_mask(int(rng.integers(s[0] + 2, s[1] - 2)), int(rng.integers(s[2] + 3, s[3] - 3)), 3.0)
        self.hazard = np.zeros((H, W))
        self.storm = None               # (cx, cy, r, t_end)
        self.tver = 0
        self.sver = 0
        self.agents = [Agent(aid, i, kind) for i, (aid, kind) in enumerate(FLEET)]
        self.by_id = {a.id: a for a in self.agents}
        self.tasks = {}
        for name, (x0, x1, y0, y1) in SECTORS.items():
            k = 0
            for yy in range(y0 + 2, y1, 5):
                for xx in range(x0 + 2, x1, 5):
                    k += 1
                    tid = f"SV-{name}{k}"
                    self.tasks[tid] = Task(tid, "survey", (xx, yy), 0.4, "camera", 1, False, 0,
                                           label=f"Survey {name}{k}")
        pts = sample_land_in_sectors(rng, self.terr, n_surv, avoid=[BASE])
        self.survivors = [Survivor(f"S{i + 1}", p) for i, p in enumerate(pts)]
        ev_rng = np.random.default_rng(seed + 10_000)
        self.events = gen_events(ev_rng, self.terr) if events is None else list(events)
        self.U = np.random.default_rng(seed + 20_000).random((len(FLEET), max(T_MAX, tmax) + 2))
        self.t = 0
        self._g, self._a = {}, {}
        self.log = []
        self.churn = 0
        self.record = record
        self.frames = []
        self.forecasts = []
        self.escalations = []
        self.occurred = set()
        self.pending_triggers = set()
        self.new_task_ids = []

    # ------------------------------------------------------------------ clone
    def clone(self, runtime_seed=None):
        c = World.__new__(World)
        c.seed = self.seed
        c.tmax = self.tmax
        c.terr, c.dead, c.hazard = self.terr.copy(), self.dead.copy(), self.hazard.copy()
        c.bridges, c.river_x = self.bridges, self.river_x
        c.storm, c.tver, c.sver = self.storm, self.tver, self.sver
        c.agents = [a.copy() for a in self.agents]
        c.by_id = {a.id: a for a in c.agents}
        c.tasks = {k: t.copy() for k, t in self.tasks.items()}
        c.survivors = [s.copy() for s in self.survivors]
        c.events = list(self.events)
        c.U = self.U.copy()
        if runtime_seed is not None:
            c.U[:, self.t:] = np.random.default_rng(runtime_seed).random((len(FLEET), c.U.shape[1] - self.t))
        c.t = self.t
        c._g, c._a = dict(self._g), dict(self._a)
        c.log, c.churn, c.record, c.frames = [], self.churn, False, []
        c.forecasts, c.escalations = [], []
        c.occurred = set(self.occurred)
        c.pending_triggers = set(self.pending_triggers)
        c.new_task_ids = list(self.new_task_ids)
        return c

    # --------------------------------------------------------------- distances
    def passable(self, x, y):
        return 0 <= x < W and 0 <= y < H and self.terr[y, x] == LAND

    def gmap(self, target):
        key = (self.tver, target)
        m = self._g.get(key)
        if m is None:
            m = np.full((H, W), INF)
            tx, ty = target
            if self.passable(tx, ty):
                m[ty, tx] = 0.0
                dq = deque([target])
                terr = self.terr
                while dq:
                    x, y = dq.popleft()
                    d = m[y, x] + 1.0
                    for dx, dy in NEI8:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H and terr[ny, nx] == LAND and m[ny, nx] > d:
                            m[ny, nx] = d
                            dq.append((nx, ny))
            self._g[key] = m
        return m

    def amap(self, target):
        """Risk-aware aerial routing toward `target` (Dijkstra; entering a cell costs 1 + 100*hazard).
        Returns (cost, length, risk) maps: min-cost-to-go, that path's length in cells, and the
        accumulated per-tick hazard along it (a first-order loss-probability estimate)."""
        key = (self.sver, target)
        m = self._a.get(key)
        if m is None:
            cost = np.full((H, W), INF)
            length = np.full((H, W), INF)
            risk = np.full((H, W), INF)
            tx, ty = target
            cost[ty, tx] = length[ty, tx] = risk[ty, tx] = 0.0
            pq = [(0.0, tx, ty)]
            hz = self.hazard
            while pq:
                d, x, y = heapq.heappop(pq)
                if d > cost[y, x]:
                    continue
                h = hz[y, x]
                for dx, dy in NEI8:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H:
                        nd = d + 1.0 + 100.0 * h + (0.05 if dx and dy else 0.0)  # tiny diagonal tie-break -> natural-looking routes
                        if nd < cost[ny, nx]:
                            cost[ny, nx] = nd
                            length[ny, nx] = length[y, x] + 1.0
                            risk[ny, nx] = risk[y, x] + h
                            heapq.heappush(pq, (nd, nx, ny))
            m = (cost, length, risk)
            self._a[key] = m
        return m

    def path_risk(self, a, p, q):
        """Accumulated storm hazard on the risk-aware route p -> q (aerial agents only)."""
        if not a.aerial or self.storm is None or p == q:
            return 0.0
        return float(self.amap(q)[2][p[1], p[0]])

    def dist(self, a, p, q, risk_aware=False):
        if p == q:
            return 0.0
        if a.aerial:
            if risk_aware and self.storm is not None:
                return float(self.amap(q)[1][p[1], p[0]])
            return float(cheb(p, q))
        return float(self.gmap(q)[p[1], p[0]])

    def next_cell(self, a, target, risk_aware):
        x, y = a.pos
        if a.aerial:
            if risk_aware and self.storm is not None:
                m = self.amap(target)[0]
                hz = self.hazard
                best, bv = None, INF
                for dx, dy in NEI8:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H:
                        v = m[ny, nx] + 1.0 + 100.0 * hz[ny, nx] + (0.05 if dx and dy else 0.0)  # cost of stepping into (nx, ny)
                        if v < bv - 1e-9:
                            best, bv = (nx, ny), v
                return best
            return (x + sgn(target[0] - x), y + sgn(target[1] - y))
        m = self.gmap(target)
        bv = m[y, x]
        if bv == INF:
            return None
        best = None
        for dx, dy in NEI8:
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and self.terr[ny, nx] == LAND and m[ny, nx] < bv:
                best, bv = (nx, ny), m[ny, nx]
        return best

    # ------------------------------------------------------------ projections
    def project(self, a, risk_aware):
        """Projected (pos, battery, kits, time) at the end of the agent's current plan."""
        pos, batt, kits, tt = a.pos, a.batt, a.kits, float(a.busy)
        if a.status == "charging" and pos == BASE:
            tt += max(0.0, (a.charge_target - batt) / a.charge)
            batt = max(batt, a.charge_target)
        for item in a.plan:
            if item == "BASE":
                d = self.dist(a, pos, BASE, risk_aware)
                batt -= d * a.rate(kits)
                tt += d / a.speed + max(0.0, (a.cap - batt) / a.charge)
                pos, batt, kits = BASE, a.cap, a.kit_cap
            elif isinstance(item, tuple):
                d = self.dist(a, pos, item[1], risk_aware)
                batt -= d * a.rate(kits)
                tt += d / a.speed
                pos = item[1]
            else:
                tk = self.tasks[item]
                d = self.dist(a, pos, tk.pos, risk_aware)
                batt -= d * a.rate(kits) + tk.dur * a.e_idle
                tt += d / a.speed + tk.dur
                pos = tk.pos
                if tk.kind == "deliver":
                    kits -= 1
        return pos, batt, kits, tt

    # ---------------------------------------------------------------- helpers
    def open_tasks(self):
        return [t for t in self.tasks.values() if t.status == "open"]

    def release_plan(self, a, keep=False):
        """Unassign all tasks in an agent's plan (optionally keep them in the plan)."""
        rel = []
        for item in a.plan:
            if isinstance(item, str) and item != "BASE":
                tk = self.tasks[item]
                if tk.status == "assigned" and tk.assignee == a.id and not keep:
                    tk.status, tk.assignee = "open", None
                    rel.append(item)
        if not keep:
            a.plan = [p for p in a.plan if not (isinstance(p, str) and p != "BASE")]
        return rel

    def connected_nodes(self, relay_override=None):
        """BFS over the comm mesh. Returns set of agent ids connected to base."""
        nodes = []
        for a in self.agents:
            if not a.alive:
                continue
            pos = relay_override if (relay_override is not None and a.kind == "relay") else a.pos
            if self.dead[pos[1], pos[0]]:
                continue
            nodes.append((a.id, pos, a.comm))
        conn = set()
        frontier = [(BASE, BASE_COMM)]
        remaining = nodes
        while frontier:
            new_frontier = []
            rest = []
            for (aid, pos, r) in remaining:
                if any(eucl(pos, fp) <= max(r, fr) for fp, fr in frontier):
                    conn.add(aid)
                    new_frontier.append((pos, r))
                else:
                    rest.append((aid, pos, r))
            frontier, remaining = new_frontier, rest
        return conn

    def logd(self, kind, text, **kw):
        if self.record:
            self.log.append(dict(t=self.t, kind=kind, text=text, **kw))

    def success(self):
        return all(s.delivered_t is not None for s in self.survivors)

    def finished(self):
        if self.t >= self.tmax:
            return True
        if any(e[0] >= self.t for e in self.events):
            return False
        surveys_done = all(t.status in ("done", "void") for t in self.tasks.values() if t.kind == "survey")
        return surveys_done and self.success()


# ----------------------------------------------------------------------------
# Policies
# ----------------------------------------------------------------------------
class Policy:
    name = "base"
    risk_aware = False
    reserve = False
    dynamic_relay = False
    voi = False
    report_seek = False
    replan = False
    sticky = 0.0
    period = 30
    tau = 120.0
    beta = 0.05
    gamma = 1.0
    risk_max = 0.12
    risk_override = {}      # per-agent-kind risk limit set by an operator decision, e.g. {"cargo": 1.0}
    max_bundle = 6
    charge_frac = 0.9

    # -- common safety behaviour: smart return-to-home (all policies) --------
    def needs_rth(self, w, a):
        if not a.alive or a.pos == BASE or a.status == "charging" or a.busy > 0:
            return False
        if a.plan and a.plan[0] == "BASE":
            return False
        need = w.dist(a, a.pos, BASE, self.risk_aware) * a.rate() * RTH_FACTOR + RTH_MARGIN
        return a.batt < need

    def charge_target(self, a):
        return a.cap * self.charge_frac

    # -- sequential auction (CBBA-style bundle construction, centralised) ----
    def bid(self, w, a, p, tk, sticky_map):
        if tk.req not in a.caps:
            return None
        ppos, pbatt, pkits, ptime = p
        d_tb = w.dist(a, tk.pos, BASE, self.risk_aware)
        if d_tb == INF:
            return None
        is_del = tk.kind == "deliver"
        opts = []
        if not (is_del and pkits <= 0):
            d1 = w.dist(a, ppos, tk.pos, self.risk_aware)
            if d1 < INF:
                e_task = d1 * a.rate(pkits) + tk.dur * a.e_idle
                kits_after = pkits - (1 if is_del else 0)
                e_ret = d_tb * a.rate(kits_after)
                ok = (pbatt - e_task >= e_ret * RTH_FACTOR + RTH_MARGIN) if self.reserve else (pbatt - e_task > 0)
                if ok:
                    t_done = ptime + d1 / a.speed + tk.dur
                    opts.append((t_done, e_task, "direct", (tk.pos, pbatt - e_task, kits_after, t_done)))
        d0 = w.dist(a, ppos, BASE, self.risk_aware)
        if d0 < INF and pbatt - d0 * a.rate(pkits) >= 0:
            b_at_base = pbatt - d0 * a.rate(pkits)
            t_charge = max(0.0, (a.cap - b_at_base) / a.charge)
            d1b = w.dist(a, BASE, tk.pos, self.risk_aware)
            if d1b < INF:
                kits_b = a.kit_cap
                e_task = d1b * a.rate(kits_b) + tk.dur * a.e_idle
                kits_after = kits_b - (1 if is_del else 0)
                e_ret = d_tb * a.rate(kits_after)
                ok = (a.cap - e_task >= e_ret * RTH_FACTOR + RTH_MARGIN) if self.reserve else (a.cap - e_task > 0)
                if ok and not (is_del and kits_b <= 0):
                    t_done = ptime + d0 / a.speed + t_charge + d1b / a.speed + tk.dur
                    opts.append((t_done, d0 * a.rate(pkits) + e_task, "via_base",
                                 (tk.pos, a.cap - e_task, kits_after, t_done)))
        if not opts:
            return None
        t_done, energy, opt, newp = min(opts, key=lambda o: o[0])
        risk = 0.0
        if self.risk_aware and a.aerial and w.storm is not None:
            start = BASE if opt == "via_base" else ppos
            risk = w.path_risk(a, start, tk.pos) + float(w.hazard[tk.pos[1], tk.pos[0]]) * (tk.dur + 1)
            if risk > self.risk_override.get(a.kind, self.risk_max):
                return None
        score = tk.prio * math.exp(-t_done / self.tau) - self.beta * energy / a.cap - self.gamma * risk
        if sticky_map and sticky_map.get(tk.id) == a.id:
            score += self.sticky
        return (score, opt, newp, t_done)

    def auction(self, w, task_ids, agents, sticky_map=None, why=""):
        """Sequential greedy auction (centralised CBBA-style bundle building).

        Repeatedly awards the single highest (agent, task) bid, appends the task to
        that agent's bundle, and re-bids only that agent (lazy max-heap), so a global
        re-plan costs O(A*T + T^2) bid evaluations instead of O(A*T^2)."""
        if not task_ids or not agents:
            return []
        proj = {a.id: w.project(a, self.risk_aware) for a in agents}
        open_set = set(task_ids)
        order = {tid: i for i, tid in enumerate(task_ids)}
        aidx = {a.id: i for i, a in enumerate(agents)}
        ver = {a.id: 0 for a in agents}
        ntask = {a.id: sum(1 for it in a.plan if isinstance(it, str) and it != "BASE") for a in agents}
        heap = []

        def push_row(a):
            if ntask[a.id] >= self.max_bundle:
                return
            p, v, ai = proj[a.id], ver[a.id], aidx[a.id]
            for tid in open_set:
                b = self.bid(w, a, p, w.tasks[tid], sticky_map)
                if b is not None:
                    heap.append((-b[0], ai, order[tid], v, a.id, tid, b))

        for a in agents:
            push_row(a)
        heapq.heapify(heap)
        out = []
        while heap and open_set:
            _, _, _, v, aid, tid, best = heapq.heappop(heap)
            if tid not in open_set or v != ver[aid]:
                continue
            a = w.by_id[aid]
            score, opt, newp, t_done = best
            if opt == "via_base":
                a.plan.append("BASE")
            a.plan.append(tid)
            tk = w.tasks[tid]
            tk.status, tk.assignee = "assigned", aid
            open_set.discard(tid)
            proj[aid] = newp
            ver[aid] += 1
            ntask[aid] += 1
            before = len(heap)
            push_row(a)
            if len(heap) > before:
                # restore heap property for the newly appended entries
                for i in range(before, len(heap)):
                    heapq._siftdown(heap, 0, i)
            runner_up = None
            if w.record:
                alts = []
                for other in agents:
                    if other.id == aid:
                        continue
                    ob = self.bid(w, other, w.project(other, self.risk_aware), tk, None)
                    alts.append((other.id, None if ob is None else round(ob[0], 2)))
                runner_up = alts
            out.append((tid, aid, round(score, 3), opt, round(t_done, 1), runner_up))
        return out

    # to be overridden
    def init(self, w):
        pass

    def decide(self, w, triggers):
        pass


class Concord(Policy):
    name = "concord"
    risk_aware = True
    reserve = True
    dynamic_relay = True
    voi = True
    report_seek = True
    replan = True
    sticky = 0.08
    charge_frac = 1.0

    def __init__(self, **flags):
        for k, v in flags.items():
            setattr(self, k, v)

    def init(self, w):
        relay = [a for a in w.agents if a.kind == "relay"][0]
        relay.plan = [("STATION", FIXED_RELAY_STATION)]

    def workers(self, w):
        return [a for a in w.agents if a.alive and a.kind != "relay"]

    def place_relay(self, w):
        relay = [a for a in w.agents if a.kind == "relay"][0]
        if not relay.alive or (relay.plan and relay.plan[0] == "BASE") or relay.status == "charging":
            return
        others = [a for a in w.agents if a.alive and a.kind != "relay"]
        weights = {}
        for a in others:
            wgt = 1.0
            if a.kind == "rover" or a.kind == "cargo":
                wgt = 1.5
            if any(m[0] >= 3 for m in a.outbox):
                wgt = 3.0
            weights[a.id] = wgt
        # anticipated positions: next target of each agent
        ant = {}
        for a in others:
            tgt = None
            for it in a.plan:
                if it == "BASE":
                    tgt = BASE
                elif isinstance(it, tuple):
                    tgt = it[1]
                else:
                    tgt = w.tasks[it].pos
                break
            ant[a.id] = tgt
        cur = relay.plan[0][1] if relay.plan and isinstance(relay.plan[0], tuple) else relay.pos
        best, bscore = cur, -1e9
        for cy in range(0, H, 2):
            for cx in range(0, W, 2):
                if w.dead[cy, cx] or w.hazard[cy, cx] > 0:
                    continue
                cand = (cx, cy)
                # the relay must hold a direct link to base (never depend on a transient chain through a moving agent)
                if eucl(cand, BASE) > max(BASE_COMM, relay.comm):
                    continue
                conn = w.connected_nodes(relay_override=cand)
                if relay.id not in conn:
                    continue
                sc = sum(weights[a.id] for a in others if a.id in conn)
                # look-ahead: would the agent's next target be covered?
                for a in others:
                    tg = ant[a.id]
                    if tg is not None and not w.dead[tg[1], tg[0]]:
                        if eucl(tg, cand) <= max(relay.comm, a.comm) or eucl(tg, BASE) <= max(BASE_COMM, a.comm):
                            sc += 0.5 * weights[a.id]
                sc -= 0.01 * cheb(cand, cur)
                if sc > bscore:
                    best, bscore = cand, sc
        if best != cur:
            w.logd("relay", f"Relay-1 repositions to {best} to keep {sum(1 for a in others if a.id in w.connected_nodes(relay_override=best))} agents linked to base")
        relay.plan = [("STATION", best)]

    def covered_mask(self, w, a, conn):
        mask = np.zeros((H, W), bool)
        mask |= disc_mask(BASE[0], BASE[1], max(BASE_COMM, a.comm))
        for o in w.agents:
            if o.alive and o.id in conn and o.id != a.id:
                mask |= disc_mask(o.pos[0], o.pos[1], max(o.comm, a.comm))
        mask &= ~w.dead
        return mask

    def decide(self, w, triggers):
        t = w.t
        # 1) battery-reserve monitor (safety)
        for a in w.agents:
            if self.needs_rth(w, a):
                rel = w.release_plan(a)
                a.plan = ["BASE"] + [p for p in a.plan if p != "BASE" and not isinstance(p, tuple)]
                need = w.dist(a, a.pos, BASE, self.risk_aware) * a.rate()
                w.logd("battery", f"{a.id} returns to base: {a.batt / a.cap:.0%} battery left, {need / a.cap:.0%} needed to reach base + 15% reserve; its {len(rel)} tasks re-auctioned",
                       agent=a.id, released=rel)
                triggers.add("rth")
        # 2) value-of-information: go back into coverage to report critical findings
        if self.report_seek:
            conn = w.connected_nodes()
            for a in self.workers(w):
                if a.connected or a.busy > 0 or not any(m[0] >= 3 for m in a.outbox):
                    continue
                if a.plan and isinstance(a.plan[0], tuple) and a.plan[0][0] == "REPORT":
                    continue
                mask = self.covered_mask(w, a, conn)
                if not mask.any():
                    continue
                ys, xs = np.nonzero(mask)
                dd = np.maximum(np.abs(xs - a.pos[0]), np.abs(ys - a.pos[1]))
                k = int(np.argmin(dd))
                if dd[k] <= 12:
                    cell = (int(xs[k]), int(ys[k]))
                    a.plan.insert(0, ("REPORT", cell))
                    w.logd("voi", f"{a.id} holds a survivor report in a dead zone -> detours {int(dd[k])} cells to reconnect (VoI priority)", agent=a.id)
        # 3) comms: relay placement
        if self.dynamic_relay and (t % 5 == 0 or triggers & {"comm_blackout", "storm", "agent_fail", "operator"}):
            self.place_relay(w)
        # 4) allocation
        workers = self.workers(w)
        for a in workers:
            if is_standby(a):
                a.plan = []
        global_replan = self.replan and (
            t == 0 or bool(triggers & {"storm", "storm_end", "bridge_collapse", "operator"}) or (t > 0 and t % self.period == 0))
        if global_replan:
            sticky_map = {}
            for a in workers:
                keep = []
                for i, it in enumerate(a.plan):
                    if isinstance(it, str) and it != "BASE":
                        if i == 0 and a.busy > 0:
                            keep.append(it)
                            continue
                        tk = w.tasks[it]
                        sticky_map[it] = a.id
                        tk.status, tk.assignee = "open", None
                    elif it == "BASE" and i == 0 and a.batt < 0.5 * a.cap:
                        keep.append(it)
                    elif isinstance(it, tuple) and i == 0:
                        keep.append(it)
                a.plan = keep
            ids = [tk.id for tk in w.open_tasks()]
            res = self.auction(w, ids, workers, sticky_map, why="global")
            for (tid, aid, score, opt, t_done, alts) in res:
                if tid in sticky_map and sticky_map[tid] != aid:
                    w.churn += 1
            if triggers:
                w.logd("replan", f"Global re-plan ({', '.join(sorted(triggers))}): {len(res)} tasks re-auctioned",
                       res=res)
        elif self.replan or t == 0:
            ids = [tk.id for tk in w.open_tasks()]
            idle = any(a.alive and not a.plan for a in workers)
            if ids and (triggers or idle):
                res = self.auction(w, ids, workers, None, why="repair")
                for (tid, aid, score, opt, t_done, alts) in res:
                    tk = w.tasks[tid]
                    if tk.kind == "deliver" or triggers & {"agent_fail", "rth", "battery_drain"}:
                        alt_txt = ""
                        if alts:
                            alt_txt = "; others: " + ", ".join(f"{o} {'ineligible' if b is None else f'bid {b:.2f}'}" for o, b in alts)
                        w.logd("assign", f"{tk.label} -> {aid} (bid {score:.2f}, ETA t+{t_done:.0f}{alt_txt})", task=tid, agent=aid)

def is_standby(a):
    return len(a.plan) == 1 and isinstance(a.plan[0], tuple) and a.plan[0][0] == "HOME"


def restation_fixed_relay(w):
    relay = [a for a in w.agents if a.kind == "relay"][0]
    if relay.alive and not relay.plan and relay.status != "charging":
        relay.plan = [("STATION", FIXED_RELAY_STATION)]


class Greedy(Policy):
    name = "greedy"

    def init(self, w):
        relay = [a for a in w.agents if a.kind == "relay"][0]
        relay.plan = [("STATION", FIXED_RELAY_STATION)]

    def decide(self, w, triggers):
        for a in w.agents:
            if self.needs_rth(w, a):
                w.release_plan(a)
                a.plan = ["BASE"]
        restation_fixed_relay(w)
        taken = set()
        for a in w.agents:
            if not a.alive or a.kind == "relay" or a.busy:
                continue
            if a.plan and not is_standby(a):
                continue
            if a.status == "charging":
                continue
            best, bd = None, INF
            for tk in w.tasks.values():
                if tk.status != "open" or tk.id in taken or tk.req not in a.caps:
                    continue
                d = w.dist(a, a.pos, tk.pos)
                if d < bd:
                    best, bd = tk, d
            if best is None:
                continue
            taken.add(best.id)
            best.status, best.assignee = "assigned", a.id
            a.plan = (["BASE"] if (best.kind == "deliver" and a.kits <= 0) else []) + [best.id]


class Static(Policy):
    name = "static"

    def init(self, w):
        relay = [a for a in w.agents if a.kind == "relay"][0]
        relay.plan = [("STATION", FIXED_RELAY_STATION)]
        # one-shot allocation of all known tasks, ignoring future energy limits
        saved = (self.reserve, self.max_bundle, self.tau)
        self.reserve, self.max_bundle, self.tau = False, 10 ** 6, 400.0
        workers = [a for a in w.agents if a.kind != "relay"]
        self.auction(w, [t.id for t in w.open_tasks()], workers)
        self.reserve, self.max_bundle, self.tau = saved

    def decide(self, w, triggers):
        for a in w.agents:
            if self.needs_rth(w, a):
                a.plan = ["BASE"] + [p for p in a.plan if p != "BASE"]
        restation_fixed_relay(w)
        for tid in w.new_task_ids:
            tk = w.tasks[tid]
            best, bd = None, INF
            for a in w.agents:
                if not a.alive or tk.req not in a.caps:
                    continue
                d = w.dist(a, a.pos, tk.pos)
                if d < bd:
                    best, bd = a, d
            if best is not None:
                pkits = w.project(best, False)[2]
                best.plan += (["BASE"] if pkits <= 0 else []) + [tid]
                tk.status, tk.assignee = "assigned", best.id


POLICIES = {"concord": Concord, "greedy": Greedy, "static": Static}


def make_policy(name, **flags):
    if name == "concord":
        return Concord(**flags)
    return POLICIES[name]()


# ----------------------------------------------------------------------------
# Simulation step
# ----------------------------------------------------------------------------
def apply_events(w, pol):
    trig = set()
    for ev in [e for e in w.events if e[0] == w.t]:
        _, kind, prm = ev
        w.occurred.add(kind)
        if kind == "agent_fail":
            a = w.agents[prm["idx"]]
            if a.alive:
                a.status, a.lost_t, a.lost_why = "lost", w.t, "hardware failure"
                rel = w.release_plan(a, keep=(pol.name == "static"))
                w.logd("event", f"EVENT: {a.id} suffers a hardware failure", agent=a.id, released=rel)
                trig.add("agent_fail")
        elif kind == "battery_drain":
            a = w.agents[prm["idx"]]
            if a.alive:
                a.batt = max(5.0, a.batt - prm["frac"] * a.cap)
                w.logd("event", f"EVENT: {a.id} battery drops to {a.batt / a.cap:.0%} (cell fault)", agent=a.id)
                trig.add("battery_drain")
        elif kind == "bridge_collapse":
            cells = w.bridges[prm["bridge"]]
            for (x, y) in cells:
                w.terr[y, x] = WATER
            for a in w.agents:
                if not a.aerial and a.pos in cells:
                    a.pos = (cells[0][0] - 1, cells[0][1])
            w.tver += 1
            w.logd("event", f"EVENT: {'north' if prm['bridge'] == 0 else 'south'} bridge collapses", bridge=prm["bridge"])
            trig.add("bridge_collapse")
        elif kind == "comm_blackout":
            cx, cy = prm["center"]
            w.dead |= disc_mask(cx, cy, prm["r"])
            w.logd("event", f"EVENT: comm blackout around {prm['center']}")
            trig.add("comm_blackout")
        elif kind == "storm":
            cx, cy = prm["center"]
            w.storm = (cx, cy, prm["r"], w.t + prm["dur"])
            w.hazard[:] = 0.0
            w.hazard[disc_mask(cx, cy, prm["r"])] = STORM_HAZARD
            w.sver += 1
            w.logd("event", f"EVENT: storm cell forms over {sector_of((cx, cy))} (aerial hazard)")
            trig.add("storm")
        elif kind == "new_target":
            sid = f"S{len(w.survivors) + 1}"
            s = Survivor(sid, prm["pos"], appear_t=w.t, by_call=True)
            s.detected_t = s.reported_t = w.t
            w.survivors.append(s)
            tid = f"DL-{sid}"
            w.tasks[tid] = Task(tid, "deliver", s.pos, 1.0, "payload", 2, True, w.t, label=f"Deliver {sid}", sid=sid)
            w.new_task_ids.append(tid)
            w.logd("event", f"EVENT: emergency call - new survivor {sid} at {s.pos}", sid=sid)
            trig.add("new_task")
    if w.storm is not None and w.t >= w.storm[3]:
        w.storm = None
        w.hazard[:] = 0.0
        w.sver += 1
        w.logd("event", "EVENT: storm clears")
        trig.add("storm_end")
    return trig


def sense(w, a):
    if a.sensor <= 0:
        return
    for s in w.survivors:
        if s.detected_t is None and cheb(a.pos, s.pos) <= a.sensor:
            s.detected_t = w.t
            a.outbox.append([3, w.t, "survivor", s.sid])
            w.logd("detect", f"{a.id} spots survivor {s.sid} at {s.pos}", agent=a.id, sid=s.sid)


def complete_item(w, a, pol):
    item = a.plan.pop(0)
    tk = w.tasks[item]
    tk.status = "done"
    if tk.kind == "deliver":
        a.kits -= 1
        for s in w.survivors:
            if s.sid == tk.sid and s.delivered_t is None:
                s.delivered_t = w.t
                w.logd("deliver", f"{a.id} delivers med-kit to {s.sid}", agent=a.id, sid=s.sid)


def act(w, a, pol):
    if not a.alive:
        return
    at_base = a.pos == BASE
    if a.status == "charging":
        a.batt = min(a.cap, a.batt + a.charge)
        if a.batt >= a.charge_target - 1e-9:
            a.status = "active"
        else:
            return
    if a.busy > 0:
        a.busy -= 1
        a.batt -= a.e_idle
        a.energy_used += a.e_idle
        if a.busy == 0:
            complete_item(w, a, pol)
        return
    # drop invalid plan heads (e.g. task done by someone else / unreachable)
    while a.plan:
        it = a.plan[0]
        if isinstance(it, str) and it != "BASE":
            tk = w.tasks[it]
            if tk.status == "done" or tk.assignee != a.id or (tk.kind == "deliver" and a.kits <= 0):
                a.plan.pop(0)
                if tk.status == "assigned" and tk.assignee == a.id:
                    tk.status, tk.assignee = "open", None
                continue
            if w.dist(a, a.pos, tk.pos, pol.risk_aware) == INF:
                a.plan.pop(0)
                tk.status, tk.assignee = "open", None
                continue
        break
    if not a.plan:
        if at_base:
            a.batt = min(a.cap, a.batt + a.charge)
            return
        if a.kind != "relay":
            a.plan = [("HOME", BASE)]  # idle -> return to standby at base (all policies)
        else:
            if a.aerial:
                a.batt -= a.e_idle
                a.energy_used += a.e_idle
            return
    it = a.plan[0]
    if it == "BASE":
        target = BASE
    elif isinstance(it, tuple):
        target = it[1]
    else:
        target = w.tasks[it].pos
    if a.pos == target:
        arrive(w, a, pol, it)
        return
    speed = a.speed * (0.5 if (a.aerial and w.hazard[a.pos[1], a.pos[0]] > 0) else 1.0)
    a.budget = min(a.budget + speed, 2.5)
    moved = 0
    while a.budget >= 1.0 and a.pos != target:
        nxt = w.next_cell(a, target, pol.risk_aware)
        if nxt is None:
            break
        e = a.rate()
        a.batt -= e
        a.energy_used += e
        a.pos = nxt
        a.budget -= 1.0
        moved += 1
        sense(w, a)
        if a.batt <= 0:
            a.status, a.lost_t, a.lost_why = "lost", w.t, "battery depleted"
            w.release_plan(a, keep=(pol.name == "static"))
            w.logd("loss", f"{a.id} LOST: battery depleted in the field", agent=a.id)
            return
    if moved == 0 and a.aerial:
        a.batt -= a.e_idle
        a.energy_used += a.e_idle
    if a.pos == target:
        arrive(w, a, pol, it)


def arrive(w, a, pol, it):
    if it == "BASE":
        a.plan.pop(0)
        a.kits = a.kit_cap
        a.status = "charging"
        a.charge_target = pol.charge_target(a) if pol.name != "concord" else a.cap
        a.budget = 0.0
    elif isinstance(it, tuple):
        if it[0] == "REPORT":
            a.plan.pop(0)
        elif it[0] == "HOME":
            a.plan.pop(0)
            a.kits = a.kit_cap
            a.status = "charging"
            a.charge_target = pol.charge_target(a) if pol.name != "concord" else a.cap
            a.budget = 0.0
        # STATION: stay (hover) - plan head kept
    else:
        tk = w.tasks[it]
        if tk.kind == "deliver" and a.kits <= 0:
            return
        a.busy = tk.dur


def hazards(w):
    for a in w.agents:
        if a.alive and a.aerial and w.hazard[a.pos[1], a.pos[0]] > 0:
            if w.U[a.idx, w.t] < w.hazard[a.pos[1], a.pos[0]]:
                a.status, a.lost_t, a.lost_why = "lost", w.t, "storm"
                w.release_plan(a)
                w.logd("loss", f"{a.id} LOST in storm", agent=a.id)
        if a.alive and a.batt <= 0 and a.pos != BASE:
            a.status, a.lost_t, a.lost_why = "lost", w.t, "battery depleted"
            w.release_plan(a)
            w.logd("loss", f"{a.id} LOST: battery depleted", agent=a.id)


def comms(w, pol):
    conn = w.connected_nodes()
    trig = set()
    for a in w.agents:
        if not a.alive:
            continue
        a.connected = a.id in conn
        a.outbox.append([0, w.t, "telemetry", None])
        if not a.connected:
            continue
        if pol.voi:
            a.outbox.sort(key=lambda m: (-m[0], m[1]))
        sent = a.outbox[:MSG_BANDWIDTH]
        del a.outbox[:MSG_BANDWIDTH]
        for m in sent:
            if m[2] == "survivor":
                s = next(s for s in w.survivors if s.sid == m[3])
                if s.reported_t is None:
                    s.reported_t = w.t
                    tid = f"DL-{s.sid}"
                    w.tasks[tid] = Task(tid, "deliver", s.pos, 1.0, "payload", 2, True, w.t,
                                        label=f"Deliver {s.sid}", sid=s.sid)
                    w.new_task_ids.append(tid)
                    w.logd("report", f"Base receives {a.id}'s survivor report {s.sid} ({w.t - s.detected_t} ticks after detection)", sid=s.sid)
                    trig.add("new_task")
    # survey waypoints in blacked-out / unreachable areas stay open; nothing else to do
    return trig


def snapshot(w):
    conn = w.connected_nodes()
    relay = [a for a in w.agents if a.kind == "relay"][0]
    return dict(
        t=w.t,
        agents=[dict(id=a.id, kind=a.kind, pos=a.pos, batt=a.batt / a.cap, alive=a.alive, conn=a.id in conn,
                     status=a.status, kits=a.kits,
                     target=(BASE if a.plan and a.plan[0] == "BASE" else
                             (a.plan[0][1] if a.plan and isinstance(a.plan[0], tuple) else
                              (w.tasks[a.plan[0]].pos if a.plan else None))),
                     plan=[(BASE if it == "BASE" else (it[1] if isinstance(it, tuple) else w.tasks[it].pos))
                           for it in a.plan[:6]])
                for a in w.agents],
        survivors=[dict(sid=s.sid, pos=s.pos, detected=s.detected_t is not None, reported=s.reported_t is not None,
                        delivered=s.delivered_t is not None) for s in w.survivors],
        surveys=[(t.pos, t.status) for t in w.tasks.values() if t.kind == "survey"],
        storm=w.storm,
        dead=w.dead.copy() if (not w.frames or w.frames[-1]["dead_ver"] != int(w.dead.sum())) else None,
        dead_ver=int(w.dead.sum()),
        terr=w.terr.copy() if (not w.frames or w.frames[-1]["tver"] != w.tver) else None,
        tver=w.tver,
        relay_station=relay.plan[0][1] if relay.plan and isinstance(relay.plan[0], tuple) else None,
    )


def step(w, pol):
    trig = apply_events(w, pol)
    trig |= w.pending_triggers
    w.pending_triggers = set()
    pol.decide(w, trig)
    w.new_task_ids = []
    for a in w.agents:
        act(w, a, pol)
    hazards(w)
    for a in w.agents:
        if a.alive:
            sense(w, a)
    w.pending_triggers |= comms(w, pol)
    if w.record:
        w.frames.append(snapshot(w))
    w.t += 1


def metrics(w):
    surv = w.survivors
    n = len(surv)
    delivered = sum(1 for s in surv if s.delivered_t is not None)
    tta = [((s.delivered_t if s.delivered_t is not None else w.tmax) - s.appear_t) for s in surv]
    rep = [(s.reported_t - s.detected_t) for s in surv if s.reported_t is not None and s.detected_t is not None and not s.by_call]
    surveys = [t for t in w.tasks.values() if t.kind == "survey"]
    return dict(
        seed=w.seed,
        success=int(delivered == n),
        delivered_frac=delivered / n if n else 1.0,
        survivors=n,
        time_to_aid=float(np.mean(tta)) if tta else 0.0,
        report_latency=float(np.mean(rep)) if rep else float("nan"),
        agents_lost=sum(1 for a in w.agents if not a.alive),
        agents_lost_non_injected=sum(1 for a in w.agents if not a.alive and a.lost_why != "hardware failure"),
        coverage=sum(1 for t in surveys if t.status == "done") / len(surveys),
        churn=w.churn,
        energy=sum(a.energy_used for a in w.agents),
        makespan=w.t,
        n_events=len(w.events),
        aid_times=[(s.delivered_t - s.appear_t) if s.delivered_t is not None else None for s in surv],
    )


def run_mission(seed, policy="concord", record=False, events=None, world=None, **flags):
    w = world if world is not None else World(seed, events=events, record=record)
    pol = make_policy(policy, **flags)
    pol.init(w)
    while not w.finished():
        step(w, pol)
    return metrics(w), w


# ----------------------------------------------------------------------------
# Monte-Carlo feasibility forecast
# ----------------------------------------------------------------------------
def forecast(w, K=40, seed=0, **flags):
    """P(mission success) from K rollouts of the current plan. Future disruptions are
    unknown to the forecaster, so each rollout samples them from the prior."""
    return forecast_wins(w, range(K), seed, **flags) / K


def forecast_wins(w, ks, seed=0, **flags):
    """Number of successful rollouts among rollout indices `ks` (lets callers split the
    K rollouts of `forecast` across worker processes with identical results)."""
    wins = 0
    for k in ks:
        c = w.clone(runtime_seed=hash((w.seed, w.t, seed, k)) % (2 ** 32))
        rng = np.random.default_rng(hash((w.seed, w.t, seed, k, 1)) % (2 ** 32))
        known = [e for e in c.events if e[0] < c.t]
        future = gen_events(rng, c.terr, t_from=c.t + 1, exclude=c.occurred)
        c.events = known + future
        pol = make_policy("concord", **flags)
        while not c.finished():
            step(c, pol)
        wins += c.success()
    return wins


if __name__ == "__main__":
    import time
    for pol in ("concord", "greedy", "static"):
        t0 = time.time()
        res = [run_mission(s, pol)[0] for s in range(20)]
        dt = time.time() - t0
        print(pol, f"{dt / 20 * 1000:.0f} ms/mission",
              "success", np.mean([r["success"] for r in res]),
              "deliv", round(np.mean([r["delivered_frac"] for r in res]), 3),
              "lost", np.mean([r["agents_lost"] for r in res]),
              "tta", round(np.mean([r["time_to_aid"] for r in res]), 1),
              "cov", round(np.mean([r["coverage"] for r in res]), 3))
