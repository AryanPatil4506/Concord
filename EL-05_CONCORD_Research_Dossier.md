# CONCORD (EL-05) — Research dossier & defence kit

*For the team, not the slides.* This is the evidence behind every slide, the full prototype results, the competitor notes, and the answers to the questions judges will ask. Keep it open during Q&A prep.

---

## 1. The PS decoded — and how the deck scores against the rubric

The single most important sentence in EL-05:

> *"The objective is to demonstrate mission-level autonomy and swarm coordination, rather than solving an isolated capability such as object detection, SLAM, or obstacle avoidance."*

So every robot is an abstract agent (position, speed, battery, sensors, payload, radio range) and the job is the brain above them. The PS contains six sub-problems; the deck shows one component for each:

| PS objective / deliverable | CONCORD component | Evidence in the deck |
|---|---|---|
| Convert high-level objectives into coordinated tasks, dependencies, priorities | Mission compiler → typed Mission DAG (LLM + schema + human confirm) | Slide 2 loop, slide 3 architecture |
| Allocate by capability, location, battery, payload, comms, risk, priority | CBBA-style auction with time-discounted bids + battery-reserve invariant | Slide 3 formula; slide 5 results |
| Re-plan on failures, obstacles, environment, new info, priorities | Event-driven repair vs global re-plan with hysteresis | Slide 5 stress sweep; ablation |
| Communication-aware; decide what's worth transmitting | Relay repositioning, value-of-information queue, report-seeking detour, disconnected autonomy | Slide 4 (10× faster critical reports) |
| Identify when the mission is no longer safely achievable; escalate | Monte-Carlo feasibility forecast → escalation card with P(success) per option | Slide 5 console still; storyboard |
| ≥3 heterogeneous agents | 4 agent types: scout drone ×2, cargo drone, rover (UGV), relay drone | Slide 5 console |
| Explanations for major autonomous decisions | Structured decision log rendered as one-line reasons | Slide 4 real log excerpt |

| Judging criterion | Where the deck earns it |
|---|---|
| Problem understanding & solution clarity | Slide 2 (PS decoded + alignment strip), slide 1 abstract |
| Technical depth & scaling | Slide 3 (formulas, complexity), slide 7 (scale-out + measured latency) |
| Originality & differentiation | Slide 4 (four differentiators + honest comparison) |
| Quality of research, prototype & presentation | Slide 5 (working v0, 4,500 missions, CIs), slide 8 (references), consistent visual system |

---

## 2. What changed from the teammate's proposal — and why

The teammate's EL-05 proposal (CONCORD) is the backbone and its design principle is kept verbatim: **"LLMs understand intent. Algorithms make decisions. Humans own the hard calls."** Changes made for the submission:

1. **Built v0 instead of promising it.** The proposal's own rule was "fill with real numbers — never estimate them". The benchmark slide now carries measured numbers from 4,500 seeded missions with bootstrap CIs.
2. **Added a cargo drone** (1 kit, weather-sensitive) next to the rover (3 kits, terrain-bound). This creates real allocation trade-offs (fast-but-fragile vs slow-but-robust) and is what makes the storyboard escalation meaningful.
3. **Honest baselines.** Greedy got the same smart return-to-home as CONCORD, so the comparison is not a strawman. Result: greedy is strong on success (96%) — our headline is speed, safety and stability, not "greedy fails".
4. **Bid function uses time-discounted reward** (the CBBA-standard form, `p·e^(−t/τ)`), which naturally balances load across agents; energy and storm risk are separate penalties; stickiness δ implements hysteresis.
5. **Relay rule tightened** during testing: the relay must keep a direct link to base (an early version chased transient chains through moving agents and hurt latency — caught by the ablation).
6. **Ablations are reported even when they're unflattering** (the battery invariant shows no measurable gain in v0; hysteresis costs ~8% energy).
7. **Deck structure uses the extra slide for PROTOTYPE AND EVIDENCE**, because "quality of prototype" is an explicit judging criterion.

---

## 3. The prototype (v0) — design, baselines, statistics, limits

### 3.1 World
- 40 × 28 grid (≈ 2 × 1.4 km if a cell is 50 m). Base on the west bank; a river with two bridges; 3 flood pockets; up to 18 building blocks (ground-impassable); four survey sectors A–D east of the river (24 survey waypoints).
- 5 hidden survivors (6 in the storyboard), found by scout cameras (Chebyshev radius 2).
- Comms: link if distance ≤ max(range_a, range_b); base range 14, relay 16, scouts/cargo 7, rover 6; mesh connectivity by BFS; dead zones block links; each connected agent uplinks 2 messages per tick; every agent produces 1 telemetry message per tick (so a disconnected agent builds a backlog).
- Storm: disc of radius 5.5 for 70 ticks (80 in the storyboard); aerial agents inside fly at half speed and are lost with probability 0.04 per tick.
- Energy: per cell moved (cargo +25% while loaded) and per tick hovering; recharge at base.
- Mission horizon 320 ticks (200 in the storyboard); success = every survivor aided by the horizon.

### 3.2 Agents
| Agent | Count | Caps | Speed (cells/tick) | Battery | Comm | Notes |
|---|---|---|---|---|---|---|
| Scout drone | 2 | camera | 2.0 | 110 | 7 | fast, short battery, weather-sensitive |
| Cargo drone | 1 | payload (1 kit) | 1.5 | 120 | 7 | fast delivery, reload at base each trip |
| Rover (UGV) | 1 | payload (3 kits) | 1.0 | 500 | 6 | slow, robust, terrain-bound (bridges) |
| Relay drone | 1 | relay | 1.5 | 220 | 16 | extends base link |

### 3.3 Disruptions (seeded, per scenario)
Agent hardware failure (p = 0.6), sudden battery drain −45% of capacity (0.6), bridge collapse (0.5), comm blackout disc r = 4 (0.5), storm (0.5), new target from an emergency call (0.6). Each type at most once; 0–6 per mission, **3.2 on average** in the main benchmark.

### 3.4 Policies
- **CONCORD:** sequential greedy auction with time-discounted bids (τ = 120), energy penalty β = 0.05, risk penalty γ = 1.0, stickiness δ = 0.08, max bundle 6; bids must satisfy the battery-reserve invariant (finish + return × 1.15 + 5); via-base option lets agents plan recharge/reload stops; risk-aware Dijkstra routing (entering a storm cell costs 1 + 100 × hazard) and a task-risk ceiling of 0.12; repair auctions on events, global re-plan on storm/bridge events and every 30 ticks; relay placement every 5 ticks maximising weighted connectivity (VoI-holders weighted 3×); VoI message priority (survivor report > telemetry); report-seeking detour ≤ 12 cells when holding a critical report in a dead zone.
- **Greedy dispatch:** nearest open task to each idle capable agent; same smart return-to-home; fixed relay station; FIFO messages.
- **Static plan:** one-shot allocation of all known tasks at t = 0; same return-to-home, resumes its list; new deliveries appended to the nearest capable agent; no re-allocation after failures; fixed relay; FIFO.

### 3.5 Metrics & statistics
Time-to-aid (delivery tick − appearance tick, censored at horizon), critical-report latency (detection → base awareness), avoidable asset losses (storm + battery depletion; injected hardware failures excluded), mission success, survivors aided, energy, reassignments (churn), wall time. Paired design: identical seeds and identical pre-drawn random numbers per agent per tick for all policies. 95% CIs by bootstrap (4,000 resamples); paired differences reported for CONCORD − greedy.

### 3.6 Honest limits (say these before a judge does)
1. Grid world, abstract agents, no physics — by design (PS scope) but still a simulation.
2. The auction is centralised when agents are connected; decentralised CBBA consensus is on the build plan.
3. The forecaster samples future disruptions from the same prior the benchmark uses, so its calibration is optimistic by construction; real deployments would learn hazard rates from history.
4. The battery-reserve invariant shows no measurable benefit in v0 because the smart return-to-home safety net already catches most cases (the invariant's value is proactive: no aborted sorties; test with gradual drains/headwinds next).
5. 1 tick ≈ 10 s is an interpretation, not a calibrated constant.
6. Escalations were measured only in the storyboard, not across the benchmark (operator load across 300 missions is future work).

### 3.7 Reproduce
`pip install numpy matplotlib pillow` → `python run_benchmark.py && python analyze.py` (≈4 min on 2 cores) → `python scaling.py` → `python storyboard.py 6 && python make_demo.py` → `python figures.py` / `python slide_charts.py`. Diagrams: `diagrams/build_slide_html.py` + `render_slides.py` (needs Playwright + Chromium).

---

## 4. Full results

### 4.1 Main benchmark — 300 random scenarios, 1,676 survivors (mean [95% CI])
| Metric | CONCORD | Greedy dispatch | Static plan |
|---|---|---|---|
| Mission success | **99.0%** [97.7, 100] | 96.3% [94.0, 98.3] | 20.0% [15.7, 24.7] |
| Survivors aided | **99.8%** | 99.2% | 62.0% |
| Mean time-to-aid (ticks) | **62.4** [60.8, 64.1] | 71.1 [68.9, 73.3] | 174.2 [169.5, 178.9] |
| Median time-to-aid (ticks; never-reached survivors count as not aided) | **59** | 66 | 157 |
| Aided within 120 ticks | **93.3%** | 88.2% | 41.8% |
| Critical-report latency (ticks) | **0.84** [0.76, 0.92] | 8.71 [8.25, 9.18] | 8.09 [7.69, 8.50] |
| Avoidable asset losses / mission | **0.107** [0.073, 0.143] | 0.197 [0.147, 0.250] | 0.223 [0.173, 0.277] |
| All asset losses / mission (incl. injected) | 0.69 | 0.78 | 0.80 |
| Energy used | **579** | 611 | 668 |
| Reassignments / mission | 0.12 | – | – |
| Wall time per mission | 131 ms | 31 ms | 38 ms |

Paired CONCORD − greedy: time-to-aid −8.66 ticks [−10.05, −7.37]; report latency −7.87 [−8.28, −7.45]; avoidable losses −0.090 [−0.143, −0.037]; success +2.7 pts [+0.7, +4.7]; energy −32 [−39, −25].

### 4.2 Stress sweep — forced number of disruption types (100 scenarios per level)
| Disruption types | Success C / G / S | Avoidable losses C / G / S | Time-to-aid C / G / S |
|---|---|---|---|
| 0 | 100 / 100 / 43% | 0.00 / 0.00 / 0.00 | 62 / 70 / 164 |
| 3 | 99 / 97 / 27% | 0.05 / 0.27 / 0.21 | 62 / 71 / 172 |
| 6 | 96 / 88 / 16% | 0.12 / 0.37 / 0.35 | 62 / 72 / 174 |

(Full 0–6 table in `results/summary.json`.)

### 4.3 Ablation — CONCORD minus one component (same 300 seeds)
| Variant | Success | Time-to-aid | Report latency | Avoidable losses | Churn | Energy |
|---|---|---|---|---|---|---|
| Full CONCORD | 99.0% | 62.4 | 0.84 | 0.107 | 0.12 | 579 |
| − value-of-information messaging | 99.3% | 64.0 | **4.37** | 0.097 | 0.06 | 571 |
| − hysteresis | 99.3% | 62.0 | 0.83 | 0.117 | **3.85** | 534 |
| − risk-aware routing | 98.7% | 62.4 | 0.83 | **0.187** | 0.10 | 574 |
| − relay repositioning | 99.0% | 63.4 | **1.12** | 0.123 | 0.20 | 581 |
| − battery-reserve invariant | 99.0% | 62.7 | 0.83 | 0.090 | 0.05 | 560 |

Read-outs: VoI is the biggest lever on awareness (5.2×); risk-aware routing is the biggest safety lever (1.75× more losses without it); hysteresis buys 33× plan stability at ~8% energy; relay repositioning trims report latency by a quarter; the battery invariant has no measurable effect in v0 (see limits).

### 4.4 Scaling — allocator latency, 1 CPU core, pure Python (3 tasks per agent, warm distance maps)
| Agents / tasks | Repair re-plan | Global re-plan | Cold distance maps |
|---|---|---|---|
| 5 / 15 | 0.16 ms | 0.8 ms | 68 ms |
| 10 / 30 | 0.49 ms | 4.7 ms | 170 ms |
| 20 / 60 | 0.80 ms | 16.6 ms | 307 ms |
| 50 / 150 | 1.96 ms | 131 ms | 620 ms |
| 100 / 300 | 4.06 ms | 611 ms | 1.27 s |
| 200 / 600 | **8.56 ms** | 2.36 s | 2.12 s |

Global re-plans grow roughly with T² (lazy-heap sequential auction); mitigations: run them asynchronously while agents execute current bundles, sector-level auctions, and a compiled port (Rust/Numba). Repair — the common case — stays under 10 ms.

### 4.5 Storyboard mission (seed 6, horizon 200 ticks, 6 survivors)
Scripted disruptions: north bridge collapses (t = 25) · Scout-2 battery fault (t = 35) · comm blackout (t = 45) · storm over sector C for 80 ticks (t = 75) · Rover-1 hardware failure (t = 85).
- t = 29: Scout-1 holds a survivor report in a dead zone → detours 3 cells to reconnect (VoI).
- t = 36: Scout-2 returns — "31% battery left, 27% needed to reach base + 15% reserve; its 4 tasks re-auctioned".
- t = 86: forecast for "hold" = **0%**; option B "fly Cargo-1 through the storm" = **72%** (29 of 40 rollouts succeed) → escalation card → approved.
- Outcome: all 6 survivors aided (last at t = 162); 0 avoidable losses; 1 human decision for 5 disruptions.
- Same scenario without the human decision (CONCORD holds): 5/6 aided. Greedy: 3/6. Static: 2/6 with 2 more drones lost.

---

## 5. Research evidence (with sources)

### 5.1 Why speed of re-coordination matters
- **1990 Luzon earthquake:** survival among trapped people fell from 88% on day 1 to 35% on day 2, 9% on day 3 and 0% from day 4; 94% of those rescued alive were extricated in the first 24 h. Source: Univ. of Pittsburgh Supercourse "Earthquakes" lecture citing Roces et al., *Bull. WHO* 1992 — <https://sites.pitt.edu/~super1/lecture/lec32971/007.htm>, <https://pubmed.ncbi.nlm.nih.gov/1394785/>.
- **1988 Armenia earthquake:** 89% of those rescued alive were extricated in the first 24 h (same Supercourse page).
- **Global scale (EM-DAT 2024):** 393 disasters, 16,753 deaths, 167 million people affected, ~US$242 B in damages. — <https://www.preventionweb.net/quick/93926>

### 5.2 Communications fail when you need them most
- **Hurricane Maria (FCC, 21 Sep 2017):** 95% of Puerto Rico's cell sites out; 48 of 78 municipalities at 100% outage. — <https://convergedigest.com/fcc-95-of-cell-sites-down-in-puerto-rico/>
- **Mumbai, 26 Jul 2005:** 944 mm of rain at Santacruz in 24 h (Mumbai's wettest day on record); ~1,094 deaths in Maharashtra; "an unprecedented 5 million mobile and 2.3 million MTNL landline users were hit for over four hours". — <https://en.wikipedia.org/wiki/Maharashtra_floods_of_2005>
- **DARPA SubT (Timothy Chung):** first responders face "severe communication constraints". — <https://www.darpa.mil/news/2021/subterranean-challenge-winners>

### 5.3 Humans are the bottleneck — and the safety net
- **DARPA SubT rules:** only one team member, the Human Supervisor, could manage and interact with the deployed robots; Team CERBERUS reports operator errors were "a significant fraction of mistakes during the runs"; they used carrier robots to drop "breadcrumb" comm nodes and a time budget for out-of-comms exploration with automatic homing. — Tranzatto et al., *Field Robotics* 2024 (arXiv:2207.04914).
- **Final results (Sep 2021):** CERBERUS 1st ($2 M), CSIRO Data61 2nd ($1 M), MARBLE 3rd ($0.5 M); CERBERUS and CSIRO tied on 23 points.
- **Supervisory control of multiple UAVs (MIT HAL):** operator performance degrades under high re-planning load; operators who try to manage every vehicle under saturation fail missions. — Cummings & Mitchell, <https://dspace.mit.edu/handle/1721.1/90289>
- **Levels of automation:** Parasuraman, Sheridan & Wickens (2000) — the framework behind "automate the routine, escalate the consequential". — <https://doi.org/10.1109/3468.844354>

### 5.4 Why the LLM stays out of the control loop
- **PlanBench (Valmeekam, Stechly, Kambhampati 2024):** best general LLM (Llama 3.1 405B) 62.6% on Blocksworld; on the obfuscated "Mystery Blocksworld" "no LLM achieves even 5%"; o1-preview 97.8% / 52.8%, but only 23.6% on longer problems; the classical planner Fast Downward solves 100% at 0.265 s per instance, "many orders of magnitude faster" than o1, with correctness guarantees. — <https://arxiv.org/abs/2409.13373>
- **LLM+P (Liu et al. 2023):** translating natural language to PDDL and calling a classical planner gives optimal plans for most problems where LLMs alone fail (e.g., Blocksworld 90% vs 15–20%). — <https://arxiv.org/abs/2304.11477>
- **LLM-Modulo (Kambhampati et al., ICML 2024):** LLMs as idea generators and translators inside a loop of external verifiers — exactly CONCORD's split. — <https://arxiv.org/abs/2402.01817>
- **RoboPAIR (Robey et al. 2024):** 100% jailbreak success on three LLM-controlled robots (NVIDIA Dolphins, Clearpath Jackal with GPT-4o, Unitree Go2) — "the first successful jailbreak of a deployed commercial robotic system". — <https://arxiv.org/abs/2410.13691>
- **SMART-LLM (Kannan, Venkatesh, Min — IROS 2024):** LLM multi-robot task decomposition/allocation works for offline plans; CONCORD borrows the NL-to-task idea but keeps execution-time decisions deterministic. — <https://arxiv.org/abs/2309.10062>

### 5.5 The allocation and planning foundations
- **CBBA** — Choi, Brunet & How, *IEEE T-RO* 25(4):912–926 (2009): decentralised auction + consensus; conflict-free assignments; robust to inconsistent situational awareness and changing network topology. — <https://doi.org/10.1109/TRO.2009.2022423>
- **Market-based coordination survey** — Dias et al., *Proc. IEEE* 94(7) (2006). — <https://doi.org/10.1109/JPROC.2006.876939>
- **MRTA taxonomies** — Gerkey & Matarić, *IJRR* 23(9) (2004) <https://doi.org/10.1177/0278364904045564>; Korsah, Stentz & Dias, *IJRR* 32(12) (2013) <https://doi.org/10.1177/0278364913496484>. CONCORD's problem is ST-SR-TA with time-extended assignment and cross-schedule dependencies (deliver depends on locate).
- **Multi-robot SAR survey** — Queralta et al., *IEEE Access* 8 (2020). — <https://arxiv.org/abs/2008.12610>
- **Decentralised planning under intermittent comms** — Best et al., Dec-MCTS, *IJRR* 38(2–3) (2019). — <https://doi.org/10.1177/0278364918755924>
- **Routing** — Hart, Nilsson & Raphael (A*), *IEEE TSSC* 4(2) (1968) <https://doi.org/10.1109/TSSC.1968.300136>; drone energy vs payload — Dorling et al., *IEEE T-SMC: Systems* 47(1) (2017) <https://doi.org/10.1109/TSMC.2016.2582745>.
- **Monte-Carlo feasibility** — statistical model checking: Legay, Delahaye & Bensalem (2010) <https://doi.org/10.1007/978-3-642-16612-9_11>.
- **Explainable planning** — Chakraborti, Sreedharan & Kambhampati, IJCAI 2020 <https://doi.org/10.24963/ijcai.2020/669>.
- **Swarm engineering** — Brambilla et al., *Swarm Intelligence* 7(1) (2013) <https://doi.org/10.1007/s11721-012-0075-2>.

### 5.6 Regulation and policy tailwinds
- **FAA Part 108 (BVLOS):** NPRM published 7 Aug 2025 (*Federal Register* 90(150)); proposes automated flight (no manual joystick control), with an operations supervisor and flight coordinators; higher aircraft-per-coordinator ratios need an FAA-accepted method. Final rule at OIRA review since 10 Jul 2026 and **not yet published as of late Sep 2026**. — <https://www.govinfo.gov/content/pkg/FR-2025-08-07/html/2025-14992.htm>; status trackers <https://www.flyusi.org/guides/get-108-ready>, <https://droneauthority.org/laws/part-108>
- **India:** Drone Rules 2021; Digital Sky interactive airspace map with green / yellow / red zones (Sep 2021) — CONCORD treats red/yellow zones as hard routing constraints. — <https://www.drishtiias.com/daily-updates/daily-news-analysis/airspace-map-of-india>
- **Namo Drone Didi:** 15,000 drones to women SHGs; outlay ₹1,261 crore (2024-25 to 2025-26) for agri-drone rental services. — <https://narendramodi.in/cabinet-approves-central-sector-scheme-for-providing-drones-to-the-women-self-help-groups-576403>

### 5.7 Market and users
- **Swarm robotics:** US$1.1 B (2024) → US$6.2 B (2030), CAGR 33%; UAV segment → US$4.3 B at 34.9% CAGR. — MarketGlass (Global Industry Analysts) via GII <https://www.giiresearch.com/report/go1788365-swarm-robotics.html>
- **Commercial drones:** US$40.6 B (2025) → US$57.8 B (2030); services US$29.4 B of 2025 spend; drone flights 15.5 M (2023) → 19.5 M (2024). — Drone Industry Insights <https://droneii.com/drone-market-growth-in-2025-and-beyond>
- **NDRF:** 16 battalions at 68 locations; sanctioned strength 18,556; >12,000 operations and >1,58,000 people rescued since 2006; 2024: 1,038 operations, >4,000 lives saved, >63,000 evacuated; Wayanad 2024: 14 rescued, 352 evacuated. — <https://www.ndrf.gov.in/en/node/90366>
- **Silkyara tunnel (Nov 2023):** 41 workers trapped for 17 days; more than a dozen agencies coordinated; drones with SLAM LiDAR and ground-penetrating radar surveyed the tunnel. — <https://www.ndrf.gov.in/en/node/90445>, <https://themachinemaker.com/madeinindia/unspoken-heroes-of-silkyara-tunnel-rescue/>
- **Wayanad landslides (2024):** rescuers mapped GPS coordinates from aerial drone pictures and phones' last locations and shared them with all teams across six zones (Army, NDRF, DSG, Coast Guard, Navy, police). — <https://www.tribuneindia.com/news/india/wayanad-tragedy-gps-coordinates-aerial-drone-pictures-used-by-rescuers-to-locate-survivors-300-missing>

---

## 6. Competitor landscape (how to talk about each)

| Player | What it is (public sources) | Where CONCORD differs | Safe wording |
|---|---|---|---|
| **FlytBase** (India-born) | Drone-dock autonomy platform: multi-vendor docks and drones, one pilot supervising multiple drones, automated deconfliction, BVLOS readiness, visual AI agents, on-prem/sovereign hosting — <https://flytbase.com/platform> | Mission-level task decomposition, re-allocation on failure, feasibility forecasting and ground-robot teaming are not publicly documented | "Excellent at operating drone fleets; CONCORD is the mission brain that could sit above such a fleet." |
| **DJI FlightHub 2** | Cloud fleet management for DJI drones and docks (mission planning, live streaming, mapping) | Single-vendor; no documented multi-agent re-allocation or escalation logic | "Fleet management, not mission orchestration." |
| **Open-RMF** | Open-source framework for interoperability between multiple robot fleets and building infrastructure (doors, lifts), with task bidding and traffic management; indoor-first — <https://www.open-rmf.org/> | Assumes building infrastructure and reliable networks; no comms-degraded or aerial focus | "Great for hospitals and buildings; we target infrastructure-poor, comms-degraded outdoor missions — and could interoperate." |
| **Auterion Nemyx** | Swarm engine on AuterionOS: one operator commanding multiple drones with drone-to-drone coordination; defence focus — <https://auterion.com/product/nemyx/> | Closed, military; no documented forecast-driven escalation or explanations | "Proves one-operator swarms are real; we are open and civilian-first." |
| **Anduril Lattice for Mission Autonomy** | Defence C2 software enabling a single operator to control many heterogeneous autonomous systems (2023) — <https://breakingdefense.com/2023/05/andurils-new-tech-could-allow-single-operator-to-control-hundreds-of-autonomous-systems/> | Closed defence stack | "Validates the category; not available to NDRF or a municipal flood cell." |
| **LLM planners** (SMART-LLM, RoCo) | LLMs decompose and allocate multi-robot tasks, mostly offline, in simulation | Execution-time decisions by LLMs are slow, unverifiable and jailbreakable | "We use the LLM for exactly the part it is good at — language." |
| **CBBA** (MIT, 2009) | The decentralised auction algorithm we build on | Algorithm, not a product: no intent layer, no escalation, no explanations | "Our allocator is CBBA-style; our contribution is the full mission loop around it." |

---

## 7. Datasets & tools for the offline build

| Need | Resource | Link |
|---|---|---|
| Realistic grid maps + multi-agent scenarios | Moving AI Lab MAPF benchmarks (ODC-By; cite Stern et al. 2019) | <https://movingai.com/benchmarks/mapf.html> |
| A real Mumbai ward (roads, buildings, river) | OpenStreetMap + OSMnx | <https://www.openstreetmap.org>, <https://osmnx.readthedocs.io> |
| Where the cell towers are (comm coverage, dead zones) | OpenCelliD — 55 M+ cells, 200+ countries | <https://opencellid.org> |
| Real flood extents for scenario generation | Copernicus Emergency Management Service rapid mapping | <https://mapping.emergency.copernicus.eu/> |
| Indian flood / hazard layers | ISRO NRSC Bhuvan | <https://bhuvan.nrsc.gov.in> |
| Building damage labels to seed "survivor" tasks | xBD (xView2) dataset — Gupta et al. 2019, arXiv:1911.09296 | <https://xview2.org/dataset> |
| Weather for storm cells | Open-Meteo API (free, no key) | <https://open-meteo.com> |
| Hardware-in-the-loop path | PX4 SITL (multi-vehicle with Gazebo) · ROS 2 | <https://docs.px4.io/main/en/simulation/>, <https://docs.ros.org> |
| Routing upgrades | Google OR-Tools (vehicle routing) | <https://developers.google.com/optimization> |
| Property-based tests | Hypothesis | <https://hypothesis.readthedocs.io> |

---

## 8. Judge Q&A — the 25 questions you will get

1. **Is the LLM controlling the robots?** No. It turns the goal into a schema-checked task graph that a human confirms, and it phrases explanations. Every assignment, route and re-plan is a deterministic algorithm running in milliseconds. PlanBench and RoboPAIR are why.
2. **Isn't this a scripted animation?** Press any disruption button — the response is computed live. The same hooks drove 4,500 seeded missions nobody scripted.
3. **Why is greedy so close on success?** Because we gave it the same smart return-to-home — we refused to beat a strawman. CONCORD's wins are speed (−12% time-to-aid), awareness (10× faster critical reports), safety (−46% avoidable losses) and stability (0.12 reassignments/mission), and the success gap widens under stress (96% vs 88%).
4. **Where does the 12% come from, if each component adds only 1–2 ticks?** Mostly from the auction itself: time-discounted, priority-aware bundles with planned recharge stops beat nearest-task dispatch. The components mostly buy safety and awareness.
5. **What exactly is CBBA and what did you implement?** Consensus-Based Bundle Algorithm: agents build task bundles by bidding, then run consensus to resolve conflicts. v0 runs the bundle phase centrally when connected (equivalent to converged consensus at this scale); asynchronous consensus for disconnected agents is on the 36-hour plan.
6. **How does it scale to 100+ agents?** Repair re-plans stay under 10 ms at 200 agents on one core in Python. Global re-plans (2.4 s at 200) run in the background while agents execute current bundles; sector-level auctions and a compiled port are next; decentralised CBBA parallelises across agents.
7. **What happens when communication is lost?** Disconnected agents keep executing their bundles; the relay drone repositions; a scout holding a survivor report detours to reconnect; claims reconcile on reconnection.
8. **How do you decide what's worth transmitting?** A value-of-information queue: survivor reports outrank hazards outrank telemetry. Without it, critical reports arrive 5.2× later.
9. **How is P(success) computed? Can you trust it?** 40 Monte-Carlo rollouts of the current plan with future failures sampled. In v0 the hazard model matches the simulator, so calibration is optimistic; in deployment you learn hazard rates and track calibration (reliability diagrams) — it's on the plan.
10. **Why 60%?** It's a tunable policy parameter per mission type; the point is that escalation is triggered by a number, and each option's odds go to the human.
11. **What if the operator doesn't answer?** A safe default (the recommended option, or the conservative one for irreversible actions) executes after a timeout and is logged.
12. **Won't humans get flooded with cards?** Only P < 60% or irreversible calls escalate, and repeats from the same root cause are de-duplicated. In the storyboard: 5 disruptions, 1 card.
13. **Why not Gazebo/ROS now?** The PS rewards mission-level reasoning; physics adds days and nothing the PS asks for. The agent interface is designed for a ROS 2 / PX4 SITL bridge.
14. **What's the battery-reserve invariant worth if the ablation shows no gain?** Honest answer: in v0 the smart return-to-home already catches most cases. The invariant prevents aborted sorties and is a checkable safety property; we'll test it with gradual drains and headwinds.
15. **Doesn't hysteresis cost efficiency?** Yes, ~8% energy — in exchange for 33× fewer reassignments. Operators trust plans that don't flip.
16. **How do you handle a bridge collapse?** The terrain version changes, ground distance maps recompute, and a global re-plan re-auctions affected deliveries — often to the cargo drone.
17. **Storms?** Risk-aware routing prices storm cells steeply; tasks inside a storm exceed the risk ceiling and wait or go to ground agents; without this, avoidable losses rise 1.75×.
18. **What if the LLM produces a bad task graph?** Schema-constrained output, then map validation (sectors exist, capabilities available, acyclic), then human confirmation; offline, a preset graph loads.
19. **Is the 1 tick = 10 s real?** It's an interpretation to make ticks feel concrete; all claims are in ticks.
20. **How is this different from FlytBase / DJI FlightHub?** They operate drone fleets extremely well; CONCORD decides the mission across mixed air-ground teams and re-plans when it breaks. It could sit above them.
21. **Dual use / weapons?** Civilian-first design: human approval for irreversible actions, no weapon payloads, auditable logs; licence terms can exclude weaponisation.
22. **How would NDRF use it tomorrow?** Start as a planning and training simulator for flood drills (no hardware risk), then a supervisory console for a small mixed fleet.
23. **What's your business model?** Open-core: the engine and simulator free; paid fleet console, integrations and support for agencies and industry.
24. **What breaks first at scale?** Global re-plans at hundreds of agents and WebSocket fan-out; we already run global re-plans asynchronously and shard missions per worker.
25. **What would you build first with more time?** The PX4 SITL bridge, a real Mumbai ward from OSM with OpenCelliD comm coverage, and forecast calibration.

---

## 9. Offline-round demo script (3 minutes) + judge-button protocol

| Time | Beat |
|---|---|
| 0:00–0:15 | Hook: "Every rescue plan breaks within minutes. Let's break ours." |
| 0:15–0:40 | Type the mission in plain English → task graph appears → operator confirms → agents deploy |
| 0:40–1:10 | Scout finds a survivor → delivery auctioned (show bids) → bridge collapses → rover re-routes; log explains |
| 1:10–1:35 | Rover heads into a dead zone → relay repositions; a scout detours to report a survivor |
| 1:35–2:00 | **Hand the mouse to a judge:** "Kill any agent you like." Tasks re-auction live |
| 2:00–2:30 | Storm → forecast drops → decision card with odds → operator approves |
| 2:30–2:50 | Benchmark chart: 300 scenarios, same seeds, CIs |
| 2:50–3:00 | Close: "The plan will break. CONCORD keeps the mission alive." |

**Judge-button protocol:** rate-limit to one event per 2 s; every button logs its seed so any surprising run can be replayed; keep a pre-recorded backup of the full run (the included `concord_demo.mp4` is a template for it); run the scripted scenario 10+ times before stage time.

---

## 10. Claims hygiene — what not to say

- Don't say "the AI decides". Say "the auction decides; the LLM translates".
- Don't say "greedy fails". Say "greedy is strong — we're 12% faster, 10× better informed, and lose about half as many drones and robots to avoidable causes".
- Don't present ~250 missions/core as measured. It's an estimate from the measured 0.8 ms tick.
- Don't claim hardware results. Say "simulation v0; PX4/ROS 2 bridge next".
- Don't claim full asynchronous CBBA yet.
- Don't mark competitors "✗". Say "not publicly documented".
- Don't round inconsistently: 12%, 10×, 46%, 96/88/16, 0.12, 8.6 ms, 4,500 — use these exact figures everywhere.

---

## 11. Offline build — highest-value additions (in order)

1. **Live console + judge buttons** (React/PixiJS + FastAPI WebSocket) on the v0 engine — the single most persuasive demo moment.
2. **LLM mission compiler** with schema-constrained output and a one-click confirm; offline Ollama fallback.
3. **Async CBBA consensus** for disconnected agents, visible on the map ("agent working offline" → "claims reconciled").
4. **Real Mumbai ward** from OSM + OpenCelliD-based comm coverage + a Mithi-river flood layer: turns "grid game" into "our city".
5. **Forecast calibration plot** (predicted vs observed success across seeds) and **escalations per mission** across the benchmark.
6. **PX4 SITL bridge** for two drones — even a 30-second clip of the same decision layer driving SITL vehicles answers the sim-to-real question.
