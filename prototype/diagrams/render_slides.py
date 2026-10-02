#!/usr/bin/env python3
"""Render diagrams/slide_*.html to slides/<name>.png at 3x (≈288 dpi at placement size)."""
import glob
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "slides")
os.makedirs(OUT, exist_ok=True)
names = sys.argv[1:] or sorted(os.path.basename(p)[6:-5] for p in glob.glob(os.path.join(HERE, "slide_*.html")))
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1900, "height": 1200}, device_scale_factor=3)
    for n in names:
        pg.goto("file://" + os.path.join(HERE, f"slide_{n}.html"))
        pg.wait_for_timeout(250)
        pg.evaluate("document.fonts.ready")
        el = pg.query_selector(".canvas")
        el.screenshot(path=os.path.join(OUT, f"d_{n}.png"), omit_background=True)
        print("wrote", f"d_{n}.png")
    b.close()
