#!/usr/bin/env python3
"""Render the storyboard mission into console frames, slide stills, a GIF and an MP4."""
import os
import pickle
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concord_sim as cs  # noqa: E402
import render  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FR = os.path.join(HERE, "frames")
MEDIA = os.path.join(HERE, "media")
os.makedirs(FR, exist_ok=True)
os.makedirs(MEDIA, exist_ok=True)

D = pickle.load(open(os.path.join(RES, "storyboard_frames.pkl"), "rb"))
frames, log, timeline, esc = D["frames"], D["log"], D["timeline"], D["escalation"]
bridges = D["bridges"]
KEEP = {"event", "battery", "voi", "assign", "deliver", "loss", "escalation", "report"}


def tidy(txt):
    txt = txt.replace("->", "→").replace("EVENT: ", "⚡ ")
    m = re.match(r"(Deliver S\d+) → (\S+) \(bid ([\d.]+), ETA t\+(\d+); others: (.*)\)", txt)
    if m:
        others = [o.strip() for o in m.group(5).split(",") if "ineligible" not in o]
        alt = f" vs {others[0].replace(' bid', '')}" if others else ""
        return f"{m.group(1)} → {m.group(2)} (bid {m.group(3)}{alt}; ETA +{m.group(4)})"
    m = re.match(r"(Survey \w+) → (\S+) \(bid ([\d.]+), ETA t\+(\d+); others: (.*)\)", txt)
    if m:
        return f"{m.group(1)} → {m.group(2)} (bid {m.group(3)})"
    txt = txt.replace("Base receives ", "Base ← ")
    return txt


lines = []
for L in log:
    if L["kind"] not in KEEP:
        continue
    if L["kind"] == "assign" and not L["text"].startswith("Deliver") and L["t"] != 36:
        continue
    lines.append((L["t"], tidy(L["text"])))


def p_at(t):
    p = timeline[0][1]
    for (tt, pp) in timeline:
        if tt <= t:
            p = pp
    return p


def state_at(i):
    terr, dead = None, None
    for f in frames[: i + 1]:
        if f["terr"] is not None:
            terr = f["terr"]
        if f["dead"] is not None:
            dead = f["dead"]
    return terr, dead


def bridges_alive(terr):
    return [cells for cells in bridges if all(terr[y, x] == cs.LAND for (x, y) in cells)]


def render_frame(i, path, dpi=100, with_card=False, highlight=None):
    f = frames[i]
    terr, dead = state_at(i)
    ll = [(t, x) for (t, x) in lines if t <= f["t"]]
    card = esc if with_card else None
    p = esc["p_now"] if with_card else p_at(f["t"])
    if with_card:
        f = dict(f, t=esc["t"])
    if with_card:
        pa = [o["p"] for o in esc["options"] if o["key"] == "A"][0]
        pb = [o["p"] for o in esc["options"] if o["key"] == "B"][0]
        ll = ll + [(esc["t"], f"ESCALATION → operator card (hold {pa:.0%} vs fly-through {pb:.0%})")]
    render.draw_console(f, terr, dead, bridges_alive(terr), ll, p, path, escalation=card,
                        highlight=highlight, dpi=dpi)


if __name__ == "__main__":
    idx = {f["t"]: i for i, f in enumerate(frames)}
    last_t = frames[-1]["t"]
    # ---- slide stills (1920x1080)
    stills = {
        "still_1_survivor_found_t027.png": (27, False, "Cargo-1"),
        "still_2_battery_reserve_t036.png": (36, False, "Scout-2"),
        "still_3_deadzone_voi_t052.png": (52, False, "Scout-1"),
        "still_4_escalation_t086.png": (esc["t"] - 1 if esc else 86, True, None),
        f"still_5_mission_complete_t{last_t:03d}.png": (last_t, False, None),
    }
    only = sys.argv[1:] == ["stills"]
    for name, (t, card, hl) in stills.items():
        render_frame(idx[t], os.path.join(MEDIA, name), dpi=150, with_card=card, highlight=hl)
        print("still", name)
    if only:
        sys.exit(0)
    # ---- animation frames
    seq = []
    k = 0
    for i, f in enumerate(frames):
        if f["t"] % 2 and f["t"] != last_t:
            continue
        card = bool(esc) and f["t"] == esc["t"] - 1
        p = os.path.join(FR, f"f{k:04d}.png")
        render_frame(i, p, dpi=100, with_card=card)
        seq.append(p)
        k += 1
        if card:  # hold the escalation card ~3 s
            for _ in range(24):
                q = os.path.join(FR, f"f{k:04d}.png")
                os.link(p, q) if not os.path.exists(q) else None
                seq.append(q)
                k += 1
    for _ in range(16):  # hold the final frame
        q = os.path.join(FR, f"f{k:04d}.png")
        os.link(seq[-1], q) if not os.path.exists(q) else None
        k += 1
    print("frames", k)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i", os.path.join(FR, "f%04d.png"),
                    "-vf", "scale=1280:720:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-crf", "20",
                    os.path.join(MEDIA, "concord_demo.mp4")], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i", os.path.join(FR, "f%04d.png"),
                    "-vf", "scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4",
                    os.path.join(MEDIA, "concord_demo.gif")], check=True)
    print("done")
