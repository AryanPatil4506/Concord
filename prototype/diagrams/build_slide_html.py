#!/usr/bin/env python3
"""Emit slide-sized HTML diagrams (CSS px = placement inches x 96). Rendered at 3x by render_slides.py."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# Tabler (outline) and Simple Icons SVG folders, e.g. from the @tabler/icons and simple-icons npm packages
TB = os.environ.get("TABLER_ICONS_DIR", os.path.join(HERE, "icons", "tabler"))
SI = os.environ.get("SIMPLE_ICONS_DIR", os.path.join(HERE, "icons", "simple-icons"))


def icon(name, color="#003470", size=26, sw=1.8):
    s = open(f"{TB}/{name}.svg").read()
    s = s.replace('stroke="currentColor"', f'stroke="{color}"').replace('width="24"', f'width="{size}"') \
         .replace('height="24"', f'height="{size}"').replace('stroke-width="2"', f'stroke-width="{sw}"')
    return s


def logo(slug, color="#003470", size=22):
    s = open(f"{SI}/{slug}.svg").read()
    return s.replace("<svg ", f'<svg fill="{color}" width="{size}" height="{size}" ')


HEAD = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="base.css"><style>
.canvas{{width:{w}px;height:{h}px;border-radius:18px}}
{css}
</style></head><body><div class="canvas">
"""
TAIL = "</div></body></html>"


def page(name, w_in, h_in, css, body):
    w, h = round(w_in * 96), round(h_in * 96)
    open(os.path.join(HERE, f"slide_{name}.html"), "w").write(HEAD.format(w=w, h=h, css=css) + body + TAIL)
    print("html", name, w, h)


# ---------------------------------------------------------------- slide 2: control loop (6.4 x 6.2 in)
page("control_loop", 6.4, 6.2, """
.n{position:absolute;width:196px;background:#fff;border:1.5px solid var(--line);border-radius:14px;padding:9px 11px}
.n h4{font-size:18px;font-weight:800;color:var(--navy);display:flex;align-items:center;gap:7px}
.n p{font-size:14.5px;color:var(--ink2);line-height:1.3;margin-top:3px}
.w{font-size:11px;font-weight:800;letter-spacing:.6px;padding:2px 6px;border-radius:5px;margin-left:auto}
.llm{background:#EEE9FF;color:var(--violet)}.alg{background:#FFE7DB;color:#B4471C}.sw{background:#E3EFFD;color:var(--blue)}.hu{background:var(--red-soft);color:var(--red)}
.c{position:absolute;left:196px;top:300px;width:214px;text-align:center}
.c b{font-size:18px;font-weight:800;color:var(--navy);line-height:1.2;display:block}
.c span{font-size:13.5px;color:var(--ink2);display:block;margin-top:6px}
.t{position:absolute;left:18px;top:14px;font-size:21px;font-weight:800;color:var(--navy)}
""", """
<div class="t">One loop, three owners</div>
<svg class="abs" style="left:0;top:0" width="614" height="595">
 <defs><marker id="a" markerWidth="11" markerHeight="11" refX="8" refY="5.5" orient="auto"><path d="M0,0 L11,5.5 L0,11 z" fill="#003470"/></marker>
 <marker id="v" markerWidth="11" markerHeight="11" refX="8" refY="5.5" orient="auto"><path d="M0,0 L11,5.5 L0,11 z" fill="#6A4FB3"/></marker>
 <marker id="r" markerWidth="11" markerHeight="11" refX="8" refY="5.5" orient="auto"><path d="M0,0 L11,5.5 L0,11 z" fill="#D03B3B"/></marker></defs>
 <ellipse cx="307" cy="318" rx="190" ry="170" fill="none" stroke="#E6EAF0" stroke-width="14"/>
 <path d="M 395 168 A 190 170 0 0 1 470 238" fill="none" stroke="#003470" stroke-width="3" marker-end="url(#a)"/>
 <path d="M 480 400 A 190 170 0 0 1 400 468" fill="none" stroke="#003470" stroke-width="3" marker-end="url(#a)"/>
 <path d="M 214 468 A 190 170 0 0 1 134 400" fill="none" stroke="#003470" stroke-width="3" marker-end="url(#a)"/>
 <path d="M 140 238 A 190 170 0 0 1 216 168" fill="none" stroke="#003470" stroke-width="3" marker-end="url(#a)"/>
 <path d="M 224 84 C 236 92 240 108 240 124" fill="none" stroke="#6A4FB3" stroke-width="3" marker-end="url(#v)"/>
 <line x1="100" y1="385" x2="84" y2="470" stroke="#D03B3B" stroke-width="3" stroke-dasharray="7 5" marker-end="url(#r)"/>
</svg>
<div class="n" style="left:12px;top:46px;width:212px;border-color:#DCD3FB"><h4>Understand<span class="w llm">LLM</span></h4><p>plain English → checked task graph</p></div>
<div class="n" style="left:232px;top:128px"><h4>Allocate<span class="w alg">ALGO</span></h4><p>auction on capability, battery, risk</p></div>
<div class="n" style="left:414px;top:240px;width:190px"><h4>Execute<span class="w sw">SWARM</span></h4><p>failures, lost links, weather stream in</p></div>
<div class="n" style="left:212px;top:470px"><h4>Re-plan<span class="w alg">ALGO</span></h4><p>repair what broke, in ms</p></div>
<div class="n" style="left:10px;top:240px;width:188px"><h4>Forecast<span class="w alg">ALGO</span></h4><p>40 rollouts → P(success)</p></div>
<div class="n" style="left:10px;top:472px;width:190px;border-color:#F3C7C7"><h4 style="color:var(--red)">Escalate<span class="w hu">HUMAN</span></h4><p>only if P&nbsp;&lt;&nbsp;60% or irreversible</p></div>
<div class="c"><b>The plan will break.<br>The mission<br>stays alive.</b><span>no LLM between<br>sensing and acting</span></div>
""")

# ---------------------------------------------------------------- slide 2: key functionalities (6.15 x 6.2 in)
feats = [
    ("message-exclamation", "Mission compiler", "plain-English goal → validated task graph (LLM + schema)"),
    ("hierarchy-3", "Capability-aware auction", "who does what, by capability, distance, battery, risk"),
    ("battery-exclamation", "Battery-reserve rule", "never take a task you can't finish and fly home from"),
    ("route", "Event-driven re-planning", "repair in milliseconds; hysteresis stops thrashing"),
    ("antenna", "Comms-aware coordination", "relay drone repositions; critical news jumps the queue"),
    ("chart-line", "Feasibility forecast", "40 Monte-Carlo rollouts → live P(mission success)"),
    ("user-check", "Human escalation", "decision cards with odds; safe default on timeout"),
    ("bolt", "Live disruption injector", "anyone can break the mission — it re-plans on the spot"),
]
rows = "".join(f'<div class="f"><div class="ic">{icon(i, "#EB6834", 26)}</div><div><b>{t}</b><span>{d}</span></div></div>' for i, t, d in feats)
page("features", 6.15, 6.2, """
.hd{position:absolute;left:18px;top:14px;font-size:21px;font-weight:800;color:var(--navy)}
.list{position:absolute;left:14px;top:54px;right:14px}
.f{display:flex;gap:12px;align-items:center;padding:7px 4px;border-bottom:1px solid var(--grid)}
.ic{width:40px;height:40px;border-radius:10px;background:#FFF3EC;display:flex;align-items:center;justify-content:center;flex:none}
.f b{display:block;font-size:16.5px;color:var(--navy);font-weight:800}
.f span{display:block;font-size:14px;color:var(--ink2);line-height:1.25}
""", f'<div class="hd">Key functionalities</div><div class="list">{rows}</div>')

# ---------------------------------------------------------------- slide 2: PS alignment strip (18.8 x 1.15 in)
ps = [("Decompose the mission", "Mission compiler → task DAG"), ("Allocate by capability", "CBBA-style auction"),
      ("Re-plan on failures", "repair / global re-plan"), ("Reason about comms", "relay + value-of-information"),
      ("Assess risk & feasibility", "Monte-Carlo forecast"), ("Escalate & explain", "decision cards + log")]
chips = "".join(f'<div class="p"><span class="k">PS asks</span><b>{a}</b><span class="arrow">→</span><em>{b}</em><span class="ok">✓</span></div>' for a, b in ps)
page("ps_alignment", 18.8, 1.15, """
.row{position:absolute;left:12px;right:12px;top:12px;bottom:12px;display:grid;grid-template-columns:repeat(6,1fr);gap:10px}
.p{background:#F6F8FB;border:1.5px solid var(--line);border-radius:12px;padding:8px 12px;position:relative}
.p .k{display:block;font-size:11px;font-weight:800;letter-spacing:.8px;color:var(--muted)}
.p b{font-size:15.5px;color:var(--navy);display:block;line-height:1.2}
.p .arrow{display:none}
.p em{font-style:normal;font-size:14px;color:#B4471C;font-weight:700;display:block;line-height:1.2;margin-top:2px}
.p .ok{position:absolute;right:10px;top:8px;width:20px;height:20px;border-radius:50%;background:var(--green-soft);color:var(--green);font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center}
""", f'<div class="row">{chips}</div>')

# ---------------------------------------------------------------- slide 3: architecture (12.3 x 7.2 in)
page("architecture", 12.3, 7.2, """
.band{position:absolute;border-radius:14px}.band .chip{position:absolute;left:12px;top:-11px;font-size:11.5px;padding:4px 9px}
.bx{position:absolute;background:#fff;border:1.5px solid var(--line);border-radius:12px;padding:8px 10px}
.bx h4{font-size:16.5px;font-weight:800;color:var(--navy);display:flex;gap:7px;align-items:center}
.bx p{font-size:14px;color:var(--ink2);line-height:1.28;margin-top:3px}
.nm{display:inline-flex;width:20px;height:20px;border-radius:50%;align-items:center;justify-content:center;font-size:11.5px;font-weight:800;color:#fff;flex:none}
.bi{border-left:5px solid var(--violet)}.bd{border-left:5px solid var(--orange)}.bw{border-left:5px solid var(--blue)}.bo{border-left:5px solid var(--navy)}
.lbl{position:absolute;font-size:12.5px;font-weight:700;color:var(--navy);background:#fff;padding:1px 6px;border-radius:5px;border:1px solid var(--line);white-space:nowrap}
.pill{position:absolute;right:14px;top:12px;background:var(--orange);color:#fff;font-weight:800;font-size:14.5px;padding:6px 12px;border-radius:999px}
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
.log{position:absolute;left:196px;right:14px;bottom:12px;height:40px;background:var(--navy);border-radius:10px;color:#fff;font-size:14px;display:flex;align-items:center;padding:0 14px}
""", """
<div class="hd">System architecture &amp; workflow</div><div class="pill">No LLM in the control loop</div>
<div class="band" style="left:12px;top:62px;width:168px;height:568px;background:#F6F8FB;border:1.5px solid var(--line)"><span class="chip" style="background:var(--navy);color:#fff">OPERATOR</span></div>
<div class="bx bo" style="left:22px;top:84px;width:148px;height:104px"><h4>Mission console</h4><p>type the goal, confirm the graph</p></div>
<div class="bx bo" style="left:22px;top:204px;width:148px;height:104px"><h4>Live map</h4><p>agents, links, storms, P(success)</p></div>
<div class="bx bo" style="left:22px;top:324px;width:148px;height:120px;border-color:#F3C7C7"><h4 style="color:var(--red)">Decision cards</h4><p>approve the hard calls, with odds</p></div>
<div class="bx bo" style="left:22px;top:460px;width:148px;height:156px"><h4>Disruption buttons</h4><p>kill · block · drain · blackout · storm · target</p></div>

<div class="band" style="left:196px;top:62px;width:962px;height:122px;background:var(--violet-soft)"><span class="chip" style="background:var(--violet);color:#fff">INTENT LAYER · LLM</span></div>
<div class="bx bi" style="left:210px;top:82px;width:300px;height:88px"><h4><span class="nm" style="background:var(--violet)">1</span>Mission compiler</h4><p>goal → typed task graph (DAG)</p></div>
<div class="bx bi" style="left:526px;top:82px;width:300px;height:88px"><h4>Validator + confirm</h4><p>schema &amp; map checks · human OK</p></div>
<div class="bx bi" style="left:842px;top:82px;width:302px;height:88px"><h4>Explainer</h4><p>decision records → plain reasons</p></div>

<div class="band" style="left:196px;top:206px;width:962px;height:252px;background:var(--orange-soft)"><span class="chip" style="background:var(--orange);color:#fff">DECISION LAYER · DETERMINISTIC · MILLISECONDS</span></div>
<div class="bx bd" style="left:210px;top:226px;width:300px;height:104px"><h4><span class="nm" style="background:var(--orange)">5</span>Re-planner</h4><p>repair vs global re-plan · hysteresis</p></div>
<div class="bx bd" style="left:526px;top:226px;width:300px;height:104px"><h4><span class="nm" style="background:var(--orange)">2</span>Allocator</h4><p>CBBA-style auction · battery-reserve rule</p></div>
<div class="bx bd" style="left:842px;top:226px;width:302px;height:104px"><h4><span class="nm" style="background:var(--orange)">3</span>Router</h4><p>Dijkstra/A* on terrain + storm risk</p></div>
<div class="bx bd" style="left:210px;top:342px;width:300px;height:104px"><h4><span class="nm" style="background:var(--red)">7</span>Escalation engine</h4><p>P &lt; 60% or irreversible → card</p></div>
<div class="bx bd" style="left:526px;top:342px;width:300px;height:104px"><h4><span class="nm" style="background:var(--orange)">6</span>Feasibility forecaster</h4><p>40 Monte-Carlo rollouts</p></div>
<div class="bx bd" style="left:842px;top:342px;width:302px;height:104px"><h4>Comms manager</h4><p>relay placement · value-of-info queue</p></div>

<div class="band" style="left:196px;top:486px;width:962px;height:130px;background:var(--blue-soft)"><span class="chip" style="background:var(--blue);color:#fff">WORLD LAYER · ONE AGENT INTERFACE</span></div>
<div class="bx bw" style="left:210px;top:508px;width:222px;height:94px"><h4>Agent interface</h4><p>get_state · send_plan</p></div>
<div class="bx bw" style="left:446px;top:508px;width:222px;height:94px"><h4><span class="nm" style="background:var(--blue)">4</span>Simulator v0</h4><p>built · 6 disruption types</p></div>
<div class="bx bw" style="left:682px;top:508px;width:222px;height:94px"><h4>Monitor</h4><p>telemetry → triggers</p></div>
<div class="bx" style="left:918px;top:508px;width:226px;height:94px;border-left:5px solid #9AA6B6"><h4 style="color:var(--ink2)">Robot bridge</h4><p>ROS 2 · PX4 (next)</p></div>
<div class="log"><b>Decision log &amp; replay</b>&nbsp;— every trigger, option, score and choice is recorded → audit · explain · benchmark</div>
<svg class="abs" style="left:0;top:0" width="1181" height="691">
 <defs><marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#003470"/></marker>
 <marker id="ao" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#EB6834"/></marker>
 <marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#D03B3B"/></marker></defs>
 <line x1="170" y1="126" x2="205" y2="126" stroke="#003470" stroke-width="2.4" marker-end="url(#ah)"/>
 <line x1="510" y1="126" x2="521" y2="126" stroke="#003470" stroke-width="2.4" marker-end="url(#ah)"/>
 <line x1="676" y1="170" x2="676" y2="221" stroke="#003470" stroke-width="2.4" marker-end="url(#ah)"/>
 <line x1="826" y1="278" x2="837" y2="278" stroke="#003470" stroke-width="2.4" marker-end="url(#ah)"/>
 <line x1="510" y1="278" x2="521" y2="278" stroke="#003470" stroke-width="2.4" marker-end="url(#ah)"/>
 <line x1="526" y1="394" x2="515" y2="394" stroke="#003470" stroke-width="2.4" marker-end="url(#ah)"/>
 <path d="M1144,278 L1152,278 L1152,470 L557,470 L557,503" fill="none" stroke="#003470" stroke-width="2.4" marker-end="url(#ah)"/>
 <path d="M793,508 L793,478 L202,478 L202,278 L205,278" fill="none" stroke="#EB6834" stroke-width="2.4" stroke-dasharray="6 4" marker-end="url(#ao)"/>
 <line x1="210" y1="394" x2="176" y2="394" stroke="#D03B3B" stroke-width="2.4" stroke-dasharray="6 4" marker-end="url(#ar)"/>
</svg>
<div class="lbl" style="left:690px;top:186px">validated task graph</div>
<div class="lbl" style="left:960px;top:458px">plans · routes</div>
<div class="lbl" style="left:300px;top:458px;color:#B4471C;border-color:#F6D2C2">events · telemetry</div>
""")

# ---------------------------------------------------------------- slide 3: algorithms card (6.25 x 7.2 in)
page("algorithms", 6.25, 7.2, """
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
.blk{position:absolute;left:14px;right:14px;background:#F6F8FB;border-radius:12px;padding:9px 12px}
.blk h5{font-size:15.5px;font-weight:800;color:var(--navy)}
.blk p{font-size:14px;color:var(--ink2);line-height:1.32;margin-top:3px}
.f{font-family:"DejaVu Sans Mono",monospace;font-size:14px;color:var(--navy);background:#fff;border:1px solid var(--line);border-radius:8px;padding:7px 9px;margin-top:6px;line-height:1.45}
.f i{color:#B4471C;font-style:normal}
.m{display:inline-block;font-size:11.5px;font-weight:800;color:var(--green);background:var(--green-soft);border-radius:5px;padding:1px 6px}
""", """
<div class="hd">Core algorithms</div>
<div class="blk" style="top:52px"><h5>Bid of agent i for task j</h5>
<div class="f">score = p<sub>j</sub>·e<sup>−t<sub>ij</sub>/τ</sup> − β·E<sub>ij</sub>/B<sub>i</sub> − γ·risk<sub>ij</sub> + δ·[held by i]</div>
<p>time-discounted reward (CBBA-style) − energy − storm risk + stickiness</p></div>
<div class="blk" style="top:190px"><h5>Battery-reserve invariant</h5>
<div class="f">valid only if B<sub>i</sub> ≥ E(i→j) + E(j) + <i>1.15</i>·E(j→base) + 5</div></div>
<div class="blk" style="top:290px"><h5>Allocation</h5><p>Sequential auction: award the best bid, re-bid only the winner (lazy heap) → O(A·T + T²). Decentralised consensus when links drop.</p></div>
<div class="blk" style="top:398px"><h5>Re-planning policy</h5><p><b>Repair</b>: agent failure, battery, new target. <b>Global</b>: storm, bridge collapse, every 30 ticks — with a hysteresis bonus δ.</p></div>
<div class="blk" style="top:506px"><h5>Forecast → escalation</h5><p>K = 40 rollouts sample future failures; escalate when P &lt; 60% or the action is irreversible.</p></div>
<div class="blk" style="top:600px;background:#EAF7EF"><h5 style="color:var(--green)">Measured on 1 CPU core <span class="m">v0</span></h5><p>repair re-plan <b>8.6 ms</b> at 200 agents · full mission tick <b>0.8 ms</b></p></div>
""")

# ---------------------------------------------------------------- slide 3: tech strip (18.8 x 1.0 in)
items = [("python", "Python"), ("numpy", "NumPy"), ("pydantic", "Pydantic"), (None, "OR-Tools"),
         ("ollama", "Ollama (local LLM)"), ("fastapi", "FastAPI + WebSocket"), ("react", "React"), ("typescript", "TypeScript"),
         (None, "PixiJS"), ("sqlite", "SQLite"), ("ros", "ROS 2 (next)"), ("openstreetmap", "OpenStreetMap"), ("docker", "Docker")]
cells = "".join((f'<div class="it">{logo(s)}<span>{l}</span></div>' if s else f'<div class="it"><span class="chip2">{l}</span></div>') for s, l in items)
page("tech_strip", 18.8, 1.0, """
.row{position:absolute;left:14px;right:14px;top:0;bottom:0;display:flex;align-items:center;gap:19px}
.lab{font-size:14px;font-weight:800;color:var(--muted);letter-spacing:.8px;margin-right:4px}
.it{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:700;color:var(--navy);white-space:nowrap}
.chip2{font-size:14px;font-weight:700;color:var(--navy);background:#EEF3FA;border-radius:7px;padding:4px 8px}
""", f'<div class="row"><span class="lab">STACK</span>{cells}</div>')

# ---------------------------------------------------------------- slide 4: comparison (11.05 x 5.35 in)
cols = [("CONCORD", "ours"), ("FlytBase", "dock autonomy"), ("DJI FlightHub 2", "fleet cloud"), ("Open-RMF", "open fleet mgmt"),
        ("Auterion Nemyx", "defence swarm"), ("Anduril Lattice", "defence C2"), ("LLM planners", "SMART-LLM"), ("CBBA", "MIT 2009")]
F, P, N = '<span class="f">●</span>', '<span class="p">◐</span>', '<span class="n">—</span>'
rows_c = [
    ("Air + ground, mixed fleet", [F, P, P, P, P, F, P, F]),
    ("Plain-language mission", [F, N, N, N, N, N, F, N]),
    ("Re-allocates on failure", [F, N, N, P, P, F, N, F]),
    ("Comms-aware (relay, VoI)", [F, P, P, N, P, P, N, P]),
    ("Forecast → human escalation", [F, N, N, N, N, N, N, N]),
    ("Explained decision log", [F, P, P, P, N, N, P, N]),
    ("Open · civilian · laptop", [F, P, P, F, N, N, F, F]),
    ("Proven on hardware", [P, F, F, F, F, F, P, F]),
]
th = "".join(f'<th class="{"ours" if i == 0 else ""}">{a}<small>{b}</small></th>' for i, (a, b) in enumerate(cols))
trs = "".join(f'<tr class="{"hon" if r == "Proven on hardware" else ""}"><td class="cap">{r}{"<small>our honest gap</small>" if r == "Proven on hardware" else ""}</td>' +
              "".join(f'<td class="{"ours" if i == 0 else ""}">{v}</td>' for i, v in enumerate(vals)) + "</tr>" for r, vals in rows_c)
page("comparison", 11.05, 5.35, """
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
table{position:absolute;left:12px;top:52px;width:1036px;border-collapse:separate;border-spacing:0}
th,td{text-align:center;padding:9px 3px;border-bottom:1px solid var(--grid)}
th{font-size:14px;color:var(--navy);font-weight:800;line-height:1.15;vertical-align:bottom}
th small{display:block;font-size:11.5px;color:var(--muted);font-weight:600}
td.cap{text-align:left;font-size:15.5px;font-weight:700;color:var(--navy);width:228px}
td.cap small{display:block;font-size:11px;color:var(--muted);font-weight:600}
.ours{background:#FFF3EC}th.ours{color:#B4471C;border-top-left-radius:10px;border-top-right-radius:10px}
.f{color:var(--navy);font-size:22px}.p{color:#7F8FA8;font-size:22px}.n{color:#C3CBD6;font-size:18px;font-weight:700}
tr.hon td{background:#F7F9FC}tr.hon td.ours{background:#FBE9DF}
.lg{position:absolute;left:16px;bottom:10px;font-size:11.5px;color:var(--ink2)}
""", f'<div class="hd">Comparison with existing approaches</div><table><tr><th style="text-align:left"></th>{th}</tr>{trs}</table>'
     '<div class="lg">● documented core capability · ◐ partial / limited scope · — not publicly documented · from public product pages &amp; papers, Sep 2026</div>')

# ---------------------------------------------------------------- slide 4: differentiators (7.5 x 8.3 in)
difs = [
    ("brain", "No LLM in the control loop", "The LLM translates intent and explains; a deterministic auction decides in milliseconds.",
     "No general LLM reaches 5% on obfuscated planning; a classical planner hits 100% in 0.27 s [5]. LLM-driven robots were jailbroken 100% of the time [6]."),
    ("user-check", "Escalation by the numbers", "Humans see odds per option — not alarms — and only when it matters.",
     "Storyboard: 5 disruptions → 1 human decision; 'hold' 0% vs 'fly through storm' 72% → all 6 survivors aided."),
    ("antenna", "Comms-aware autonomy", "Relay drone repositions, survivor reports jump the queue, agents keep working when cut off.",
     "Critical reports reach base 10× faster than FIFO dispatch (0.84 vs 8.7 ticks, 300 missions)."),
    ("bolt", "Judges can break it live", "The same disruption hooks drive a 4,500-mission benchmark — nothing is scripted.",
     "Stable plans: 0.12 reassignments per mission vs 3.85 without hysteresis."),
]
dcards = "".join(f'<div class="d"><div class="ic">{icon(i, "#FFFFFF", 28, 2)}</div><div><b>{t}</b><p>{d}</p><em>{e}</em></div></div>' for i, t, d, e in difs)
page("differentiators", 7.5, 8.3, """
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
.list{position:absolute;left:12px;right:12px;top:54px;bottom:12px;display:flex;flex-direction:column;gap:12px}
.d{flex:1;display:flex;gap:14px;align-items:center;background:#F6F8FB;border-radius:14px;padding:12px 14px;border-left:5px solid var(--orange)}
.ic{width:52px;height:52px;border-radius:13px;background:var(--orange);display:flex;align-items:center;justify-content:center;flex:none}
.d b{font-size:20.5px;color:var(--navy);font-weight:800;display:block}
.d p{font-size:16px;color:var(--ink2);line-height:1.32;margin-top:3px}
.d em{display:block;font-style:normal;font-size:15px;color:#B4471C;font-weight:700;line-height:1.3;margin-top:7px}
""", f'<div class="hd">Innovation &amp; core differentiators</div><div class="list">{dcards}</div>')

# ---------------------------------------------------------------- slide 5: KPI tiles (9.5 x 2.1 in)
tiles = [("−12%", "time-to-aid", "vs reactive dispatch"), ("10×", "faster critical reports", "0.84 vs 8.7 ticks"),
         ("−46%", "avoidable asset losses", "0.11 vs 0.20 per mission"), ("96%", "success with 6 disruptions", "vs 88% greedy · 16% static")]
tl = "".join(f'<div class="t"><b>{a}</b><span>{b}</span><em>{c}</em></div>' for a, b, c in tiles)
page("kpi_tiles", 9.5, 2.1, """
.row{position:absolute;inset:12px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.t{background:#FFF3EC;border-radius:14px;padding:10px 12px;display:flex;flex-direction:column;justify-content:center}
.t b{font-size:40px;font-weight:800;color:#B4471C;line-height:1}
.t span{font-size:15px;font-weight:800;color:var(--navy);margin-top:6px;line-height:1.15}
.t em{font-style:normal;font-size:12.5px;color:var(--ink2);margin-top:3px}
""", f'<div class="row">{tl}</div>')

# ---------------------------------------------------------------- slide 6: gantt (12.55 x 4.35 in)
page("gantt", 12.55, 4.35, """
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
.sub{position:absolute;left:16px;top:42px;font-size:13.5px;color:var(--ink2)}
.grid{position:absolute;left:150px;top:92px;width:1044px;height:300px}
.hour{position:absolute;top:-20px;font-size:12px;color:var(--muted);transform:translateX(-50%)}
.vline{position:absolute;top:0;bottom:0;width:1px;background:var(--grid)}
.row{position:absolute;left:0;width:1044px;height:52px;border-bottom:1px solid var(--grid)}
.rl{position:absolute;left:-140px;width:132px;top:6px;font-size:14.5px;font-weight:800;color:var(--navy);line-height:1.1}
.rl span{display:block;font-size:11.5px;font-weight:600;color:var(--muted)}
.bar{position:absolute;top:7px;height:38px;border-radius:8px;padding:3px 7px;font-size:13px;line-height:1.2;color:#fff;font-weight:700;overflow:hidden}
.A{background:#2A78D6}.B{background:#EB6834}.C{background:#6A4FB3}.D{background:#0B8A4A}.X{background:var(--navy)}
""", """
<div class="hd">36-hour build plan</div><div class="sub">v0 already de-risks the core · integrate at hour 12 · freeze at hour 31</div>
<div class="grid" id="g"></div>
<script>
const g=document.getElementById('g');const H=36,W=1044,px=W/H;
for(let h=0;h<=H;h+=4){const v=document.createElement('div');v.className='vline';v.style.left=(h*px)+'px';g.appendChild(v);
const t=document.createElement('div');t.className='hour';t.style.left=(h*px)+'px';t.textContent=h+'h';g.appendChild(t);}
const rows=[['World','A · sim &amp; maps','A',[[2,8,'Live engine + WebSocket'],[18,24,'Real Mumbai map (OSM)'],[28,31,'1k-seed run']]],
['Allocation','B · auction','B',[[2,8,'Async CBBA'],[12,18,'OR-Tools routing'],[24,28,'Churn tuning'],[28,31,'Scale test']]],
['Autonomy','C · re-plan · comms','C',[[2,8,'Trigger API'],[12,18,'Escalation cards'],[18,24,'Comms view'],[24,28,'Calibration']]],
['Product','D · UI · LLM','D',[[2,8,'PixiJS map'],[12,18,'Disruption buttons'],[18,24,'LLM compiler'],[24,28,'Explainer'],[31,36,'Pitch · Q&amp;A']]],
['All hands','integrate · polish','X',[[0,2,'Specs'],[8,12,'Integration'],[31,34,'Dry runs']]]];
rows.forEach((r,i)=>{const row=document.createElement('div');row.className='row';row.style.top=(i*58)+'px';
row.innerHTML=`<div class="rl">${r[0]}<span>${r[1]}</span></div>`;
r[3].forEach(([a,b,t])=>{const bar=document.createElement('div');bar.className='bar '+r[2];bar.style.left=(a*px+2)+'px';bar.style.width=((b-a)*px-4)+'px';bar.innerHTML=t;row.appendChild(bar);});
g.appendChild(row);});
</script>
""")

# ---------------------------------------------------------------- slide 6: risks (12.55 x 3.8 in)
risks = [("Too much scope for 36 h", "High", "High", "v0 already runs allocator, re-planner, forecaster, benchmark; hour-12 gate; cut list"),
         ("Bug appears live on stage", "Med", "High", "4,500 seeded missions fuzzed; invariant tests; 10 dry runs; backup video"),
         ("Sim-to-real gap", "High", "Med", "one agent interface → ROS 2 / PX4 SITL bridge; physics out of PS scope"),
         ("Venue internet fails", "Med", "Med", "local LLM (Ollama) + preset task graphs + template explanations"),
         ("LLM returns a bad task graph", "Med", "Low", "schema-constrained output → validator → human confirm → preset")]
def lv(x):
    c = {"High": ("#FDECEC", "#D03B3B"), "Med": ("#FFF4D6", "#9A6A00"), "Low": ("#E9F8EF", "#0B8A4A")}[x]
    return f'<span class="lv" style="background:{c[0]};color:{c[1]}">{x}</span>'
rr = "".join(f"<tr><td class='r'>{a}</td><td>{lv(b)}</td><td>{lv(c)}</td><td class='m'>{d}</td></tr>" for a, b, c, d in risks)
page("risks", 12.55, 3.8, """
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
table{position:absolute;left:14px;top:50px;width:1177px;border-collapse:collapse}
th{font-size:12.5px;color:var(--muted);text-align:left;font-weight:800;letter-spacing:.6px;padding:4px 8px;border-bottom:1.5px solid var(--line)}
td{padding:12px 8px;border-bottom:1px solid var(--grid);font-size:16px;color:var(--ink2);vertical-align:middle}
td.r{font-weight:800;color:var(--navy);width:290px;font-size:16.5px}td.m{line-height:1.25}
.lv{display:inline-block;font-size:13.5px;font-weight:800;border-radius:6px;padding:3px 9px}
""", f"<div class='hd'>Challenges &amp; risks — each with a tested mitigation</div><table><tr><th>RISK</th><th>LIKELIHOOD</th><th>IMPACT</th><th>MITIGATION</th></tr>{rr}</table>")

# ---------------------------------------------------------------- slide 7: users (9.0 x 3.6 in)
users = [("first-aid-kit", "Disaster response", "NDRF: 16 battalions, 1,038 operations in 2024; SDRFs; fire services"),
         ("antenna", "Infrastructure inspection", "power lines, pipelines, bridges — long, remote, repetitive"),
         ("alert-triangle", "Mining & industrial safety", "inspect hazardous zones before people go in"),
         ("tree", "Agriculture fleets", "15,000 drones to women SHGs under Namo Drone Didi"),
         ("helicopter", "Maritime & coastal SAR", "coordinated air + surface search patterns"),
         ("map-2", "Cities & municipalities", "monsoon flood response, e.g. Mumbai's BMC wards")]
ut = "".join(f'<div class="u"><div class="ic">{icon(i, "#003470", 24)}</div><div><b>{a}</b><span>{b}</span></div></div>' for i, a, b in users)
page("users", 9.0, 3.6, """
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
.g{position:absolute;left:12px;right:12px;top:50px;bottom:12px;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat(3,1fr);gap:8px}
.u{display:flex;gap:10px;align-items:center;background:#F6F8FB;border-radius:12px;padding:6px 10px}
.ic{width:40px;height:40px;border-radius:10px;background:#EAF3FF;display:flex;align-items:center;justify-content:center;flex:none}
.u b{display:block;font-size:15.5px;color:var(--navy);font-weight:800}
.u span{display:block;font-size:13px;color:var(--ink2);line-height:1.22}
""", f'<div class="hd">Target users &amp; applications</div><div class="g">{ut}</div>')

# ---------------------------------------------------------------- slide 7: scale-out (9.55 x 5.1 in)
qa = [("10× more missions", "stateless gateway + one worker per mission; <strong>0.8 ms</strong> per mission tick → ~250 live missions per core (est.)"),
      ("100+ agents", "repair re-plan <strong>8.6 ms at 200 agents</strong>; global re-plans run in the background"),
      ("A server crashes", "agents keep their task bundles; a standby worker replays the event log"),
      ("Cloud link drops", "edge gateway runs decentralised CBBA; on-board battery-reserve rule"),
      ("LLM outage", "zero control impact — local model + preset missions"),
      ("Bad release", "CI replays the 300-mission benchmark and blocks regressions")]
qr_ = "".join(f'<div class="q"><b>{a}</b><span>{b}</span></div>' for a, b in qa)
page("scale_out", 9.55, 5.1, """
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
.sub{position:absolute;left:16px;top:42px;font-size:13.5px;color:var(--ink2)}
.arch{position:absolute;left:14px;top:74px;width:300px;bottom:14px;display:flex;flex-direction:column;gap:7px}
.a{background:#fff;border:1.5px solid var(--line);border-radius:10px;padding:6px 9px;font-size:13.5px;color:var(--ink2);line-height:1.2}
.a b{display:block;font-size:14.5px;color:var(--navy)}
.arr{text-align:center;color:var(--muted);font-size:13px;line-height:.6}
.qs{position:absolute;left:330px;right:14px;top:74px;bottom:14px;display:flex;flex-direction:column;gap:6px}
.q{background:#F6F8FB;border-radius:10px;padding:6px 10px}
.q > b{display:block;font-size:14.5px;color:var(--navy)}
.q strong{color:var(--navy)}
.q span{display:block;font-size:13.5px;color:var(--ink2);line-height:1.25}
""", f"""<div class="hd">“YC says yes tomorrow” — built to survive success</div><div class="sub">what breaks first, and what we already do about it</div>
<div class="arch"><div class="a"><b>Gateway</b>FastAPI · WebSocket · auth · autoscaled</div><div class="arr">▼</div>
<div class="a" style="border-left:5px solid var(--orange)"><b>Mission workers</b>1 decision loop per mission, sharded</div><div class="arr">▼</div>
<div class="a" style="background:#FFF3EC"><b>Event bus + decision log</b>NATS / Redis Streams · append-only</div><div class="arr">▼</div>
<div class="a" style="border-left:5px solid var(--blue)"><b>Edge gateways</b>ROS 2 · PX4 · simulator</div>
<div class="a"><b>Tests</b>property-based · 300-seed regression · chaos · load (k6)</div></div>
<div class="qs">{qr_}</div>""")
import json as _j
_sb = _j.load(open(os.path.join(os.path.dirname(HERE), "results", "storyboard.json")))
_want = [(25, "event"), (27, "assign"), (29, "voi"), (36, "battery"), (53, "assign"), (75, "event"), (85, "event"), (86, "escalation")]
_pick = []
for (tt, kk) in _want:
    for L in _sb["log"]:
        if L["t"] == tt and L["kind"] == kk:
            t = L["text"].replace("EVENT: ", "⚡ ").replace("->", "→").replace(" 1 cells", " 1 cell")
            t = t.replace("; others: Scout-1 ineligible, Scout-2 ineligible,", " vs").replace("; others: Scout-1 ineligible,", " vs")
            _pick.append((L["t"], t))
            break
_lines = "".join(f'<div class="l"><span class="tt">t={t:03d}</span><span class="tx">{x}</span></div>' for t, x in _pick[:8])
page("decision_log", 5.2, 2.8, """
.hd{position:absolute;left:14px;top:10px;font-size:17px;font-weight:800;color:var(--navy)}
.box{position:absolute;left:10px;right:10px;top:40px;bottom:10px;background:#0B1B33;border-radius:10px;padding:8px 10px;overflow:hidden}
.l{display:flex;gap:8px;font-family:"DejaVu Sans Mono",monospace;font-size:10.8px;line-height:1.35;margin-bottom:2px}
.tt{color:#35E0B0;flex:none}.tx{color:#EAF1FB}
""", f'<div class="hd">Every decision is logged &amp; explained (real v0 output)</div><div class="box">{_lines}</div>')
# ---------------------------------------------------------------- slide 7: impact (4.55 x 2.9 in)
imp = [("−12%", "faster aid", "time-to-aid vs reactive dispatch"), ("−46%", "fewer lost assets", "avoidable losses per mission"),
       ("1 of 5", "calls go to a human", "storyboard: 5 disruptions, 1 decision"), ("100%", "decisions explained", "every choice logged with its numbers")]
it = "".join(f'<div class="i"><b>{a}</b><div><span>{b}</span><em>{c}</em></div></div>' for a, b, c in imp)
page("impact", 4.55, 2.9, """
.hd{position:absolute;left:14px;top:10px;font-size:17px;font-weight:800;color:var(--navy)}
.g{position:absolute;left:10px;right:10px;top:40px;bottom:10px;display:flex;flex-direction:column;gap:6px}
.i{flex:1;display:flex;gap:10px;align-items:center;background:#FFF3EC;border-radius:10px;padding:4px 10px}
.i b{font-size:22px;font-weight:800;color:#B4471C;width:84px;flex:none}
.i span{display:block;font-size:14px;font-weight:800;color:var(--navy);line-height:1.1}
.i em{display:block;font-style:normal;font-size:12px;color:var(--ink2)}
""", f'<div class="hd">Expected impact &amp; key benefits</div><div class="g">{it}</div>')

# ---------------------------------------------------------------- slide 7: why now (9.0 x 1.35 in)
wn = [("FAA Part 108", "BVLOS rule proposed Aug 2025: automated flight, human supervisors"),
      ("India", "Drone Rules 2021 · Digital Sky green/yellow/red airspace map"),
      ("Momentum", "drone flights up 25% in 2024: 15.5 M → 19.5 M (DRONEII)")]
w_ = "".join(f'<div class="w"><b>{a}</b><span>{b}</span></div>' for a, b in wn)
page("why_now", 9.0, 1.35, """
.row{position:absolute;inset:10px;display:grid;grid-template-columns:120px 1fr 1fr 1fr;gap:8px;align-items:stretch}
.lab{display:flex;align-items:center;justify-content:center;background:var(--navy);color:#fff;border-radius:10px;font-weight:800;font-size:16px}
.w{background:#F6F8FB;border-radius:10px;padding:6px 10px}
.w b{display:block;font-size:14.5px;color:var(--navy)}
.w span{display:block;font-size:12.5px;color:var(--ink2);line-height:1.25}
""", f'<div class="row"><div class="lab">Why now</div>{w_}</div>')

# ---------------------------------------------------------------- slide 7: testing (4.55 x 3.05 in)
tests = [("Property-based tests", "no double-assignment · reserve never violated · DAG order kept"),
         ("Simulation regression", "300 seeded missions per pull request, metric gates"),
         ("Chaos testing", "the disruption injector doubles as a chaos monkey"),
         ("Load testing", "k6: 1,000 live viewers, 1,000 simulated agents")]
tt = "".join(f'<div class="x"><b>{a}</b><span>{b}</span></div>' for a, b in tests)
page("testing", 4.55, 3.05, """
.hd{position:absolute;left:14px;top:10px;font-size:17px;font-weight:800;color:var(--navy)}
.g{position:absolute;left:10px;right:10px;top:40px;bottom:10px;display:flex;flex-direction:column;gap:6px}
.x{flex:1;background:var(--navy);border-radius:10px;padding:5px 10px}
.x b{display:block;font-size:14px;color:var(--gold)}
.x span{display:block;font-size:12.5px;color:#DCE6F5;line-height:1.2}
.ok{position:absolute;right:14px;top:12px;font-size:12px;font-weight:800;color:var(--green);background:var(--green-soft);border-radius:6px;padding:2px 7px}
""", f'<div class="hd">Tested to survive success</div><div class="ok">4,500 missions · 0 crashes</div><div class="g">{tt}</div>')
# ---------------------------------------------------------------- slide 6: feasibility (6.0 x 8.3 in)
blocks = [
    ("Technical feasibility — already proven", [
        "v0 works today: 1,272-line simulator, CONCORD + 2 baselines, forecaster, renderer",
        "4,500 seeded missions run, 0 crashes, fully reproducible",
        "runs offline on a 2-core laptop CPU — no GPU, no cloud"]),
    ("Operational feasibility", [
        "operator stays in charge: confirm the task graph, approve escalations",
        "same agent interface for simulator, ROS 2 and PX4 SITL"]),
    ("Resources & deployment", [
        "team of 4 × 36 h; one laptop each",
        "open-source stack; ₹0 infrastructure; local LLM optional",
        "one Docker image; browser console"]),
    ("Sustainability & viability", [
        "open-core: free engine + simulator; paid fleet console & integrations",
        "pilot path: SDRF / municipal flood cells → NDRF",
        "guardrails: civilian-first, human approval for irreversible acts, no weapon payloads"]),
]
bh = "".join('<div class="b"><h5>' + t + '</h5><ul>' + "".join(f"<li>{x}</li>" for x in xs) + '</ul></div>' for t, xs in blocks)
page("feasibility", 6.0, 8.3, """
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
.g{position:absolute;left:12px;right:12px;top:54px;bottom:12px;display:flex;flex-direction:column;gap:10px}
.b{flex:1;background:#F6F8FB;border-radius:12px;padding:10px 12px;border-left:5px solid var(--navy)}
.b:first-child{border-left-color:var(--green);background:#EEF8F2}
.b{display:flex;flex-direction:column;justify-content:center}
.b h5{font-size:19px;font-weight:800;color:var(--navy);margin-bottom:6px}
.b ul{margin-left:20px}
.b li{font-size:16.5px;color:var(--ink2);line-height:1.35;margin-bottom:4px}
""", f'<div class="hd">Feasibility &amp; viability</div><div class="g">{bh}</div>')

# ---------------------------------------------------------------- slide 8: evidence (6.5 x 8.3 in)
ev = [("Every hour counts", "Survival of trapped people: 88% day 1 → 35% day 2 → 9% day 3", "[1]"),
      ("Comms fail first", "95% of cell sites down after Hurricane Maria; 5 M mobile users cut off in Mumbai, 26 Jul 2005", "[2, 3]"),
      ("Humans are the bottleneck", "DARPA SubT allowed one human supervisor per robot team; the winner's operator errors were a significant fraction of mistakes", "[4]"),
      ("LLMs are not planners", "No LLM reaches 5% on obfuscated planning; a classical planner hits 100% in 0.27 s; LLM-driven robots jailbroken 100%", "[5, 6, 7]"),
      ("Auctions are proven", "CBBA is conflict-free and robust to inconsistent information and changing comms", "[8, 9]"),
      ("Regulation wants supervised autonomy", "FAA Part 108 proposal: automated flight, trained human supervisors", "[10]")]
eh = "".join(f'<div class="e"><b>{a}</b><span>{b} <i>{c}</i></span></div>' for a, b, c in ev)
page("evidence", 6.5, 8.3, """
.hd{position:absolute;left:16px;top:12px;font-size:21px;font-weight:800;color:var(--navy)}
.g{position:absolute;left:12px;right:12px;top:54px;bottom:12px;display:flex;flex-direction:column;gap:9px}
.e{flex:1;background:#F6F8FB;border-radius:12px;padding:9px 14px;border-left:5px solid var(--orange);display:flex;flex-direction:column;justify-content:center}
.e b{display:block;font-size:19px;color:var(--navy);font-weight:800}
.e span{display:block;font-size:16.5px;color:var(--ink2);line-height:1.33;margin-top:3px}
.e i{font-style:normal;color:#B4471C;font-weight:800}
""", f'<div class="hd">Research background &amp; evidence</div><div class="g">{eh}</div>')
print("done")
