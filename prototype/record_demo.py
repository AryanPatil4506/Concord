"""Record live-console missions for the static (frontend-only) demo build.

Drives the real MissionSession headlessly and captures every message it would have sent over the
WebSocket. At each operator escalation every option is recorded as its own branch (to MAX_DEPTH;
deeper escalations follow the recommended option), so the hosted demo can replay whichever answer
the viewer picks.

    python record_demo.py            # -> console/public/demo/*.json
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from server import compiler, forecasting  # noqa: E402
from server.app import _json_default  # noqa: E402
from server.session import SCENARIOS, MissionSession  # noqa: E402

OUT = os.path.join(HERE, "console", "public", "demo")
RESULTS = os.path.join(HERE, "results")
MAX_DEPTH = 2

# (id, scenario, seed, title, blurb, scripted operator injections [(tick, kind, params)])
DEMOS = [
    ("storyboard", "storyboard", None, "Flood SAR · storyboard",
     "Seed 6 · 6 survivors · 200 ticks · 5 scripted disruptions revealed as they happen "
     "(the mission in the demo video). Includes an operator escalation.", []),
    ("random-42", "random", 42, "Flood SAR · random scenario (seed 42)",
     "5 survivors · 320 ticks · disruptions drawn from the benchmark prior, unknown to the planner in advance.", []),
    ("random-1234", "random", 1234, "Flood SAR · random scenario (seed 1234)",
     "5 survivors · 320 ticks · a second draw from the benchmark prior.", []),
    ("chaos", "sandbox", 77, "Flood SAR · operator chaos",
     "Seed 77 · 6 survivors · 240 ticks · an operator breaks the plan live: hardware failure, bridge collapse, "
     "storm, comms blackout and a new emergency call.",
     [(30, "agent_fail", {"agent": "Scout-2"}),
      (55, "bridge_collapse", {"bridge": 0}),
      (80, "storm", {"pos": [33, 21]}),
      (105, "comm_blackout", {"pos": [38, 12]}),
      (130, "new_target", {"pos": [36, 30]})]),
]


def _clean(msg):
    return json.loads(json.dumps(msg, default=_json_default))


async def run(scenario, seed, injections, script):
    """Run one mission to completion. `script` lists the option chosen at each escalation (in order);
    escalations beyond the script take the recommended option. Returns the message stream with an
    `{"type": "_decide", ...}` marker after each escalation."""
    out = []

    async def broadcast(msg):
        out.append(_clean(msg))

    s = MissionSession(broadcast, scenario=scenario, seed=seed,
                       objective=compiler.DEFAULT_OBJECTIVE)
    out.append(_clean(s.full_state()))
    s.phase = "running"
    out.append(dict(type="phase", phase="running"))
    pending = sorted(injections)
    n_esc = 0
    # forecasts in the live server run concurrently; here each is awaited so the order is fixed
    s._schedule_forecast()
    while s.phase != "complete":
        await asyncio.gather(*list(s._forecast_tasks))
        while pending and pending[0][0] == s.world.t:
            _, kind, prm = pending.pop(0)
            s.last_inject = 0.0
            err = await s.inject(kind, prm)
            if err:
                raise RuntimeError(f"inject {kind} at t={s.world.t}: {err}")
        await s._tick()
        if s.phase == "escalation":
            s._timeout_task.cancel()
            esc = s.escalation
            key = script[n_esc] if n_esc < len(script) else esc["recommend"]
            out.append(dict(type="_decide", key=key, depth=n_esc,
                            options=[o["key"] for o in esc["options"]], recommend=esc["recommend"]))
            n_esc += 1
            await s.decide(key)
    await asyncio.gather(*list(s._forecast_tasks))
    return out


def _split(stream, depth):
    """Messages after the `depth`-th decision marker up to (excluding) the next one."""
    seen = -1
    seg = []
    for m in stream:
        if m["type"] == "_decide":
            seen += 1
            if seen == depth:
                return seg, m
            seg = []
            continue
        if seen == depth - 1:
            seg.append(m)
    return seg, None


async def build_node(scenario, seed, injections, script, cache):
    key = tuple(script)
    if key not in cache:
        t0 = time.time()
        cache[key] = await run(scenario, seed, injections, list(script))
        print(f"    run {list(script) or '[]'}: {len(cache[key])} msgs, {time.time() - t0:.1f}s", flush=True)
    stream = cache[key]
    seg, marker = _split(stream, len(script))
    node = dict(messages=seg)
    if marker:
        node["recommend"] = marker["recommend"]
        if len(script) < MAX_DEPTH:
            node["branches"] = {}
            for opt in marker["options"]:
                node["branches"][opt] = await build_node(scenario, seed, injections, script + [opt], cache)
        else:
            # deeper escalations: every answer replays the recommended branch
            node["branches"] = {"*": await build_node(scenario, seed, injections, script + [marker["recommend"]],
                                                      cache)}
    return node


def _strip(node):
    """Drop the decision markers that leaked into deeper segments."""
    node["messages"] = [m for m in node["messages"] if m["type"] != "_decide"]
    for b in node.get("branches", {}).values():
        _strip(b)
    return node


async def main():
    os.makedirs(OUT, exist_ok=True)
    index = []
    for did, scenario, seed, title, blurb, inj in DEMOS:
        print(f"recording {did}", flush=True)
        cache = {}
        root = _strip(await build_node(scenario, seed, inj, [], cache))
        first = root["messages"][0]
        first["scenario"] = did
        first["scenario_title"] = title
        with open(os.path.join(OUT, f"{did}.json"), "w") as f:
            json.dump(root, f, separators=(",", ":"))
        index.append(dict(id=did, title=title, blurb=blurb, fixed_seed=first["static"]["seed"],
                          tmax=SCENARIOS[scenario]["tmax"]))
    with open(os.path.join(OUT, "scenarios.json"), "w") as f:
        json.dump(index, f, indent=1)

    with open(os.path.join(RESULTS, "summary.json")) as f:
        summary = json.load(f)
    ev = dict(main=summary["main"], stress=summary["stress"], ablation=summary["ablation"],
              paired=summary["paired_concord_minus_greedy"])
    sb = os.path.join(RESULTS, "storyboard.json")
    if os.path.exists(sb):
        with open(sb) as f:
            s = json.load(f)
        ev["storyboard"] = dict(metrics=s["metrics"], timeline=s["timeline"], escalation=s["escalation"])
    with open(os.path.join(OUT, "evidence.json"), "w") as f:
        json.dump(ev, f, separators=(",", ":"), default=_json_default)
    forecasting.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
