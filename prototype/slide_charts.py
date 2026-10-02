#!/usr/bin/env python3
"""Slide-sized charts: rendered at the exact size they occupy on the 20 x 11.25 in slide,
so text stays >= 11 pt when placed at 100%. Output: slides/<name>.png (transparent corners)."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "slides")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 12})

NAVY, INK2, MUTED, GRID, BASEL = "#003470", "#44536B", "#7A8699", "#E6EAF0", "#C3CBD6"
ORANGE, SLATE, LSLATE, RED, GREEN = "#EB6834", "#51627A", "#A9B4C2", "#D03B3B", "#0B8A4A"
POL = {"concord": ("CONCORD", ORANGE), "greedy": ("Greedy dispatch", SLATE), "static": ("Static plan", LSLATE)}
DPI = 250


def card(w, h, title=None, sub=None, src=None, tsize=17):
    fig = plt.figure(figsize=(w, h), dpi=DPI)
    fig.patch.set_alpha(0)
    r = 0.18  # corner radius in inches
    fig.add_artist(FancyBboxPatch((0.004, 0.006), 0.992, 0.988, transform=fig.transFigure,
                                  boxstyle=f"round,pad=0,rounding_size={r / w}", mutation_aspect=w / h,
                                  fc="white", ec=(0, 0.2, 0.44, 0.14), lw=1.0, zorder=-10))
    y = 1 - 0.34 / h
    if title:
        fig.text(0.22 / w, y, title, fontsize=tsize, fontweight="bold", color=NAVY, va="center")
    if sub:
        fig.text(0.22 / w, y - 0.36 / h, sub, fontsize=11.5, color=INK2, va="center")
    if src:
        fig.text(0.22 / w, 0.17 / h, src, fontsize=9.5, color=MUTED, va="center")
    return fig


def ax_at(fig, w, h, l, b, aw, ah):
    """axes placed in inches"""
    ax = fig.add_axes([l / w, b / h, aw / w, ah / h])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASEL)
    ax.tick_params(colors=INK2, length=0, labelsize=11)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    return ax


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=DPI, transparent=True)
    plt.close(fig)
    print("wrote", name)


S = json.load(open(os.path.join(RES, "summary.json")))
SC = json.load(open(os.path.join(RES, "scaling.json")))
SB = json.load(open(os.path.join(RES, "storyboard.json")))


# ------------------------------------------------------------------ slide 2: survival by day (5.35 x 2.9)
def s2_survival():
    w, h = 5.35, 2.9
    fig = card(w, h, "Survival of trapped people, by day", None,
               "1990 Luzon earthquake · Roces et al., Bull. WHO 1992 (via Pitt Supercourse)", tsize=14)
    ax = ax_at(fig, w, h, 0.35, 0.5, 4.8, 1.75)
    vals = [88, 35, 9, 0]
    ax.bar(range(4), vals, width=0.52, color=[ORANGE, "#F09A74", "#F5C2A9", "#F5C2A9"], zorder=3)
    for x, v in enumerate(vals):
        ax.text(x, v + 4, f"{v}%", ha="center", fontsize=14, fontweight="bold", color=NAVY)
    ax.set_xticks(range(4))
    ax.set_xticklabels(["Day 1", "Day 2", "Day 3", "Day 4+"], fontsize=12)
    ax.set_ylim(0, 110)
    ax.set_yticks([])
    ax.yaxis.grid(False)
    save(fig, "s2_survival_by_day.png")


# ------------------------------------------------------------------ slide 4: LLM vs planner (5.6 x 2.8)
def s4_llm():
    w, h = 5.6, 2.8
    fig = card(w, h, "Who should plan? Plan correctness, obfuscated tasks", None,
               "PlanBench 'Mystery Blocksworld', 600 problems · Valmeekam et al. 2024", tsize=13.5)
    ax = fig.add_axes([0.24 / w, 0.45 / h, 5.1 / w, 1.75 / h])
    ax.axis("off")
    rows = [("Best general LLM", 0, "<5%", SLATE), ("Reasoning model (o1-preview)", 52.8, "52.8%", LSLATE),
            ("Classical planner (0.27 s)", 100, "100%", ORANGE)]
    for i, (lab, v, txt, col) in enumerate(rows):
        y = 2 - i
        ax.text(0, y + 0.28, lab, fontsize=11.5, color=NAVY if i == 2 else INK2, fontweight="bold" if i == 2 else "normal")
        ax.barh(y - 0.08, 100, height=0.28, left=0, color="#EEF1F5")
        ax.barh(y - 0.08, max(v, 1.2), height=0.28, left=0, color=col)
        ax.text(102, y - 0.08, txt, fontsize=12.5, fontweight="bold", color=NAVY, va="center")
    ax.set_xlim(0, 118)
    ax.set_ylim(-0.4, 2.6)
    save(fig, "s4_llm_vs_planner.png")


# ------------------------------------------------------------------ slide 5: KPI small multiples (9.05 x 3.95)
def s5_kpis():
    w, h = 9.05, 3.95
    m = S["main"]
    fig = card(w, h, "300 randomised disruption scenarios", "same seeds for every policy · mean ± 95% CI",
               "CONCORD v0 benchmark, seeds 1000–1299 · avoidable losses exclude injected hardware failures", tsize=15)
    panels = [("time_to_aid", "Time-to-aid", "ticks, lower = better", "{:.1f}"),
              ("report_latency", "Critical-report delay", "ticks, lower = better", "{:.1f}"),
              ("agents_lost_non_injected", "Avoidable losses", "per mission, lower = better", "{:.2f}"),
              ("success", "Mission success", "%", "{:.0f}%")]
    order = ["concord", "greedy", "static"]
    for i, (k, t, hint, fmt) in enumerate(panels):
        ax = ax_at(fig, w, h, 0.3 + i * 2.19, 0.62, 1.9, 1.95)
        mult = 100 if k == "success" else 1
        vals = [m[p][k][0] * mult for p in order]
        lo = [m[p][k][1] * mult for p in order]
        hi = [m[p][k][2] * mult for p in order]
        ax.bar(range(3), vals, width=0.62, color=[POL[p][1] for p in order], zorder=3)
        ax.errorbar(range(3), vals, yerr=[np.subtract(vals, lo), np.subtract(hi, vals)], fmt="none", ecolor=NAVY,
                    elinewidth=0.9, capsize=2.5, zorder=4)
        top = max(hi) * 1.3
        ax.set_ylim(0, top)
        ax.set_yticks([])
        ax.yaxis.grid(False)
        for x, v, hv in zip(range(3), vals, hi):
            ax.text(x, hv + top * 0.03, fmt.format(v), ha="center", fontsize=11, fontweight="bold",
                    color=NAVY if x == 0 else INK2)
        ax.set_xticks(range(3))
        ax.set_xticklabels(["CONC.", "Greedy", "Static"], fontsize=10.5)
        ax.set_title(t, loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=16)
        ax.text(0, 1.03, hint, transform=ax.transAxes, fontsize=9.5, color=MUTED)
    save(fig, "s5_benchmark_kpis.png")


# ------------------------------------------------------------------ slide 5: stress (9.05 x 4.2)
def s5_stress():
    w, h = 9.05, 4.2
    st = S["stress"]
    ks = list(range(7))
    fig = card(w, h, "The more the plan breaks, the bigger the lead", "100 missions per point · x = disruption types at once",
               "CONCORD v0 stress sweep, seeds 2000–2099 per level", tsize=15)
    for i, (k, lab, mult) in enumerate((("success", "Mission success", 100), ("agents_lost_non_injected", "Avoidable losses / mission", 1))):
        ax = ax_at(fig, w, h, 0.55 + i * 4.3, 0.62, 3.2, 2.2)
        for p in ("static", "greedy", "concord"):
            y = [st[str(kk)][p][k][0] * mult for kk in ks]
            ax.plot(ks, y, color=POL[p][1], lw=2.6 if p == "concord" else 2.0, marker="o", ms=4.5,
                    markeredgecolor="white", markeredgewidth=1, zorder=3 if p == "concord" else 2)
            txt = f"{y[-1]:.0f}%" if mult == 100 else f"{y[-1]:.2f}"
            off = 0
            if mult == 1:
                off = {"greedy": 0.015, "static": -0.015, "concord": 0}[p]
            ax.text(6.2, y[-1] + off, txt, fontsize=10.5, color=NAVY if p == "concord" else INK2,
                    fontweight="bold" if p == "concord" else "normal", va="center")
        ax.set_xticks(ks)
        ax.set_xlim(-0.2, 6.2)
        if mult == 100:
            ax.set_ylim(0, 108)
            ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_title(lab, loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=6)
    # legend
    lx = 5.35
    for p in ("concord", "greedy", "static"):
        fig.lines.append(matplotlib.lines.Line2D([lx / w, (lx + 0.25) / w], [(h - 0.70) / h] * 2, color=POL[p][1], lw=2.6,
                                                 transform=fig.transFigure))
        fig.text((lx + 0.31) / w, (h - 0.70) / h, POL[p][0].replace(" dispatch", "").replace(" plan", ""), fontsize=10.5,
                 color=INK2, va="center")
        lx += 1.2
    save(fig, "s5_stress_sweep.png")


# ------------------------------------------------------------------ slide 7: scaling (4.7 x 3.05)
def s7_scaling():
    w, h = 4.7, 3.05
    fig = card(w, h, "Re-plan time vs swarm size", "1 CPU core, pure Python, 3 tasks per agent",
               "CONCORD v0 scaling test (scaling.py)", tsize=14)
    ax = ax_at(fig, w, h, 0.62, 0.78, 2.55, 1.45)
    n = [r["n"] for r in SC]
    g = [r["global_ms"] for r in SC]
    rp = [r["repair_ms"] for r in SC]
    ax.plot(n, g, color=SLATE, lw=2, marker="o", ms=4, markeredgecolor="white")
    ax.plot(n, rp, color=ORANGE, lw=2.4, marker="o", ms=4, markeredgecolor="white")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(n)
    ax.set_xticklabels([str(v) for v in n], fontsize=10)
    ax.minorticks_off()
    ax.set_yticks([0.1, 1, 10, 100, 1000])
    ax.set_yticklabels(["0.1ms", "1ms", "10ms", "100ms", "1s"], fontsize=10)
    ax.set_ylim(0.08, 6000)
    ax.set_xlabel("agents", fontsize=10, color=INK2, labelpad=2)
    ax.text(215, rp[-1], f"repair\n{rp[-1]:.1f} ms", fontsize=10.5, color=NAVY, fontweight="bold", va="center")
    ax.text(215, g[-1], f"global\n{g[-1] / 1000:.1f} s", fontsize=10.5, color=INK2, va="center")
    save(fig, "s7_scaling_latency.png")


# ------------------------------------------------------------------ slide 7: market (4.3 x 2.9)
def s7_market():
    w, h = 4.3, 2.9
    fig = card(w, h, "Swarm robotics market", "US$ billion, CAGR 33%",
               "MarketGlass (Global Industry Analysts) via GII, 2025", tsize=14)
    ax = ax_at(fig, w, h, 0.45, 0.5, 3.4, 1.55)
    vals = [1.1, 6.2]
    ax.bar([0, 1], vals, width=0.45, color=[LSLATE, ORANGE], zorder=3)
    for x, v in enumerate(vals):
        ax.text(x, v + 0.25, f"${v}B", ha="center", fontsize=14, fontweight="bold", color=NAVY)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["2024", "2030"], fontsize=12)
    ax.set_ylim(0, 7.8)
    ax.set_yticks([])
    ax.yaxis.grid(False)
    save(fig, "s7_market.png")


# ------------------------------------------------------------------ backup: forecast timeline (9.05 x 3.6)
def s_forecast():
    w, h = 9.05, 3.6
    tl = sorted(SB["timeline"])
    esc = SB["escalation"]
    fig = card(w, h, "Escalation driven by a live forecast", "storyboard mission · P(success) from 40 rollouts",
               "CONCORD v0 storyboard (seed 6) · red dot = forecast for 'hold' at t=86; operator approved option B", tsize=15)
    ax = ax_at(fig, w, h, 0.65, 0.55, 8.0, 2.1)
    ax.axvspan(75, 155, color="#9B6BFF", alpha=0.09, lw=0)
    ax.text(115, 103, "storm over sector C", color="#6A4FB3", fontsize=10, ha="center")
    ax.axhline(60, color=RED, lw=1)
    ax.text(1, 63, "escalate below 60%", color=RED, fontsize=10)
    ts = [t for t, p in tl if t != esc["t"]]
    ps = [p * 100 for t, p in tl if t != esc["t"]]
    ax.plot(ts, ps, color=ORANGE, lw=2.4, marker="o", ms=4, markeredgecolor="white", zorder=3)
    ax.scatter([esc["t"]], [0], s=40, color=RED, zorder=4)
    pb = [o["p"] for o in esc["options"] if o["key"] == "B"][0] * 100
    ax.text(esc["t"] + 3, 8, f"rover lost: hold → {esc['p_now'] * 100:.0f}%, fly-through → {pb:.0f}% · human approves",
            fontsize=10, color=NAVY)
    ax.set_xlim(0, 172)
    ax.set_ylim(-4, 110)
    ax.set_yticks([0, 50, 100])
    ax.set_yticklabels(["0%", "50%", "100%"])
    save(fig, "backup_forecast_timeline.png")


if __name__ == "__main__":
    s2_survival()
    s4_llm()
    s5_kpis()
    s5_stress()
    s7_scaling()
    s7_market()
    s_forecast()
