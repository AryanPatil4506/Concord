# EL-05 · CONCORD — Slide-by-slide content for the ELEVATE 1.0 proposal deck

> **CONCORD** — *Tell the swarm what you want done. CONCORD decides who does what, re-plans the moment the world changes, and asks a human only when it genuinely should.*
>
> **The plan will break. The mission stays alive.**

This file tells you exactly what goes on each slide of the ELEVATE template: the words, the visuals (all generated and included), where each visual sits, and what to say. Every number in it comes either from a cited source or from our own working prototype (**CONCORD v0**, included), which was run on **4,500 seeded simulated missions**. Nothing is estimated unless it says so.

---

## 0. Read this first

### 0.1 What is in the package

The four visual folders are inside **`EL-05_CONCORD_Visuals.zip`**.

| Folder / file | What it holds | Use it for |
|---|---|---|
| `slides/` | **Slide-ready PNGs** rendered at the exact size they occupy on the slide (DPI embedded, so *Insert → Picture* drops them in at the right size) | building the 8 slides |
| `full_detail/` | Larger, more detailed versions of every chart and diagram | backup slides, GitHub README, Q&A |
| `media/` | Prototype console stills, `concord_demo.gif` (15 s), `concord_demo.mp4` | demo link, backup, social |
| `icons/` | 24 Tabler icons (MIT licence) in navy, orange and white | extra icons anywhere |
| `concord_v0_prototype.zip` | The working prototype + benchmark + every script that made every chart | your GitHub repo |
| `EL-05_CONCORD_Research_Dossier.md` | Deep research, full results, competitor notes, judge Q&A, demo script | preparation, not the slides |

**Files that are not placed on a slide (keep them for Q&A, the README and backup):**

| File | What it shows | When to pull it out |
|---|---|---|
| `slides/backup_forecast_timeline.png` | P(success) over the storyboard mission: drops to 0% when the rover fails in the storm, recovers after the human approves option B | "How does the forecast behave over time?" |
| `full_detail/chart_1_benchmark_kpis.png`, `chart_2_stress_sweep.png` | Larger versions of the slide 5 charts | README, zoomed Q&A |
| `full_detail/chart_3_time_to_aid_cdf.png` | Share of survivors aided vs time: 93% vs 88% vs 42% within 120 ticks | "Is the 12% driven by a few outliers?" (no — the whole curve shifts) |
| `full_detail/chart_4_ablation_table.png` | What each component buys (VoI 5.2×, hysteresis 33×, risk routing 1.75×, relay +34%, battery invariant no change) | "Which part actually matters?" |
| `full_detail/chart_5_scaling_latency.png` … `chart_9_market.png` | Larger versions of the scaling, forecast, survival, LLM-vs-planner and market charts | README |
| `full_detail/diagram_mission_dag.png` | The typed task graph the LLM compiles from a plain-English goal | "What exactly does the LLM output?" |
| `full_detail/diagram_risk_matrix.png` | Likelihood × impact matrix of eight risks (the five on slide 6 plus allocator thrashing, "it's just a game" and slow global re-plans), each with its mitigation | "What could go wrong?" |
| `full_detail/diagram_architecture.png`, `diagram_control_loop.png`, `diagram_comparison.png`, `diagram_gantt.png`, `diagram_scale_out.png`, `diagram_tech_stack.png` | Poster-size versions of the slide diagrams | README, printouts |
| `media/still_1 … still_5` | Console at t = 27 (survivor found, delivery auctioned), 36 (battery-reserve return), 52 (dead zone, reports still reach base), 86 (escalation card), 169 (mission complete) | GitHub README, demo-video thumbnail, backup if the video won't play |

### 0.2 The deck at a glance (8 slides — the maximum allowed)

| # | Template slide | One message the judge must leave with | Main visuals |
|---|---|---|---|
| 1 | Title | CONCORD is a mission brain for mixed drone–robot swarms, and it already works | abstract text |
| 2 | PROPOSED SOLUTION | We read the PS correctly: it is mission-level autonomy. LLM for intent, algorithms for decisions, humans for the hard calls | survival chart, control loop, key functionalities, PS-alignment strip |
| 3 | TECHNICAL APPROACH | Real algorithms with formulas, a clean architecture, no LLM in the control loop | architecture, core algorithms card, tech strip |
| 4 | INNOVATION AND UNIQUENESS | Four differentiators nobody else combines, each backed by evidence | differentiators, comparison matrix, LLM-vs-planner chart, real decision log |
| 5 | **PROTOTYPE AND EVIDENCE** *(the optional extra slide)* | We built it and broke it 4,500 times: faster aid, fewer avoidable losses, stable plans | live console still, KPI tiles, benchmark chart, stress chart |
| 6 | FEASIBILITY AND VIABILITY | Low-risk to build: the core is done, the 36-hour plan is concrete, risks have tested mitigations | feasibility card, Gantt, risk table |
| 7 | IMPACT AND SCALING | Real users, measurable benefits, and an architecture that survives success | users, market, impact, why-now, scale-out, scaling chart, testing |
| 8 | RESEARCH AND REFERENCES | Grounded in research, with openable links | evidence card, reference list, links + QR codes |

Delete the template's **INSTRUCTIONS** slide and the **empty 9th slide** before submitting.

### 0.3 Rules from the template — do not break these

1. **No more than 8 slides** (7 template slides + 1 extra). Ours is exactly 8.
2. **No participant names anywhere** — including inside links. Create a neutral GitHub account/organisation (for example `concord-el05`) and a neutral YouTube/Drive owner name; a personal username in a URL reveals a name.
3. **Every link must open for a stranger.** Test each in a private/incognito window. Drive files: *Anyone with the link → Viewer*. YouTube: *Unlisted*.
4. **File name:** `EL-05_<TeamName>` (the template asks for `psid_teamname`), saved as PDF (safest) or PPTX.
5. **Focused, visual, evidence-led.** Keep on-slide prose short; let the visuals carry the proof.
6. Judged on: problem understanding & solution clarity · technical depth & scaling · originality & differentiation · quality of research, prototype and presentation. Each slide below says which criterion it serves.

### 0.4 Design system (matches the template)

| Token | Value | Where |
|---|---|---|
| Navy (primary text) | `#003470` | all titles, body text |
| Template orange | `#FF914D` | small accents, highlights in text |
| Template gold | `#FFCD82` | dashed runway line (already in template) |
| CONCORD orange (charts) | `#EB6834` | our series in every chart; key numbers |
| Slate / light slate | `#51627A` / `#A9B4C2` | the two baselines in every chart |
| Card | white, rounded corners, 8–12% transparency optional | every text block sits on a white card so it reads over the sky |
| Title font | **Anton** (already in template) | slide titles |
| Body font | **Inter** (free, Google Fonts) — or the template's Agrandir if you have it | everything else; all generated visuals use Inter |
| Sizes | subheads 24–28 pt bold · body 15–18 pt · captions/sources 11–12 pt | the slide is 20 × 11.25 in, so 16 pt looks like 11 pt on a normal slide |

**Grid used for every position in this file:** slide is 20.00 × 11.25 in; content area starts below the dashed runway line at **y = 2.65 in** and runs to **y = 10.95 in**; left/right margins **0.60 in**; gutters **0.25 in**. Positions are the picture's top-left corner (PowerPoint: *Format Picture → Size & Position → Position*).

---

## Slide 1 — Title

**Serves:** first impression + problem/solution clarity.

| Template field | Put this |
|---|---|
| **Team Name:** | *your team name* (no member names) |
| **PS ID :** | **EL-05** |
| **PS Name :** | **AI-Powered Autonomous Robot & Drone Swarm Mission Orchestration** |
| **Abstract :** | the text below (16 pt, navy; make the first line bold) |

**Abstract (≈75 words — fits the template's abstract card at 16 pt):**

> **CONCORD — the plan will break; the mission stays alive.**
> A mission brain for mixed drone–robot swarms. Operators state a goal in plain English; an LLM turns it into a checked task graph, then deterministic auctions allocate, route and re-plan in milliseconds as agents fail, links drop or storms roll in. A live Monte-Carlo forecast escalates only the hard calls to a human. In 300 simulated disasters, our working prototype aided survivors **12% faster** and cut avoidable drone and robot losses by **46%** versus reactive dispatch.

*Shorter fallback (≈45 words) if the box is tight:* "CONCORD is a mission brain for mixed drone–robot swarms: plain-English goals become checked task graphs; auctions allocate and re-plan in milliseconds; a live forecast escalates only hard calls to humans. Tested on 300 simulated disasters: 12% faster aid, 46% fewer avoidable drone and robot losses."

---

## Slide 2 — PROPOSED SOLUTION

**Judge takeaway:** they understood the PS — mission-level autonomy, not perception — and have a crisp concept with every PS objective covered.
**Serves:** problem understanding & solution clarity.

Replace the three template bullets with the layout below. (The three template prompts are all covered: *core concept* = control loop, *key functionalities* = feature list, *problem–solution alignment* = bottom strip.)

### Layout

| Element | File / type | Position (x, y) in | Size (w × h) in |
|---|---|---|---|
| Sub-headline | text box, Inter Bold 26 pt navy | 0.60, 2.62 | 18.8 × 0.6 |
| Problem card | white rounded rectangle + text (below) | 0.60, 3.40 | 5.35 × 3.20 |
| Survival chart | `slides/s2_survival_by_day.png` | 0.60, 6.75 | 5.35 × 2.90 |
| Core concept | `slides/d_control_loop.png` | 6.60, 3.40 | 6.40 × 6.20 |
| Key functionalities | `slides/d_features.png` | 13.25, 3.40 | 6.15 × 6.20 |
| PS alignment strip | `slides/d_ps_alignment.png` | 0.60, 9.80 | 18.80 × 1.15 |

*Optional photo:* if you want a picture in the problem card, use the Mumbai monsoon photo (Image link **I-2** below) as a 5.35 × 1.4 in strip at the top of the card and shorten the text.

### On-slide text

**Sub-headline:**
> **The plan will break. CONCORD keeps the mission alive.**

**Problem card** (label 13 pt orange caps; body 15 pt navy):
> **THE PROBLEM**
> **26 Jul 2005 · 944 mm of rain in 24 h at Santacruz** — a few km from this campus. ~1,094 dead across Maharashtra; 5 million mobile phones cut off.
> Rescue plans break within minutes — drones fail, bridges fall, links drop, storms roll in — and one human re-plans every robot by hand.

Text inside the visuals (already rendered — for reference/editing):
- **Control loop — "One loop, three owners":** Understand (LLM: plain English → checked task graph) → Allocate (ALGO: auction on capability, battery, risk) → Execute (SWARM: failures, lost links, weather stream in) → Re-plan (ALGO: repair what broke, in ms) → Forecast (ALGO: 40 rollouts → P(success)) → Escalate (HUMAN: only if P < 60% or irreversible). Centre: *The plan will break. The mission stays alive. No LLM between sensing and acting.*
- **Key functionalities:** Mission compiler · Capability-aware auction · Battery-reserve rule · Event-driven re-planning · Comms-aware coordination · Feasibility forecast · Human escalation · Live disruption injector (one line each).
- **PS alignment strip:** Decompose the mission → Mission compiler · Allocate by capability → CBBA-style auction · Re-plan on failures → repair / global re-plan · Reason about comms → relay + value-of-information · Assess risk & feasibility → Monte-Carlo forecast · Escalate & explain → decision cards + log.

### Speaker notes (≈40 s)
"The problem statement is explicit: this is about mission-level autonomy, not object detection or SLAM. Every robot is an abstract agent with position, battery, sensors, payload and radio range, and the job is the brain above them. Real missions break plans — here in Mumbai the 2005 flood took out five million phones in a day — and survival drops from 88% on day one to 9% on day three, so re-coordination speed is the whole game. CONCORD splits the work: an LLM understands intent, deterministic algorithms make every decision in milliseconds, and humans only get the calls that are genuinely risky — with the odds attached. The strip at the bottom maps every PS objective to a component."

**Don't:** call it a "drone app", show robot perception, or let the LLM appear to fly anything.

---

## Slide 3 — TECHNICAL APPROACH

**Judge takeaway:** real algorithms with formulas and measured latency; a layered architecture where the LLM sits outside the control loop.
**Serves:** technical depth & scaling.

### Layout

| Element | File / type | Position (x, y) in | Size (w × h) in |
|---|---|---|---|
| Architecture & workflow | `slides/d_architecture.png` | 0.60, 2.65 | 12.30 × 7.20 |
| Core algorithms | `slides/d_algorithms.png` | 13.15, 2.65 | 6.25 × 7.20 |
| Tech stack strip | `slides/d_tech_strip.png` | 0.60, 9.95 | 18.80 × 1.00 |

### Text inside the visuals (for reference/editing)
- **Architecture:** Operator column (mission console · live map · decision cards · disruption buttons) → **Intent layer (LLM):** ① Mission compiler (goal → typed task graph), Validator + confirm (schema & map checks, human OK), Explainer (decision records → plain reasons) → **Decision layer (deterministic, ms):** ② Allocator (CBBA-style auction · battery-reserve rule), ③ Router (Dijkstra/A* on terrain + storm risk), ⑤ Re-planner (repair vs global · hysteresis), ⑥ Feasibility forecaster (40 Monte-Carlo rollouts), ⑦ Escalation engine (P < 60% or irreversible → card), Comms manager (relay placement · value-of-information queue) → **World layer (one agent interface):** agent interface (get_state · send_plan), ④ Simulator v0 (built), Monitor (telemetry → triggers), Robot bridge (ROS 2 · PX4, next). Bottom: decision log & replay. Badge: **No LLM in the control loop.**
- **Core algorithms:**
  - Bid of agent *i* for task *j*: `score = p_j · e^(−t_ij/τ) − β·E_ij/B_i − γ·risk_ij + δ·[held by i]` — time-discounted reward (CBBA-style) − energy − storm risk + stickiness.
  - Battery-reserve invariant: valid only if `B_i ≥ E(i→j) + E(j) + 1.15·E(j→base) + 5`.
  - Allocation: sequential auction — award the best bid, re-bid only the winner (lazy heap) → O(A·T + T²); decentralised consensus when links drop.
  - Re-planning: **repair** on agent failure, battery, new target; **global** on storm, bridge collapse and every 30 ticks, with a hysteresis bonus δ.
  - Forecast → escalation: K = 40 rollouts sample future failures; escalate when P < 60% or the action is irreversible.
  - Measured on 1 CPU core: repair re-plan **8.6 ms at 200 agents**; full mission tick **0.8 ms**.
- **Stack:** Python · NumPy · Pydantic · OR-Tools · Ollama (local LLM) · FastAPI + WebSocket · React · TypeScript · PixiJS · SQLite · ROS 2 (next) · OpenStreetMap · Docker.

### Speaker notes (≈45 s)
"Read the architecture by the numbers. One: the LLM compiles a plain-English goal into a typed task graph, which is schema-checked and confirmed by the operator — the LLM never touches a motor. Two: agents bid for tasks; the bid rewards finishing high-priority work early and penalises energy and storm risk, and a bid is only valid if the agent can finish the task *and* get home with a 15% reserve. Three: routes avoid storms. Four: the swarm executes. Five: any event — a failure, a collapsed bridge, a lost link — triggers a repair that re-auctions only what broke; a hysteresis bonus stops thrashing. Six: forty Monte-Carlo rollouts forecast the chance of success. Seven: only if that drops below 60%, or the action is irreversible, a human gets a decision card. All of it is logged, which gives us replay and explanations for free."

**Don't:** claim full asynchronous CBBA is done — v0 runs the centralised bundle phase; the decentralised consensus is on the build plan.

---

## Slide 4 — INNOVATION AND UNIQUENESS

**Judge takeaway:** four differentiators, each with proof, and an honest comparison that shows exactly where CONCORD sits.
**Serves:** originality & differentiation.

### Layout

| Element | File / type | Position (x, y) in | Size (w × h) in |
|---|---|---|---|
| Innovation & core differentiators | `slides/d_differentiators.png` | 0.60, 2.65 | 7.50 × 8.30 |
| Comparison with existing approaches | `slides/d_comparison.png` | 8.35, 2.65 | 11.05 × 5.35 |
| Who should plan? (evidence) | `slides/s4_llm_vs_planner.png` | 8.35, 8.15 | 5.60 × 2.80 |
| Real decision log (unique feature) | `slides/d_decision_log.png` | 14.20, 8.15 | 5.20 × 2.80 |

### Text inside the visuals (for reference/editing)
1. **No LLM in the control loop** — the LLM translates intent and explains; a deterministic auction decides in milliseconds. *Proof: no general LLM reaches 5% on obfuscated planning; a classical planner hits 100% in 0.27 s [5]. LLM-driven robots were jailbroken 100% of the time [6].*
2. **Escalation by the numbers** — humans see odds per option, not alarms, and only when it matters. *Proof: storyboard mission: 5 disruptions → 1 human decision; "hold" 0% vs "fly through storm" 72% → all 6 survivors aided.*
3. **Comms-aware autonomy** — relay drone repositions, survivor reports jump the queue, agents keep working when cut off. *Proof: critical reports reach base 10× faster than FIFO dispatch (0.84 vs 8.7 ticks, 300 missions).*
4. **Judges can break it live** — the same disruption hooks drive a 4,500-mission benchmark; nothing is scripted. *Proof: stable plans — 0.12 reassignments per mission vs 3.85 without hysteresis.*

**Comparison matrix** (● documented core capability · ◐ partial / limited scope · — not publicly documented; from public product pages and papers, Sep 2026):

| Capability | CONCORD | FlytBase | DJI FlightHub 2 | Open-RMF | Auterion Nemyx | Anduril Lattice | LLM planners (SMART-LLM) | CBBA (MIT 2009) |
|---|---|---|---|---|---|---|---|---|
| Air + ground, mixed fleet | ● | ◐ | ◐ | ◐ | ◐ | ● | ◐ | ● |
| Plain-language mission | ● | — | — | — | — | — | ● | — |
| Re-allocates on failure | ● | — | — | ◐ | ◐ | ● | — | ● |
| Comms-aware (relay, VoI) | ● | ◐ | ◐ | — | ◐ | ◐ | — | ◐ |
| Forecast → human escalation | ● | — | — | — | — | — | — | — |
| Explained decision log | ● | ◐ | ◐ | ◐ | — | — | ◐ | — |
| Open · civilian · laptop | ● | ◐ | ◐ | ● | — | — | ● | ● |
| **Proven on hardware** *(our honest gap)* | ◐ | ● | ● | ● | ● | ● | ◐ | ● |

### Speaker notes (≈40 s)
"Most swarm demos show robots following a plan. Ours shows a swarm that keeps its mission alive when the plan breaks. Four things are new together. First, no LLM in the loop — the research is clear that LLMs are not reliable planners and are easy to jailbreak, so ours only translates and explains. Second, escalation is quantified: the operator sees each option's probability of success, from rollouts. Third, we treat communication as a resource — the relay drone moves, and a survivor report outranks telemetry. Fourth, it is un-scriptable: judges can break it live, and the same hooks power a 4,500-mission benchmark. The matrix is honest: fleet tools fly drones, defence stacks are closed, research planners stop at the plan — and the one row where others beat us is real hardware, which is our next step."

**Don't:** mark competitors with ✗. "—" means *not publicly documented*, which is defensible; "does not have" is not.

---

## Slide 5 — PROTOTYPE AND EVIDENCE *(the optional extra slide)*

**Judge takeaway:** it exists, it works, and it measurably beats the obvious alternatives — with confidence intervals.
**Serves:** quality of prototype & research; technical depth.

Make this slide by duplicating the TECHNICAL APPROACH slide and changing the title to **PROTOTYPE AND EVIDENCE**.

### Layout

| Element | File / type | Position (x, y) in | Size (w × h) in |
|---|---|---|---|
| Live console (real simulation state at t = 86) | `slides/s5_console_escalation.png` | 0.60, 2.65 | 9.50 × 5.34 |
| KPI tiles | `slides/d_kpi_tiles.png` | 0.60, 8.15 | 9.50 × 2.10 |
| Caption with links | text box, Inter 13 pt | 0.60, 10.30 | 9.50 × 0.60 |
| Benchmark (300 scenarios) | `slides/s5_benchmark_kpis.png` | 10.35, 2.65 | 9.05 × 3.95 |
| Stress sweep | `slides/s5_stress_sweep.png` | 10.35, 6.75 | 9.05 × 4.20 |

**Caption text (put real links in; add QR codes on slide 8):**
> ▶ 15-second demo: `<your YouTube/Drive link>` · Code + 4,500-mission benchmark: `github.com/<neutral-org>/concord` · runs on one laptop CPU, every mission seeded

### Text inside the visuals (for reference)
- **Console still:** Rover-1 has failed; a storm cell sits over sector C where survivors S2, S3, S6 wait; the escalation card offers **A) Hold** — P(success) 0% and **B) Fly Cargo-1 through the storm** — P(success) 72%, recommended; safe default on timeout: B. Right panel: live P(success) gauge, swarm battery/link status, auto-explained decision log.
- **KPI tiles:** **−12%** time-to-aid vs reactive dispatch · **10×** faster critical reports (0.84 vs 8.7 ticks) · **−46%** avoidable asset losses (0.11 vs 0.20 per mission) · **96%** success with 6 disruptions (vs 88% greedy, 16% static).
- **Benchmark chart (300 randomised disruption scenarios, same seeds for every policy, mean ± 95% CI):** time-to-aid 62.4 / 71.1 / 174.2 ticks · critical-report delay 0.8 / 8.7 / 8.1 ticks · avoidable losses 0.11 / 0.20 / 0.22 per mission · mission success 99% / 96% / 20% (CONCORD / greedy dispatch / static plan).
- **Stress sweep (100 missions per point):** with 0 → 6 simultaneous disruption types, success stays 100% → 96% for CONCORD vs 100% → 88% greedy and 43% → 16% static; avoidable losses 0.12 vs 0.37 vs 0.35 at six.

### What the two baselines are (say this if asked — it is what makes the numbers credible)
- **Greedy dispatch:** each idle capable agent takes the nearest open task; smart return-to-home (same safety rule as CONCORD); fixed relay; first-in-first-out messaging. This is what a sensible fleet tool does today.
- **Static plan:** a good one-shot allocation at t = 0, executed with the same return-to-home; new tasks go to the nearest capable agent; no re-allocation after failures.
- Both see **exactly the same scenarios and the same random draws** as CONCORD (paired comparison).

### Speaker notes (≈40 s)
"We didn't just design this — we built v0 and tried to break it. This is a real frame from the simulator: the rover has just failed, a storm sits over the three remaining survivors, and holding back gives a 0% chance of finishing in time, while flying the last cargo drone through the storm gives 72% — so CONCORD asks the operator. Across 300 randomised disasters with the same seeds for every policy, CONCORD reaches survivors 12% faster than greedy dispatch, gets critical findings to base ten times faster, and loses 46% fewer drones and robots to avoidable causes like storms and flat batteries. And the gap grows as things get worse: at six simultaneous disruption types, success is 96% versus 88% and 16%."

**Honesty notes (keep them in your pocket):** v0 is a grid world with abstract agents; 1 tick ≈ 10 s is our interpretation; greedy already reaches 96% success in the default scenarios, so our headline is speed, safety and stability, not "greedy fails".

---

## Slide 6 — FEASIBILITY AND VIABILITY

**Judge takeaway:** this team can ship — the core already runs, the 36-hour plan is concrete, and every big risk has a tested mitigation.
**Serves:** technical depth & scaling; quality of prototype.

### Layout

| Element | File / type | Position (x, y) in | Size (w × h) in |
|---|---|---|---|
| Feasibility & viability card | `slides/d_feasibility.png` | 0.60, 2.65 | 6.00 × 8.30 |
| 36-hour build plan (Gantt) | `slides/d_gantt.png` | 6.85, 2.65 | 12.55 × 4.35 |
| Challenges & risks | `slides/d_risks.png` | 6.85, 7.15 | 12.55 × 3.80 |

### Text inside the visuals (for reference/editing)
- **Technical feasibility — already proven:** v0 works today (1,272-line simulator, CONCORD + 2 baselines, forecaster, renderer) · 4,500 seeded missions run, 0 crashes, fully reproducible · runs offline on a 2-core laptop CPU — no GPU, no cloud.
- **Operational feasibility:** operator stays in charge (confirm the task graph, approve escalations) · same agent interface for simulator, ROS 2 and PX4 SITL.
- **Resources & deployment:** team of 4 × 36 h, one laptop each · open-source stack, ₹0 infrastructure, local LLM optional · one Docker image, browser console.
- **Sustainability & viability:** open-core (free engine + simulator; paid fleet console & integrations) · pilot path: SDRF / municipal flood cells → NDRF · guardrails: civilian-first, human approval for irreversible acts, no weapon payloads.
- **Gantt (36 h):** World — live engine + WebSocket (2–8 h), real Mumbai map from OSM (18–24 h), 1k-seed run (28–31 h) · Allocation — async CBBA (2–8), OR-Tools routing (12–18), churn tuning (24–28), scale test (28–31) · Autonomy — trigger API (2–8), escalation cards (12–18), comms view (18–24), calibration (24–28) · Product — PixiJS map (2–8), disruption buttons (12–18), LLM compiler (18–24), explainer (24–28), pitch & Q&A (31–36) · All hands — specs (0–2), integration (8–12), dry runs (31–34). Milestones: integrate at 12 h, freeze at 31 h.
- **Risks:** too much scope (High/High → v0 already runs the core; hour-12 gate; cut list) · bug live on stage (Med/High → 4,500 seeded missions fuzzed; invariant tests; 10 dry runs; backup video) · sim-to-real gap (High/Med → one agent interface → ROS 2 / PX4 SITL; physics out of PS scope) · venue internet fails (Med/Med → local Ollama + preset task graphs + templates) · bad task graph from the LLM (Med/Low → schema-constrained output → validator → human confirm → preset).

**Cut list (say it if asked):** ablation re-runs → replay scrubber → OR-Tools (keep insertion heuristic) → LLM explainer (keep templates). **Never cut:** disruption buttons, battery-reserve rule, repair re-planning, relay repositioning, one escalation card, the baseline benchmark chart.

### Speaker notes (≈35 s)
"Feasibility is not a promise here — v0 already runs the allocator, re-planner, comms manager, forecaster and benchmark, on a laptop CPU with no GPU and no cloud. The 36 hours go into the live product: a WebSocket engine, the map UI with judge buttons, the LLM compiler, asynchronous consensus for cut-off agents and a real Mumbai map. We integrate at hour 12 and freeze at hour 31. The biggest risk is a bug on stage, and we've already fuzzed 4,500 seeded missions."

**Check your event rules** on reusing pre-built code in the offline round; if it is not allowed, present v0 as the validated design and rebuild the core in the first 12 hours (the Gantt already assumes that pace).

---

## Slide 7 — IMPACT AND SCALING

**Judge takeaway:** clear users, measurable benefits, and a concrete answer to "YC says yes tomorrow".
**Serves:** technical depth & scaling; problem understanding.

### Layout

| Element | File / type | Position (x, y) in | Size (w × h) in |
|---|---|---|---|
| Target users & applications | `slides/d_users.png` | 0.60, 2.65 | 9.00 × 3.60 |
| Swarm robotics market | `slides/s7_market.png` | 0.60, 6.40 | 4.30 × 2.90 |
| Expected impact & key benefits | `slides/d_impact.png` | 5.05, 6.40 | 4.55 × 2.90 |
| Why now | `slides/d_why_now.png` | 0.60, 9.50 | 9.00 × 1.35 |
| "YC says yes tomorrow" | `slides/d_scale_out.png` | 9.85, 2.65 | 9.55 × 5.10 |
| Re-plan time vs swarm size | `slides/s7_scaling_latency.png` | 9.85, 7.90 | 4.70 × 3.05 |
| Tested to survive success | `slides/d_testing.png` | 14.85, 7.90 | 4.55 × 3.05 |

### Text inside the visuals (for reference/editing)
- **Users:** Disaster response (NDRF: 16 battalions, 1,038 operations in 2024; SDRFs; fire services) · Infrastructure inspection (power lines, pipelines, bridges) · Mining & industrial safety · Agriculture fleets (15,000 drones to women SHGs under Namo Drone Didi) · Maritime & coastal SAR · Cities & municipalities (monsoon flood response, e.g. Mumbai's BMC wards).
- **Market:** swarm robotics US$1.1 B (2024) → US$6.2 B (2030), CAGR 33%.
- **Impact:** −12% faster aid · −46% fewer lost assets · 1 of 5 calls goes to a human (storyboard) · 100% of decisions explained.
- **Why now:** FAA Part 108 BVLOS proposal (Aug 2025): automated flight with human supervisors · India: Drone Rules 2021 and the Digital Sky green/yellow/red airspace map · drone flights up 25% in 2024 (15.5 M → 19.5 M).
- **YC says yes tomorrow:** 10× more missions → stateless gateway + one worker per mission; 0.8 ms per mission tick → ~250 live missions per core *(estimate)* · 100+ agents → repair re-plan 8.6 ms at 200 agents; global re-plans run in the background · a server crashes → agents keep their task bundles; a standby worker replays the event log · cloud link drops → edge gateway runs decentralised CBBA; on-board battery-reserve rule · LLM outage → zero control impact · bad release → CI replays the 300-mission benchmark and blocks regressions.
- **Scaling chart:** repair re-plan 0.16 ms (5 agents) → 8.6 ms (200 agents); global re-plan 0.8 ms → 2.4 s (1 core, pure Python).
- **Testing:** property-based tests (no double-assignment, reserve never violated, DAG order kept) · simulation regression (300 seeded missions per pull request) · chaos testing (the disruption injector doubles as a chaos monkey) · load testing (k6: 1,000 live viewers, 1,000 simulated agents) · badge: 4,500 missions · 0 crashes.

### Speaker notes (≈45 s)
"Who uses this? First, disaster responders — NDRF alone ran over a thousand operations last year — then infrastructure inspection, mining, agriculture co-ops with fifteen thousand new drones, coastal search, and city flood cells like Mumbai's. The benefit is measurable: faster aid, fewer lost drones and robots, fewer decisions dumped on a human, and an explanation for every decision. And if YC says yes tomorrow: missions are independent, so they shard one per worker; each tick costs under a millisecond; a repair re-plan at 200 agents takes 8.6 ms; if a server dies, agents keep flying their bundles and a standby worker replays the log. Every pull request re-runs our 300-mission benchmark, and the disruption injector doubles as our chaos monkey."

**Don't:** present the ~250 missions/core figure as measured — it is an estimate derived from the measured 0.8 ms tick.

---

## Slide 8 — RESEARCH AND REFERENCES

**Judge takeaway:** the design stands on published evidence, and every link opens.
**Serves:** quality of research, prototype and presentation.

### Layout

| Element | File / type | Position (x, y) in | Size (w × h) in |
|---|---|---|---|
| Research background & evidence | `slides/d_evidence.png` | 0.60, 2.65 | 6.50 × 8.30 |
| References (numbered, clickable) | white card + text, Inter 10.5–11 pt, two columns | 7.35, 2.65 | 7.10 × 8.30 |
| Demo, GitHub & supporting links | white card + text + 2 QR codes (1.4 in) | 14.70, 2.65 | 4.70 × 8.30 |
| *(optional)* 3 precedent thumbnails | Image links I-5, I-6, I-7, each 1.45 in wide | inside the links card, bottom | — |

Make QR codes with `make_qr.py` (in the prototype zip): `python make_qr.py "<url>" repo` → `qr_repo.png`. Scan each with a phone before submitting.

### Evidence card text (for reference — already in `d_evidence.png`)
1. **Every hour counts** — survival of trapped people: 88% day 1 → 35% day 2 → 9% day 3 **[1]**
2. **Comms fail first** — 95% of cell sites down after Hurricane Maria; 5 M mobile users cut off in Mumbai, 26 Jul 2005 **[2, 3]**
3. **Humans are the bottleneck** — DARPA SubT allowed one human supervisor per robot team; the winner's operator errors were "a significant fraction of mistakes" **[4]**
4. **LLMs are not planners** — no LLM reaches 5% on obfuscated planning; a classical planner hits 100% in 0.27 s; LLM-driven robots jailbroken 100% **[5, 6, 7]**
5. **Auctions are proven** — CBBA is conflict-free and robust to inconsistent information and changing comms **[8, 9]**
6. **Regulation wants supervised autonomy** — FAA Part 108 proposal: automated flight, trained human supervisors **[10]**

### References card (type these; make each title a hyperlink)
1. Roces M.C. et al. (1992). Risk factors for injuries due to the 1990 earthquake in Luzon, Philippines. *Bull. WHO* 70(4). — <https://pubmed.ncbi.nlm.nih.gov/1394785/> · summary: <https://sites.pitt.edu/~super1/lecture/lec32971/007.htm>
2. FCC status report on Hurricane Maria, 21 Sep 2017 (95% of cell sites out). — <https://convergedigest.com/fcc-95-of-cell-sites-down-in-puerto-rico/>
3. Maharashtra floods of 2005. — <https://en.wikipedia.org/wiki/Maharashtra_floods_of_2005>
4. Tranzatto M. et al. (2024). Team CERBERUS Wins the DARPA Subterranean Challenge: Technical Overview and Lessons Learned. *Field Robotics*. — <https://arxiv.org/abs/2207.04914> · DARPA results: <https://www.darpa.mil/news/2021/subterranean-challenge-winners>
5. Valmeekam K., Stechly K., Kambhampati S. (2024). LLMs Still Can't Plan; Can LRMs? — <https://arxiv.org/abs/2409.13373>
6. Robey A. et al. (2024). Jailbreaking LLM-Controlled Robots. — <https://arxiv.org/abs/2410.13691>
7. Kambhampati S. et al. (2024). LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks. *ICML*. — <https://arxiv.org/abs/2402.01817>
8. Choi H.-L., Brunet L., How J.P. (2009). Consensus-Based Decentralized Auctions for Robust Task Allocation. *IEEE T-RO* 25(4):912–926. — <https://doi.org/10.1109/TRO.2009.2022423>
9. Dias M.B., Zlot R., Kalra N., Stentz A. (2006). Market-Based Multirobot Coordination: A Survey and Analysis. *Proc. IEEE* 94(7):1257–1270. — <https://doi.org/10.1109/JPROC.2006.876939>
10. FAA (2025). Normalizing Unmanned Aircraft Systems Beyond Visual Line of Sight Operations (Part 108 NPRM). *Federal Register* 90(150). — <https://www.govinfo.gov/content/pkg/FR-2025-08-07/html/2025-14992.htm>
11. Gerkey B., Matarić M. (2004). A formal analysis and taxonomy of task allocation in multi-robot systems. *IJRR* 23(9). — <https://doi.org/10.1177/0278364904045564>
12. Queralta J.P. et al. (2020). Collaborative Multi-Robot Search and Rescue: Planning, Coordination, Perception, and Active Vision. *IEEE Access* 8. — <https://arxiv.org/abs/2008.12610>
13. Legay A., Delahaye B., Bensalem S. (2010). Statistical Model Checking: An Overview. *RV 2010*. — <https://doi.org/10.1007/978-3-642-16612-9_11>
14. Parasuraman R., Sheridan T., Wickens C. (2000). A model for types and levels of human interaction with automation. *IEEE SMC-A* 30(3). — <https://doi.org/10.1109/3468.844354>
15. CRED / EM-DAT (2025). 2024 Disasters in Numbers. — <https://www.preventionweb.net/quick/93926>
16. NDRF (2025). 20th Raising Day. — <https://www.ndrf.gov.in/en/node/90366>
17. MarketGlass / Global Industry Analysts (2025). Swarm Robotics (via GII Research). — <https://www.giiresearch.com/report/go1788365-swarm-robotics.html>

*(More references — MAPF, Dec-MCTS, explainable planning, drone energy models — are in the dossier if you want a second column.)*

### Links card (type these; make each a hyperlink)
- **GitHub (code + benchmark):** `github.com/<neutral-org>/concord` + QR
- **Demo video (15 s run + escalation):** `<YouTube unlisted / Drive viewer link>` + QR
- **Benchmark data:** `results/summary.json` in the repo
- **Datasets & tools we build on:** Moving AI MAPF benchmark maps · OpenStreetMap / OSMnx · OpenCelliD (cell towers → comm coverage) · Copernicus EMS rapid mapping · ISRO Bhuvan · PX4 SITL + Gazebo · ROS 2 · Open-RMF · Google OR-Tools
- **Competitors reviewed:** FlytBase · DJI FlightHub 2 · Open-RMF · Auterion Nemyx · Anduril Lattice · SMART-LLM
- **Precedents (thumbnails):** NASA Perseverance + Ingenuity (heterogeneous team on Mars) · NASA JPL CADRE (3 cooperating Moon rovers) · DARPA SubT Challenge (air + ground teams underground)

### Speaker notes (≈20 s)
"Everything we claim is either measured in our prototype or cited here — survival data, communication failures, the single-supervisor rule in DARPA SubT, the evidence that LLMs shouldn't be planners, and the auction literature we build on. The code, the benchmark and the demo are one scan away."

---

## Image links (checked 30 Sep 2026)

All of these opened and are free to use under the stated licence. Credit small, in 9–10 pt grey, under the image.

| ID | Image | Link | Licence / credit | Suggested use |
|---|---|---|---|---|
| I-1 | Two drones in a pale sky — a heavy-lift drone carrying solar panels next to a small quadcopter (heterogeneous pair) | <https://unsplash.com/photos/drones-are-flying-in-a-cloudy-blue-sky-FQa5xUZlAUo> | Unsplash License · Photo: Valentin Zickner | Slide 1 or 2 accent — matches the template's sky |
| I-2 | Mumbai municipal HQ reflected on a rain-soaked street (monsoon) | <https://unsplash.com/photos/brihanmumbai-municipal-corporation-building-in-mumbai-fUOMWdwuuvw> | Unsplash License · Photo: Satyajeet Mazumdar | Slide 2 problem card strip (local hook) |
| I-3 | Mumbai rain seen from inside an auto-rickshaw | <https://unsplash.com/photos/rainy-day-view-from-an-auto-rickshaw-q7ZP_49Lq5g> | Unsplash License · Photo: Saad Ahmad | Alternative to I-2 |
| I-4 | Rescue workers evacuating people by boat in a flood *(Jakarta, 2025 — do not caption as India)* | <https://unsplash.com/photos/rescue-workers-navigate-floodwaters-in-a-boat-_hlDpQwfQnY> | Unsplash License · Photo: Iqro Rinaldi | Slide 2 or 7 (disaster response) |
| I-5 | NASA Perseverance rover's selfie with the Ingenuity helicopter (PIA24542) | page: <https://science.nasa.gov/photojournal/perseverances-selfie-with-ingenuity/> · full-res JPG: <https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia24/pia24542/PIA24542.jpg> | NASA (public domain) · Credit: NASA/JPL-Caltech/MSSS | Slide 8 precedent: air + ground team |
| I-6 | NASA JPL CADRE — three cooperating lunar rovers | page: <https://www.jpl.nasa.gov/missions/cadre> · image: <https://d2pn8kiwq2w21t.cloudfront.net/images/cadre-mission-gradient3_riQgUnN.height-1024.jpg> | NASA/JPL-Caltech | Slide 8 precedent: multi-robot autonomy |
| I-7 | DARPA SubT Challenge final — Team CERBERUS wins | page: <https://www.darpa.mil/news/2021/subterranean-challenge-winners> · image: <https://www.darpa.mil/sites/default/files/styles/wide_816/public/subt-finals-announcement-619.png?itok=ESRAsN8J> | Source: DARPA | Slide 8 precedent: comms-degraded teams |
| I-8 | Drone spraying crop rows | <https://unsplash.com/photos/drone-spraying-green-crop-field-nMDwrS1NsIE> | Unsplash License · Photo: DRONE EFT | Slide 7 agriculture tile (optional) |
| I-9 | Power transmission tower, low angle | <https://unsplash.com/photos/low-angle-photo-of-transmission-post-08ai5EDtn9k> | Unsplash License · Photo: Jonathan Hanna | Slide 7 infrastructure tile (optional) |
| I-10 | Tabler Icons (drone, robot, antenna, battery, storm, route…) | <https://tabler.io/icons> — 72 PNGs already exported in `icons/` | MIT licence | anywhere |
| I-11 | Tech logos (Python, FastAPI, React, ROS…) | <https://simpleicons.org> · e.g. <https://cdn.simpleicons.org/fastapi/003470> (any logo, any hex colour) | CC0 (brand guidelines apply) | already composed in `d_tech_strip.png` |

Avoid "Unsplash+" images (paywalled) and any image of a real organisation's logo used as if endorsing you.

---

## Numbers cheat-sheet (every number on the slides, with where it comes from)

| Claim on the slides | Exact value | Source |
|---|---|---|
| Faster aid | −12.2% mean time-to-aid (62.4 vs 71.1 ticks; paired Δ −8.7, 95% CI −10.1 to −7.4) | v0 benchmark, 300 scenarios |
| vs static plan | −64% (62.4 vs 174.2 ticks) | v0 benchmark |
| Faster critical reports | 10.4× (0.84 vs 8.71 ticks) | v0 benchmark |
| Fewer avoidable losses | −45.8% (0.107 vs 0.197 per mission; paired Δ −0.090, CI −0.143 to −0.037) | v0 benchmark |
| Mission success | 99.0% vs 96.3% vs 20.0% | v0 benchmark |
| Survivors aided within 120 ticks | 93.3% vs 88.2% vs 41.8% (median 59 vs 66 vs 157 ticks; survivors never reached count as not aided) | v0 benchmark, 1,676 survivors |
| Energy | −5.2% vs greedy; −13.4% vs static | v0 benchmark |
| Stress (6 disruption types) | success 96% / 88% / 16%; avoidable losses 0.12 / 0.37 / 0.35 | v0 stress sweep, 100 per level |
| Plan stability | 0.12 reassignments per mission (3.85 without hysteresis) | v0 ablation |
| Risk-aware routing | avoidable losses 0.107 → 0.187 without it (1.75× more) | v0 ablation |
| VoI messaging | report delay 0.84 → 4.37 ticks without it (5.2×) | v0 ablation |
| Repair re-plan at 200 agents | 8.6 ms (global 2.4 s), 1 core, pure Python | v0 scaling test |
| Mission tick | 0.79 ms (mean over 300 missions of wall time ÷ ticks; ≈131 ms per whole mission) | v0 benchmark wall time |
| ~250 missions per core | 1000 ms ÷ 0.79 ms per tick ÷ 5 ticks/s per live mission (the sped-up console rate; at 1 tick ≈ 10 s of real time the headroom is far larger) — **estimate** | derived |
| Storyboard | 5 disruptions → 1 escalation; hold 0% vs fly-through 72% (29 of 40 rollouts); all 6 survivors aided by t = 162 | v0 storyboard, seed 6 |
| 4,500 missions, 0 crashes | 900 main + 2,100 stress + 1,500 ablation, all completed | v0 benchmark run |
| 944 mm; ~1,094 dead; 5 M mobile users cut off | 26 Jul 2005, Santacruz | Wikipedia, Maharashtra floods of 2005 |
| 88% → 35% → 9% → 0% | survival among trapped, by day, 1990 Luzon earthquake | Roces et al. 1992 via Pitt Supercourse |
| 95% of cell sites down | Puerto Rico, 21 Sep 2017 | FCC via Converge Digest |
| <5% / 52.8% / 100% | best LLM / o1-preview / Fast Downward on Mystery Blocksworld (0.265 s per problem) | Valmeekam et al. 2024 |
| 100% jailbreak | RoboPAIR on Unitree Go2, Clearpath Jackal, NVIDIA Dolphins | Robey et al. 2024 |
| 16 battalions; 1,038 operations in 2024 | NDRF | ndrf.gov.in |
| 15,000 drones; ₹1,261 crore | Namo Drone Didi (women SHGs) | Cabinet approval |
| US$1.1 B → 6.2 B, 33% CAGR | swarm robotics 2024 → 2030 | MarketGlass (Global Industry Analysts) via GII |
| 15.5 M → 19.5 M drone flights (+25%) | 2023 → 2024 | Drone Industry Insights |
| Part 108 NPRM | published 7 Aug 2025; final rule under OIRA review since 10 Jul 2026, not yet published (late Sep 2026) | Federal Register; FlyUSI / DroneAuthority trackers |

---

## Before you submit — checklist

- [ ] Exactly 8 slides; INSTRUCTIONS slide and blank 9th slide deleted
- [ ] No member names anywhere (slides, speaker notes, file properties, GitHub/YouTube usernames). *File → Info → Properties → Author*: clear it
- [ ] Every link opens in an incognito window; QR codes scan from a phone
- [ ] Numbers on slides match the cheat-sheet exactly (no rounding drift between slides)
- [ ] PDF export checked: fonts embedded (*Options → ISO 19005-1* or "embed fonts"), images sharp at 200% zoom
- [ ] File named `EL-05_<TeamName>.pdf` (or .pptx)
- [ ] Credits under photos (Unsplash / NASA / DARPA)
- [ ] One person reads the deck cold in 90 seconds and can say what CONCORD does and why it's better
