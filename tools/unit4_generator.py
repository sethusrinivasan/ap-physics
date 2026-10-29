#!/usr/bin/env python3
"""Build all 36 Unit 4 interactive walkthroughs, QR codes, audio, and TOC."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import escape
from pathlib import Path
import qrcode
import qrcode.image.svg

ROOT = Path("/home/home/github/ap-physics")
UNIT4 = ROOT / "unit4"
FIG_DIR = UNIT4 / "figures"
PARSED_JSON = ROOT / "tools" / "unit4_parsed.json"

# Read layout CSS and JS template from Unit 2 Q90
Q90_HTML = (ROOT / "unit2" / "q90" / "index.html").read_text()

STYLE_START = Q90_HTML.find("<style>")
STYLE_END = Q90_HTML.find("</style>")
CSS_CONTENT = Q90_HTML[STYLE_START + len("<style>\n") : STYLE_END].strip()

JS_DOLLAR = Q90_HTML.find("    const $ = (id) => document.getElementById(id);")
JS_END = Q90_HTML.rfind("  </script>")
JS_ENGINE = Q90_HTML[JS_DOLLAR:JS_END].strip()


def chunks(text: str, max_chars: int = 150) -> list[str]:
    text = re.sub(r"[’‘]", "'", str(text))
    text = re.sub(r"[“”]", '"', text)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    cur = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) > max_chars:
            if cur:
                out.append(cur)
                cur = ""
            words = s.split()
            piece = ""
            for w in words:
                nxt = f"{piece} {w}" if piece else w
                if len(nxt) > max_chars and piece:
                    out.append(piece)
                    piece = w
                else:
                    piece = nxt
            if piece:
                out.append(piece)
            continue
        nxt = f"{cur} {s}" if cur else s
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            out.append(cur)
            cur = s
    if cur:
        out.append(cur)
    return out


def google_tts(text: str) -> bytes:
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=en-US&q={urllib.parse.quote(text)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "audio/mpeg,audio/webm,audio/*;q=0.9,*/*;q=0.8",
            "Referer": "https://translate.google.com/",
        },
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = resp.read()
                if len(data) >= 500:
                    return data
        except Exception:
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"TTS failed for text: {text[:60]}")


def step_speech(step: dict) -> str:
    parts = []
    if step.get("lead"):
        parts.append(step["lead"])
    for block in step.get("blocks", []):
        if block.get("vars"):
            parts.append("Here is what each symbol means.")
            for item in block["vars"]:
                parts.append(f"{item['say']} means {item['meaning']}.")
        if block.get("explain"):
            parts.append(block["explain"])
        if block.get("speakFormula"):
            parts.append(block["speakFormula"])
    return " ".join(parts)


def make_qr_svg(url: str, dest_path: Path) -> None:
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(image_factory=factory, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    dest_path.write_bytes(img.to_string())
