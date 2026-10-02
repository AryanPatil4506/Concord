#!/usr/bin/env python3
"""Render every diagrams/*.html `.canvas` to charts/<name>.png at 2x (transparent corners)."""
import glob
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "charts")
os.makedirs(OUT, exist_ok=True)

names = sys.argv[1:] or [os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(HERE, "*.html"))]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1800, "height": 1400}, device_scale_factor=2)
    for n in names:
        pg.goto("file://" + os.path.join(HERE, n + ".html"))
        pg.wait_for_timeout(300)
        pg.evaluate("document.fonts.ready")
        el = pg.query_selector(".canvas")
        out = os.path.join(OUT, f"diagram_{n}.png")
        el.screenshot(path=out, omit_background=True)
        print("wrote", out)
    b.close()
