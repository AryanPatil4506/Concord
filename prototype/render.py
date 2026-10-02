#!/usr/bin/env python3
"""Mission-console renderer for CONCORD v0 frames (matplotlib, dark ops theme)."""
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Wedge  # noqa: E402
import numpy as np  # noqa: E402

import concord_sim as cs  # noqa: E402

plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]

BG = "#081629"
PANEL = "#0E2240"
INK = "#EAF1FB"
INK2 = "#9FB3CF"
MUTED = "#5F7697"
LAND = "#122846"
WATER = "#1F5E93"
BUILD = "#2A3D5C"
BRIDGE = "#C9A45C"
LINK = "#35E0B0"
STORM = "#9B6BFF"
DEAD = "#FF5C6C"
AGENT_COL = {"scout": "#43D2FF", "cargo": "#FF914D", "rover": "#FFCD82", "relay": "#C3A6FF"}
AGENT_MARK = {"scout": "^", "cargo": "v", "rover": "s", "relay": "D"}
# map labels use the full agent names: survivors are labelled S1..S6, so "S1"/"S2" for the scouts would be ambiguous
SHORT = {"Scout-1": "Scout-1", "Scout-2": "Scout-2", "Cargo-1": "Cargo-1", "Rover-1": "Rover-1", "Relay-1": "Relay-1"}


def _terrain_rgb(terr):
    cmap = ListedColormap([LAND, WATER, BUILD])
    return cmap, terr


def draw_map(ax, fr, terr, dead, bridges_alive, show_hidden=None, highlight=None):
    ax.set_facecolor(BG)
    cmap, t = _terrain_rgb(terr)
    ax.imshow(t, cmap=cmap, vmin=0, vmax=2, origin="upper", extent=(-0.5, cs.W - 0.5, cs.H - 0.5, -0.5),
              interpolation="nearest", zorder=0)
    # bridges
    for cells in bridges_alive:
        for (x, y) in cells:
            ax.add_patch(Rectangle((x - 0.5, y - 0.35), 1, 0.7, color=BRIDGE, zorder=1, lw=0))
    # dead zones
    if dead is not None and dead.any():
        ov = np.zeros((cs.H, cs.W, 4))
        ov[dead] = matplotlib.colors.to_rgba(DEAD, 0.20)
        ax.imshow(ov, origin="upper", extent=(-0.5, cs.W - 0.5, cs.H - 0.5, -0.5), zorder=2, interpolation="nearest")
        ys, xs = np.nonzero(dead)
        ax.scatter(xs, ys, marker="x", s=10, c=DEAD, alpha=0.35, linewidths=0.8, zorder=2)
    # storm
    if fr["storm"] is not None:
        cx, cy, r, _ = fr["storm"]
        for k, a in ((1.0, 0.10), (0.8, 0.10), (0.6, 0.12), (0.4, 0.14)):
            ax.add_patch(Circle((cx, cy), r * k, color=STORM, alpha=a, lw=0, zorder=2))
        ax.add_patch(Circle((cx, cy), r, fill=False, ec=STORM, lw=1.4, ls=(0, (4, 3)), zorder=3))
        ax.text(cx, cy - r - 0.7, "STORM CELL", color=STORM, ha="center", va="bottom", fontsize=7.5,
                fontweight="bold", zorder=6)
    # sectors
    for name, (x0, x1, y0, y1) in cs.SECTORS.items():
        ax.add_patch(Rectangle((x0 - 0.5, y0 - 0.5), x1 - x0, y1 - y0, fill=False, ec="#6F87AA", lw=0.8,
                               ls=(0, (2, 3)), zorder=3))
        ax.text(x0 + 0.1, y0 + 0.3, f"SECTOR {name}", color="#8FA6C8", fontsize=7, fontweight="bold",
                va="top", ha="left", zorder=6)
    # survey waypoints
    for (pos, st) in fr["surveys"]:
        ax.scatter([pos[0]], [pos[1]], s=9, c=("#35E0B0" if st == "done" else "#50698C"), zorder=4, lw=0)
    # comm links
    nodes = [("BASE", cs.BASE, cs.BASE_COMM)] + [(a["id"], a["pos"], cs.SPECS[a["kind"]]["comm"])
                                                 for a in fr["agents"] if a["alive"] and a["conn"]]
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            (_, p, r1), (_, q, r2) = nodes[i], nodes[j]
            if np.hypot(p[0] - q[0], p[1] - q[1]) <= max(r1, r2):
                ax.plot([p[0], q[0]], [p[1], q[1]], color=LINK, lw=0.9, alpha=0.45, zorder=5)
    # planned routes
    for a in fr["agents"]:
        if not a["alive"] or not a["plan"]:
            continue
        pts = [a["pos"]] + a["plan"][:4]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=AGENT_COL[a["kind"]], lw=1.1, alpha=0.55,
                ls=(0, (3, 2)), zorder=5)
    # survivors
    for s in fr["survivors"]:
        x, y = s["pos"]
        if s["delivered"]:
            ax.scatter([x], [y], marker="o", s=70, facecolor="#1FBF75", edgecolor="white", lw=1.0, zorder=7)
            ax.text(x, y + 0.05, "✓", color="white", ha="center", va="center", fontsize=7, fontweight="bold", zorder=8)
        elif s["reported"]:
            ax.scatter([x], [y], marker="P", s=85, c="#FF4D5E", edgecolors="white", linewidths=0.8, zorder=7)
        elif s["detected"]:
            ax.scatter([x], [y], marker="P", s=85, c="#FFB547", edgecolors="white", linewidths=0.8, zorder=7)
        elif show_hidden:
            ax.scatter([x], [y], marker="P", s=40, c="none", edgecolors="#5F7697", linewidths=0.8, zorder=7)
        if s["detected"] or s["delivered"]:
            ax.text(x + 0.7, y - 0.6, s["sid"], color=INK, fontsize=7, fontweight="bold", zorder=8)
    # base
    ax.scatter([cs.BASE[0]], [cs.BASE[1]], marker="h", s=260, c="#FFFFFF", edgecolors=LINK, linewidths=1.5, zorder=8)
    ax.text(cs.BASE[0], cs.BASE[1] + 1.5, "BASE", color=INK, ha="center", va="top", fontsize=7.5, fontweight="bold",
            zorder=8)
    # agents
    for a in fr["agents"]:
        x, y = a["pos"]
        col = AGENT_COL[a["kind"]]
        if not a["alive"]:
            ax.scatter([x], [y], marker="X", s=90, c="#7C8BA3", edgecolors=BG, linewidths=1, zorder=9)
            flip = x > cs.W - 8   # keep labels inside the map near the right edge
            ax.text(x - 0.8 if flip else x + 0.8, y + 0.2, f"{SHORT[a['id']]} lost", color="#9AA8BD", fontsize=7,
                    ha="right" if flip else "left", zorder=9)
            continue
        ax.scatter([x], [y], marker=AGENT_MARK[a["kind"]], s=120, c=col, edgecolors=BG, linewidths=1.2, zorder=9)
        if not a["conn"]:
            ax.add_patch(Circle((x, y), 1.15, fill=False, ec=DEAD, lw=1.2, ls=(0, (2, 2)), zorder=9))
        lab = f"{SHORT[a['id']]} {a['batt'] * 100:.0f}%"
        flip = x > cs.W - 8
        ax.text(x - 0.8 if flip else x + 0.8, y - 0.55, lab, color=INK, fontsize=7.2, fontweight="bold", zorder=10,
                ha="right" if flip else "left",
                bbox=dict(boxstyle="round,pad=0.15", fc=BG, ec="none", alpha=0.65))
        if highlight and a["id"] == highlight:
            ax.add_patch(Circle((x, y), 1.8, fill=False, ec="#FFFFFF", lw=1.6, zorder=10))
    ax.set_xlim(-0.5, cs.W - 0.5)
    ax.set_ylim(cs.H - 0.5, -0.5)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


def gauge(ax, p, threshold=0.6):
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-0.35, 1.25)
    ax.axis("off")
    ax.add_patch(Wedge((0, 0), 1.0, 0, 180, width=0.22, color="#223A5E", lw=0))
    col = "#35E0B0" if p >= 0.8 else ("#FFB547" if p >= threshold else "#FF4D5E")
    ax.add_patch(Wedge((0, 0), 1.0, 180 - 180 * p, 180, width=0.22, color=col, lw=0))
    th = np.pi * (1 - threshold)
    ax.plot([0.74 * np.cos(th), 1.06 * np.cos(th)], [0.74 * np.sin(th), 1.06 * np.sin(th)], color=INK, lw=1.4)
    ax.text(0, 0.18, f"{p * 100:.0f}%", color=INK, ha="center", va="center", fontsize=22, fontweight="bold")
    ax.text(0, -0.2, "P(mission success)", color=INK2, ha="center", va="center", fontsize=8.5)
    ax.text(1.08 * np.cos(th) - 0.05, 1.08 * np.sin(th) + 0.08, "escalate\n< 60%", color=INK2, ha="right",
            va="bottom", fontsize=6.5)


def draw_console(fr, terr, dead, bridges_alive, log_lines, p_success, out, title_extra="", escalation=None,
                 show_hidden=False, highlight=None, dpi=110):
    fig = plt.figure(figsize=(12.8, 7.2), facecolor=BG)
    ax = fig.add_axes([0.015, 0.06, 0.66, 0.86])
    draw_map(ax, fr, terr, dead, bridges_alive, show_hidden=show_hidden, highlight=highlight)
    fig.text(0.017, 0.955, "CONCORD", color=INK, fontsize=15, fontweight="bold", va="center")
    fig.text(0.105, 0.955, "mission console  ·  flood search & rescue  ·  prototype v0 (simulation)", color=INK2,
             fontsize=9.5, va="center")
    fig.text(0.675, 0.955, f"t = {fr['t']:>3d}", color=INK, fontsize=12, fontweight="bold", va="center", ha="right")
    # legend strip (auto-spaced)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="^", color=AGENT_COL["scout"], lw=0, ms=7),
               Line2D([], [], marker="v", color=AGENT_COL["cargo"], lw=0, ms=7),
               Line2D([], [], marker="s", color=AGENT_COL["rover"], lw=0, ms=7),
               Line2D([], [], marker="D", color=AGENT_COL["relay"], lw=0, ms=6),
               Line2D([], [], marker="P", color="#FF4D5E", lw=0, ms=8),
               Line2D([], [], marker="o", color="#1FBF75", lw=0, ms=7),
               Line2D([], [], color=LINK, lw=1.4),
               Line2D([], [], marker="s", color=DEAD, alpha=0.45, lw=0, ms=8)]
    labels = ["Scout drone", "Cargo drone", "Rover (UGV)", "Relay drone", "Survivor – aid pending",
              "Aid delivered", "Comm link", "Dead zone"]
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.012), ncol=8, frameon=False,
              fontsize=7.6, labelcolor=INK2, handletextpad=0.35, columnspacing=1.1)
    # right panel
    pax = fig.add_axes([0.69, 0.0, 0.31, 1.0])
    pax.set_facecolor(PANEL)
    pax.set_xticks([])
    pax.set_yticks([])
    for sp in pax.spines.values():
        sp.set_visible(False)
    gax = fig.add_axes([0.715, 0.66, 0.26, 0.26])
    gauge(gax, p_success)
    fig.text(0.705, 0.955, "FEASIBILITY FORECAST", color=INK2, fontsize=8.5, fontweight="bold", va="center")
    fig.text(0.705, 0.635, "Monte-Carlo rollouts of the current plan (K=40)", color=MUTED, fontsize=7.2)
    # agents table
    y = 0.595
    fig.text(0.705, y, "SWARM", color=INK2, fontsize=8.5, fontweight="bold")
    y -= 0.03
    for a in fr["agents"]:
        col = AGENT_COL[a["kind"]] if a["alive"] else "#7C8BA3"
        status = "LOST" if not a["alive"] else ("linked" if a["conn"] else "NO LINK")
        fig.text(0.705, y, "■", color=col, fontsize=9, va="center")
        fig.text(0.722, y, a["id"], color=INK, fontsize=8, va="center")
        batt = 0 if not a["alive"] else a["batt"]
        fig.add_artist(Rectangle((0.80, y - 0.006), 0.08, 0.012, transform=fig.transFigure, color="#223A5E", lw=0))
        bcol = "#35E0B0" if batt > 0.45 else ("#FFB547" if batt > 0.25 else "#FF4D5E")
        fig.add_artist(Rectangle((0.80, y - 0.006), 0.08 * max(0, batt), 0.012, transform=fig.transFigure, color=bcol,
                                 lw=0))
        fig.text(0.887, y, status, color=(INK2 if status == "linked" else "#FF7A85"), fontsize=7.2, va="center")
        y -= 0.028
    # decision log
    y -= 0.02
    fig.text(0.705, y, "DECISION LOG (auto-explained)", color=INK2, fontsize=8.5, fontweight="bold")
    y -= 0.012
    for (t, txt) in log_lines[-7:][::-1]:
        wrapped = textwrap.wrap(txt, 52)[:3]
        y -= 0.028
        fig.text(0.705, y, f"t={t}", color=LINK, fontsize=7, va="top", fontweight="bold")
        for k, line in enumerate(wrapped):
            fig.text(0.742, y - k * 0.022, line, color=INK, fontsize=7, va="top")
        y -= 0.022 * (len(wrapped) - 1)
        if y < 0.05:
            break
    if escalation:
        ex = fig.add_axes([0.03, 0.56, 0.43, 0.3])
        ex.set_xlim(0, 1)
        ex.set_ylim(0, 1)
        ex.axis("off")
        ex.add_patch(FancyBboxPatch((0.0, 0.0), 1, 1, boxstyle="round,pad=0.0,rounding_size=0.04", fc="#0B1B33",
                                    ec="#FFB547", lw=2))
        ex.text(0.04, 0.87, "⚠  ESCALATION — operator decision requested", color="#FFB547", fontsize=10.5,
                fontweight="bold", va="center")
        ex.text(0.04, 0.74, textwrap.fill(escalation["situation"], 78), color=INK, fontsize=7.8, va="top",
                linespacing=1.35)
        yy = 0.36
        for opt in escalation["options"]:
            star = "  ← recommended" if opt["key"] == escalation["recommend"] else ""
            ex.text(0.04, yy, f"{opt['key']})  {opt['text']}", color=INK, fontsize=7.9, va="center")
            ex.text(0.97, yy, f"P(success) {opt['p'] * 100:.0f}%{star}", color=("#35E0B0" if star else INK2),
                    fontsize=7.9, va="center", ha="right", fontweight=("bold" if star else "normal"))
            yy -= 0.13
        ex.text(0.04, 0.08, f"Safe default on timeout (30 s): option {escalation['recommend']}  ·  every option scored by 40 rollouts",
                color=INK2, fontsize=7.4, va="center")
    fig.savefig(out, dpi=dpi, facecolor=BG)
    plt.close(fig)
