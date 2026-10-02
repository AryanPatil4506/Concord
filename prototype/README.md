# CONCORD v0 — mission orchestration for heterogeneous robot & drone swarms

**ELEVATE 1.0 · EL-05 · prototype v0 (simulation)**

> Tell the swarm what you want done. CONCORD decides who does what, re-plans the moment the world changes, and asks a human only when it genuinely should.

This repository is the working prototype behind our proposal: a headless grid-world simulator, the CONCORD decision layer, two honest baselines, a seeded benchmark, a Monte-Carlo feasibility forecaster, and the renderer that produced the demo video and every chart in the deck.

## What is in v0

| Piece | File | What it does |
|---|---|---|
| World + agents + disruptions | `concord_sim.py` | 40×28 grid, river + bridges, flood pockets, buildings, dead zones, storms; 2 scout drones, 1 cargo drone, 1 rover, 1 relay drone; 6 disruption types |
| CONCORD policy | `concord_sim.py` (`Concord`) | sequential auction with time-discounted bids (CBBA-style bundle building), battery-reserve invariant, risk-aware routing, event-driven repair / global re-plan with hysteresis, relay placement, value-of-information messaging |
| Baselines | `concord_sim.py` (`Greedy`, `Static`) | nearest-capable-idle dispatch; one-shot plan with local return-to-home |
| Forecaster | `concord_sim.py` (`forecast`) | K Monte-Carlo rollouts of the live plan; future disruptions sampled from the prior |
| Benchmark | `run_benchmark.py`, `analyze.py` | 300 random scenarios × 3 policies, stress sweep (0–6 disruption types), 5 ablations → `results/summary.json` |
| Scaling test | `scaling.py` | allocator latency vs fleet size (5 → 200 agents) |
| Storyboard + demo | `storyboard.py`, `make_demo.py`, `render.py` | scripted flood mission with a real escalation → console stills, GIF, MP4 |
| Charts | `figures.py`, `diagrams/` | every figure used in the deck |

## Live mission console

A web console on the same engine: brief a mission in plain English, review the compiled task graph, deploy, watch the swarm, inject disruptions ("break the plan"), and answer escalation cards. Benchmark evidence and the method are one tab away.

```bash
pip install numpy fastapi uvicorn             # engine + server
cd console && npm install && npm run build && cd ..
python -m server                              # → http://127.0.0.1:8000
```

For UI development, run `python -m server` and `cd console && npm run dev` (Vite on :5173 proxies `/api` and `/ws` to the engine).

| Piece | Where | What it does |
|---|---|---|
| Server | `server/app.py`, `server/session.py` | FastAPI + WebSocket; steps the v0 engine in real time, applies injected disruptions (rate-limited to one per 2 s, each logged with its parameters), re-forecasts after every disruption and raises escalation cards below 60% with a 30 s safe default |
| Forecasting | `server/forecasting.py` | the 40 Monte-Carlo rollouts split across worker processes (same results as `concord_sim.forecast`) |
| Mission compiler | `server/compiler.py` | **offline rule-based fallback** that fills the Mission DAG schema and runs the validation checks — no LLM is involved in v0 |
| Console | `console/` | React + TypeScript + Vite; one dependency beyond React (`lucide-react` icons) |

The storyboard scenario reproduces the recorded demo exactly (same forecasts, escalation at t=86 with Hold 0% vs. "fly Cargo-1 through the storm" 72%, all 6 survivors aided by t=162; greedy 3/6 and static 2/6 on the same disruptions).

## Reproduce everything (≈8 min on a 2-core laptop, CPU only)

```bash
pip install numpy matplotlib pillow            # + playwright for the HTML diagrams
python run_benchmark.py && python analyze.py   # 4,500 seeded missions -> results/summary.json
python scaling.py                              # results/scaling.json
python storyboard.py 6 && python make_demo.py  # media/ stills, concord_demo.gif / .mp4
python figures.py                              # charts/*.png
```

Every mission is seeded; the same seed gives the same result on every machine. Baselines and CONCORD see identical scenarios and identical random draws (paired comparison).

## Headline results (300 random disruption scenarios, 1,676 survivors)

| Metric | CONCORD | Greedy dispatch | Static plan |
|---|---|---|---|
| Mission success | **99.0%** | 96.3% | 20.0% |
| Mean time-to-aid (ticks) | **62.4** | 71.1 | 174.2 |
| Critical-report latency (ticks) | **0.84** | 8.71 | 8.09 |
| Avoidable asset losses / mission | **0.107** | 0.197 | 0.223 |
| Energy used | **579** | 611 | 668 |
| Task reassignments / mission | 0.12 | – | – |

Stress test, 6 simultaneous disruption types: success 96% vs 88% vs 16%.
Allocator: repair re-plan 8.6 ms and global re-plan 2.4 s at 200 agents / 600 tasks (1 core, pure Python).

## Honest limits of v0

* Grid world, no physics; agents are abstract (the PS asks for mission-level autonomy, not perception or control).
* Centralised auction while connected; the decentralised consensus phase of CBBA is the next step.
* The forecaster samples future disruptions from the same prior the benchmark uses, so its calibration is optimistic by construction.
* The battery-reserve invariant shows no measurable gain in v0 because the smart return-to-home safety net already catches most cases.
* 1 tick ≈ 10 s is an interpretation, not a calibrated constant.

## Roadmap

FastAPI + WebSocket live engine → React/PixiJS console with judge-facing disruption buttons → LLM mission compiler (schema-constrained, local fallback) → asynchronous CBBA for disconnected agents → OSM map import → ROS 2 / PX4 SITL bridge behind the same agent interface.
