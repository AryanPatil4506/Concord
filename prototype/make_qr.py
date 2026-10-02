#!/usr/bin/env python3
"""Make slide-ready QR codes for your public links (navy on white, with quiet zone).

    pip install qrcode pillow
    python make_qr.py "https://github.com/<neutral-org>/concord" repo
    python make_qr.py "https://youtu.be/<video-id>" demo

Writes qr_<name>.png next to this script. Scan every code with a phone before submitting.
"""
import sys

import qrcode

url, name = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "link")
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=20, border=3)
qr.add_data(url)
qr.make(fit=True)
qr.make_image(fill_color="#003470", back_color="white").save(f"qr_{name}.png")
print(f"wrote qr_{name}.png for {url}")
