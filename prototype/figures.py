#!/usr/bin/env python3
"""Slide-ready charts (PNG, white rounded card on transparent background) for the EL-05 deck."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "charts")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 11, "axes.titlesize": 12, "svg.fonttype": "none"})

NAVY = "#003470"
INK2 = "#44536B"
MUTED = "#7A8699"
GRID = "#E6EAF0"
BASEL = "#C3CBD6"
ORANGE = "#EB6834"    # CONCORD (emphasis)
SLATE = "#51627A"     # Greedy baseline
LSLATE = "#A9B4C2"    # Static baseline
GOLD = "#F2B13B"
RED = "#D03B3B"
GREEN = "#0CA30C"
POL = {"concord": ("CONCORD", ORANGE), "greedy": ("Greedy dispatch", SLATE), "static": ("Static plan", LSLATE)}
DPI = 200


def card(figsize, title, subtitle=None, source=None):
    fig = plt.figure(figsize=figsize, dpi=DPI)
    fig.patch.set_alpha(0.0)
    fig.add_artist(FancyBboxPatch((0.006, 0.01), 0.988, 0.98, boxstyle="round,pad=0,rounding_size=0.025",
                                  transform=fig.transFigure, fc="white", ec=(0, 0.2, 0.44, 0.12), lw=1.0,
                                  mutation_aspect=figsize[0] / figsize[1], zorder=-10))
    fig.text(0.035, 0.925, title, fontsize=17, fontweight="bold", color=NAVY, va="center")
    if subtitle:
        fig.text(0.035, 0.855, subtitle, fontsize=10.5, color=INK2, va="center")
    if source:
        fig.text(0.035, 0.045, source, fontsize=8.2, color=MUTED, va="center")
    return fig


def style_ax(ax, ygrid=True):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASEL)
    ax.tick_params(colors=INK2, length=0, labelsize=9.5)
    if ygrid:
        ax.yaxis.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=DPI, transparent=True)
    plt.close(fig)
    print("wrote", name)


def rounded_bars(ax, xs, heights, colors, width=0.56):
    bars = ax.bar(xs, heights, width=width, color=colors, zorder=3)
    for b in bars:  # 4px-ish rounded data end, square baseline
        b.set_joinstyle("round")
    return bars


# ----------------------------------------------------------------------------- 1. KPI small multiples
def chart_kpis(S):
    m = S["main"]
    fig = card((16, 6.2), "300 randomised disruption scenarios: CONCORD vs baselines",
               "Same 300 seeded missions for every policy (0–6 random disruptions each, 3.2 on average) · mean with 95% bootstrap CI · prototype v0 simulation",
               "Source: CONCORD v0 benchmark (run_benchmark.py, seeds 1000–1299). Avoidable losses exclude injected hardware failures. 1 tick ≈ 10 s (assumed).")
    panels = [("success", "Mission success", "%", 100, "higher is better"),
              ("time_to_aid", "Mean time-to-aid", "ticks", 1, "lower is better"),
              ("report_latency", "Critical-report latency", "ticks", 1, "lower is better"),
              ("agents_lost_non_injected", "Avoidable asset losses", "per mission", 1, "lower is better")]
    order = ["concord", "greedy", "static"]
    for i, (k, t, unit, mult, hint) in enumerate(panels):
        ax = fig.add_axes([0.045 + i * 0.24, 0.17, 0.19, 0.55])
        style_ax(ax)
        vals = [m[p][k][0] * mult for p in order]
        lo = [m[p][k][1] * mult for p in order]
        hi = [m[p][k][2] * mult for p in order]
        cols = [POL[p][1] for p in order]
        rounded_bars(ax, range(3), vals, cols)
        ax.errorbar(range(3), vals, yerr=[np.array(vals) - np.array(lo), np.array(hi) - np.array(vals)],
                    fmt="none", ecolor=NAVY, elinewidth=1, capsize=3, zorder=4)
        top = max(hi) * 1.22
        ax.set_ylim(0, top)
        if unit == "%":
            ax.set_yticks([0, 20, 40, 60, 80, 100])
        for x, v, h in zip(range(3), vals, hi):
            lab = f"{v:.1f}%" if unit == "%" else (f"{v:.2f}" if v < 1 else f"{v:.1f}")
            ax.text(x, h + top * 0.03, lab, ha="center", va="bottom", fontsize=10.5, fontweight="bold",
                    color=NAVY if x == 0 else INK2)
        ax.set_xticks(range(3))
        ax.set_xticklabels([POL[p][0].replace(" ", "\n") for p in order], fontsize=9.5)
        ax.set_title(f"{t}", loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=18)
        ax.text(0, 1.035, f"{unit} · {hint}", transform=ax.transAxes, fontsize=9, color=MUTED)
    save(fig, "chart_1_benchmark_kpis.png")


# ----------------------------------------------------------------------------- 2. stress sweep
def chart_stress(S):
    st = S["stress"]
    ks = list(range(7))
    fig = card((12, 6.4), "The more the plan breaks, the bigger CONCORD's lead",
               "100 seeded missions per point · x = number of different disruption types injected into the same mission",
               "Source: CONCORD v0 benchmark (stress sweep, seeds 2000–2099 per level). Disruption types: agent failure, battery fault, bridge collapse, comm blackout, storm, new target.")
    # shared legend row
    lx = 0.035
    for p in ("concord", "greedy", "static"):
        fig.lines.append(matplotlib.lines.Line2D([lx, lx + 0.025], [0.775, 0.775], color=POL[p][1], lw=2.6,
                                                 transform=fig.transFigure))
        fig.text(lx + 0.032, 0.775, POL[p][0], fontsize=10, color=INK2, va="center")
        lx += 0.2
    specs = [("success", "Mission success (%)", 100, (0, 108)), ("agents_lost_non_injected", "Avoidable asset losses per mission", 1, None)]
    for i, (k, lab, mult, ylim) in enumerate(specs):
        ax = fig.add_axes([0.06 + i * 0.49, 0.16, 0.37, 0.5])
        style_ax(ax)
        for p in ("static", "greedy", "concord"):
            y = [st[str(kk)][p][k][0] * mult for kk in ks]
            ax.plot(ks, y, color=POL[p][1], lw=2.6 if p == "concord" else 2, marker="o", ms=5.5,
                    markeredgecolor="white", markeredgewidth=1.2, zorder=3 if p == "concord" else 2)
            if p == "concord":
                ax.text(6.15, y[-1] + (4 if mult == 100 else -0.02), f"{y[-1]:.0f}%" if mult == 100 else f"{y[-1]:.2f}",
                        color=NAVY, fontsize=10, va="center", fontweight="bold")
            else:
                off = {("greedy", 100): -4, ("static", 100): 0, ("greedy", 1): 0.012, ("static", 1): -0.012}[(p, mult)]
                ax.text(6.15, y[-1] + off, f"{y[-1]:.0f}%" if mult == 100 else f"{y[-1]:.2f}",
                        color=INK2, fontsize=10, va="center")
        if ylim:
            ax.set_ylim(*ylim)
            ax.set_yticks([0, 20, 40, 60, 80, 100])
        ax.set_xticks(ks)
        ax.set_xlim(-0.2, 6.2)
        ax.set_xlabel("Disruption types injected", color=INK2, fontsize=9.5)
        ax.set_title(lab, loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
    save(fig, "chart_2_stress_sweep.png")


# ----------------------------------------------------------------------------- 3. time-to-aid CDF
def chart_cdf(S):
    m = S["main"]
    fig = card((10.5, 6.2), "Survivors reach aid sooner",
               "Share of all survivors aided vs time since they appeared · 300 missions per policy",
               "Source: CONCORD v0 benchmark (seeds 1000–1299). 1 tick ≈ 10 s (assumed). Curves end at the 320-tick mission limit.")
    ax = fig.add_axes([0.08, 0.17, 0.88, 0.58])
    style_ax(ax)
    t = np.arange(0, 321)
    for p in ("static", "greedy", "concord"):
        a = m[p]["aid_times"]
        n = len(a)
        vals = np.array([x for x in a if x is not None])
        y = [(vals <= tt).sum() / n * 100 for tt in t]
        ax.plot(t, y, color=POL[p][1], lw=2.4 if p == "concord" else 2, zorder=3 if p == "concord" else 2)
        med = np.median([x if x is not None else 999 for x in a])
        within = (vals <= 120).sum() / n * 100
        ax.plot([], [], color=POL[p][1], lw=2.6, label=f"{POL[p][0]} — median {med:.0f} ticks · {within:.0f}% aided within 120")
    ax.set_xlim(0, 320)
    ax.set_ylim(0, 102)
    ax.axvline(120, color=BASEL, lw=1)
    h, l = ax.get_legend_handles_labels()
    ax.legend(h[::-1], l[::-1], loc="lower right", frameon=False, fontsize=9.6, labelcolor=INK2)
    ax.set_xlabel("Ticks since the survivor appeared", color=INK2, fontsize=9.5)
    ax.set_ylabel("Survivors aided (%)", color=INK2, fontsize=9.5)
    save(fig, "chart_3_time_to_aid_cdf.png")


# ----------------------------------------------------------------------------- 4. ablation table
def chart_ablation(S):
    ab = S["ablation"]
    full = ab["full"]
    rows = [
        ("Value-of-information messaging", "no_voi_messaging", "report_latency", "Critical-report latency (ticks)", "{:.2f}"),
        ("Hysteresis (anti-thrashing)", "no_hysteresis", "churn", "Task reassignments / mission", "{:.2f}"),
        ("Risk-aware routing", "no_risk_awareness", "agents_lost_non_injected", "Avoidable asset losses / mission", "{:.3f}"),
        ("Relay repositioning", "no_relay_repositioning", "report_latency", "Critical-report latency (ticks)", "{:.2f}"),
        ("Battery-reserve invariant", "no_battery_invariant", "time_to_aid", "Mean time-to-aid (ticks)", "{:.1f}"),
    ]
    fig = card((13, 5.6), "What each component buys (ablation)",
               "CONCORD with one component switched off · same 300 seeded missions · each row shows the metric that component targets",
               "Source: CONCORD v0 benchmark (ablation runs, seeds 1000–1299). Trade-off: hysteresis costs ~8% more energy. Battery invariant: in v0 the smart return-to-home safety net already catches most cases.")
    ax = fig.add_axes([0.035, 0.12, 0.93, 0.66])
    ax.axis("off")
    cols_x = [0.0, 0.29, 0.58, 0.72, 0.86]
    heads = ["Component", "Metric it protects", "With it", "Without", "Effect"]
    for x, h in zip(cols_x, heads):
        ax.text(x, 0.95, h, fontsize=10.5, color=MUTED, fontweight="bold", va="center")
    ax.plot([0, 1], [0.89, 0.89], color=BASEL, lw=1)
    y = 0.77
    for name, key, metric, mlabel, fmt in rows:
        a = full[metric][0]
        b = ab[key][metric][0]
        ecol = ORANGE
        if a > 0 and abs(b - a) / a < 0.05:
            eff, ecol = "no measurable change", MUTED
        elif b > 0 and a > 0:
            ratio = b / a
            if ratio >= 10:
                eff = f"{ratio:.0f}× worse without"
            elif ratio >= 2:
                eff = f"{ratio:.1f}× worse without"
            elif ratio >= 1.5:
                eff = f"{ratio:.2f}× worse without"
            else:
                eff = f"{(b - a) / a:+.0%} worse without"
        else:
            eff = "—"
        ax.text(cols_x[0], y, name, fontsize=11.5, color=NAVY, fontweight="bold", va="center")
        ax.text(cols_x[1], y, mlabel, fontsize=10.5, color=INK2, va="center")
        ax.text(cols_x[2], y, fmt.format(a), fontsize=11.5, color=NAVY, fontweight="bold", va="center")
        ax.text(cols_x[3], y, fmt.format(b), fontsize=11.5, color=INK2, va="center")
        ax.text(cols_x[4], y, eff, fontsize=11, color=ecol, fontweight="bold", va="center")
        ax.plot([0, 1], [y - 0.085, y - 0.085], color=GRID, lw=0.8)
        y -= 0.17
    save(fig, "chart_4_ablation_table.png")


# ----------------------------------------------------------------------------- 5. scaling
def chart_scaling(sc):
    fig = card((10.5, 6.2), "Re-planning stays fast as the swarm grows",
               "Allocator wall-time vs fleet size (3 tasks per agent) · median of 3–5 trials · 1 CPU core, pure Python",
               "Source: CONCORD v0 scaling test (scaling.py). Global re-plan = every task re-auctioned; repair = one agent fails, only its tasks re-auctioned.")
    ax = fig.add_axes([0.1, 0.17, 0.62, 0.58])
    style_ax(ax)
    n = [r["n"] for r in sc]
    g = [r["global_ms"] for r in sc]
    rp = [r["repair_ms"] for r in sc]
    ax.plot(n, g, color=SLATE, lw=2, marker="o", ms=5.5, markeredgecolor="white", markeredgewidth=1.2)
    ax.plot(n, rp, color=ORANGE, lw=2.4, marker="o", ms=5.5, markeredgecolor="white", markeredgewidth=1.2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(n)
    ax.set_xticklabels([str(v) for v in n])
    ax.minorticks_off()
    ax.set_yticks([0.1, 1, 10, 100, 1000, 10000])
    ax.set_yticklabels(["0.1 ms", "1 ms", "10 ms", "100 ms", "1 s", "10 s"])
    ax.set_ylim(0.08, 12000)
    ax.axhline(1000, color=BASEL, lw=1)
    ax.text(5.2, 1150, "1 s", color=MUTED, fontsize=8.5)
    ax.set_xlabel("Agents in the swarm (tasks = 3 × agents)", color=INK2, fontsize=9.5)
    ax.text(210, rp[-1], f"Repair re-plan\n{rp[-1]:.1f} ms @ 200 agents", color=NAVY, fontsize=9.5,
            fontweight="bold", va="center")
    ax.text(210, g[-1], f"Global re-plan\n{g[-1] / 1000:.1f} s @ 200 agents", color=INK2, fontsize=9.5, va="center")
    save(fig, "chart_5_scaling_latency.png")


# ----------------------------------------------------------------------------- 6. forecast timeline
def chart_forecast(sb):
    tl = sorted(sb["timeline"])
    esc = sb["escalation"]
    fig = card((13, 6.2), "Live feasibility forecast drives escalation — not a hunch",
               "Storyboard mission (scripted disruptions): P(mission success) from 40 Monte-Carlo rollouts, recomputed every 10 ticks and after every event",
               "Source: CONCORD v0 storyboard run (storyboard.py, seed 6, deadline 200 ticks). Hold-option forecast shown at t=86; operator approved option B.")
    ax = fig.add_axes([0.06, 0.2, 0.9, 0.52])
    style_ax(ax)
    ax.axvspan(75, 155, color="#9B6BFF", alpha=0.08, lw=0)
    ax.text(115, 104, "storm over sector C", color="#6A4FB3", fontsize=9, ha="center")
    ax.axhline(60, color=RED, lw=1)
    ax.text(1, 62, "escalation threshold 60%", color=RED, fontsize=8.8)
    ts = [t for t, p in tl if t != esc["t"]]
    ps = [p * 100 for t, p in tl if t != esc["t"]]
    ax.plot(ts, ps, color=ORANGE, lw=2.4, marker="o", ms=5, markeredgecolor="white", markeredgewidth=1.1, zorder=3)
    # escalation moment
    ax.scatter([esc["t"]], [esc["p_now"] * 100], s=70, color=RED, zorder=4, edgecolor="white", lw=1.2)
    pb = [o["p"] for o in esc["options"] if o["key"] == "B"][0] * 100
    ax.annotate(f"t={esc['t']}: Rover fails → 'hold' plan forecasts {esc['p_now'] * 100:.0f}%\n"
                f"Escalation card: B (fly Cargo-1 through storm) = {pb:.0f}% → operator approves",
                xy=(esc["t"], esc["p_now"] * 100), xytext=(esc["t"] + 8, 12), fontsize=9.2, color=NAVY,
                arrowprops=dict(arrowstyle="-", color=NAVY, lw=0.8))
    events = [(25, "bridge\ncollapse"), (35, "battery\nfault"), (45, "comm\nblackout"), (85, "rover\nfailure")]
    for t, lab in events:
        ax.axvline(t, color=BASEL, lw=0.9, zorder=1)
        ax.text(t + 1, 8 if t != 85 else 88, lab, fontsize=8.3, color=INK2, va="bottom")
    ax.set_xlim(0, 172)
    ax.set_ylim(-3, 108)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_yticklabels([f"{v}%" for v in (0, 20, 40, 60, 80, 100)])
    ax.set_xlabel("Mission time (ticks)", color=INK2, fontsize=9.5)
    last = sb["metrics"]
    last_del = max(L["t"] for L in sb["log"] if L["kind"] == "deliver")
    ax.text(171, 40, f"Outcome: all {last['survivors']} survivors aided by t={last_del}\n0 avoidable asset losses", ha="right", va="top",
            fontsize=9.5, color=GREEN, fontweight="bold")
    save(fig, "chart_6_forecast_timeline.png")


# ----------------------------------------------------------------------------- 7. golden hours
def chart_golden():
    fig = card((9, 6.2), "Survival collapses by the day",
               "Survival among people trapped in collapsed buildings, 1990 Luzon earthquake (Philippines)",
               "Source: Univ. of Pittsburgh Supercourse lecture 'Earthquakes', citing Roces et al., Bull. WHO 1992.")
    ax = fig.add_axes([0.09, 0.17, 0.86, 0.57])
    style_ax(ax)
    days = ["Day 1", "Day 2", "Day 3", "Day 4+"]
    vals = [88, 35, 9, 0]
    rounded_bars(ax, range(4), vals, [ORANGE, "#F09A74", "#F5C2A9", "#F5C2A9"], width=0.5)
    for x, v in enumerate(vals):
        ax.text(x, v + 2.5, f"{v}%", ha="center", fontsize=13, fontweight="bold", color=NAVY)
    ax.set_xticks(range(4))
    ax.set_xticklabels(days, fontsize=11)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    save(fig, "chart_7_survival_by_day.png")


# ----------------------------------------------------------------------------- 8. LLM vs planner
def chart_llm():
    fig = card((12, 6.2), "LLMs understand intent — algorithms should decide",
               "PlanBench, zero-shot plan correctness (600 problems each). 'Mystery' = the same problems with renamed objects/actions",
               "Source: Valmeekam, Stechly & Kambhampati, 'LLMs Still Can't Plan; Can LRMs?' (arXiv:2409.13373, 2024). Fast Downward averaged 0.265 s per problem.")
    ax = fig.add_axes([0.07, 0.17, 0.62, 0.56])
    style_ax(ax)
    groups = ["Blocksworld", "Mystery Blocksworld"]
    series = [("Best general LLM (Llama 3.1 405B)", [62.6, 0], SLATE),
              ("Reasoning model (o1-preview)", [97.8, 52.8], LSLATE),
              ("Classical planner (Fast Downward)", [100, 100], ORANGE)]
    w = 0.24
    for i, (lab, vals, col) in enumerate(series):
        xs = np.arange(2) + (i - 1) * (w + 0.03)
        ax.bar(xs, vals, width=w, color=col, zorder=3, label=lab)
        for x, v, g in zip(xs, vals, range(2)):
            txt = "<5%" if (i == 0 and g == 1) else f"{v:.1f}%".replace(".0%", "%")
            ax.text(x, v + 2, txt, ha="center", fontsize=10, fontweight="bold", color=NAVY)
    ax.set_xticks(range(2))
    ax.set_xticklabels(groups, fontsize=11)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 0.95), frameon=False, fontsize=10, labelcolor=INK2)
    fig.text(0.715, 0.3, "No LLM in CONCORD's control loop:\nthe LLM compiles the mission and\nexplains decisions; a verified,\ndeterministic allocator decides.",
             fontsize=10.2, color=NAVY, va="center")
    save(fig, "chart_8_llm_vs_planner.png")


# ----------------------------------------------------------------------------- 9. market
def chart_market():
    fig = card((12, 6.2), "A fast-growing market needs a mission brain",
               "Market size (US$ billion)",
               "Sources: MarketGlass (Global Industry Analysts), 'Swarm Robotics', via GII Research (2025); Drone Industry Insights, 'Drone Market Report 2025–2030' (2025).")
    specs = [("Swarm robotics", ["2024", "2030"], [1.1, 6.2], "CAGR 33%"),
             ("Commercial drones", ["2025", "2030"], [40.6, 57.8], "services ≈ 72% of 2025 spend")]
    for i, (t, xs, vals, note) in enumerate(specs):
        ax = fig.add_axes([0.07 + i * 0.47, 0.17, 0.38, 0.55])
        style_ax(ax)
        rounded_bars(ax, range(2), vals, [LSLATE, ORANGE], width=0.45)
        for x, v in enumerate(vals):
            ax.text(x, v * 1.03, f"${v:g}B", ha="center", va="bottom", fontsize=13, fontweight="bold", color=NAVY)
        ax.set_xticks(range(2))
        ax.set_xticklabels(xs, fontsize=11)
        ax.set_ylim(0, max(vals) * 1.25)
        ax.set_yticklabels([])
        ax.yaxis.grid(False)
        ax.set_title(t, loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=12)
        ax.text(0.5, max(vals) * 1.17, note, fontsize=9.5, color=INK2, ha="center")
    save(fig, "chart_9_market.png")


if __name__ == "__main__":
    S = json.load(open(os.path.join(RES, "summary.json")))
    sc = json.load(open(os.path.join(RES, "scaling.json")))
    sb = json.load(open(os.path.join(RES, "storyboard.json")))
    chart_kpis(S)
    chart_stress(S)
    chart_cdf(S)
    chart_ablation(S)
    chart_scaling(sc)
    chart_forecast(sb)
    chart_golden()
    chart_llm()
    chart_market()
