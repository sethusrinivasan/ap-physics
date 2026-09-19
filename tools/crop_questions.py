#!/usr/bin/env python3
"""Crop each Unit 2 question (stem, figure, and A–D choices) from the exam PDF."""
from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path("/home/home/ap-physics")
Q_PDF = Path("/home/home/Downloads/Unit 2 Topic Questions.pdf")
UNIT2 = ROOT / "unit2"
FIG_DIR = UNIT2 / "figures"
HIRES_DIR = FIG_DIR / "hires"
REPORT = FIG_DIR / "crop-report.json"

DPI = 200
SCALE = DPI / 72.0
PAGE_W_PT = 612.0
PAGE_H_PT = 792.0
CONTENT_TOP = 68.0  # below "Unit 2: Topic Questions"
FOOTER_Y = 760.0
PAD_TOP = 10.0
PAD_BEFORE_NEXT = 10.0
PAD_X = 22.0
MIN_SLICE_PT = 22.0


def pdf_bbox_xml(path: Path) -> str:
    return subprocess.check_output(["pdftotext", "-bbox", str(path), "-"], text=True, errors="replace")


def parse_pages(xml: str) -> list[list[tuple[float, float, float, float, str]]]:
    chunks = re.split(r"<page\b[^>]*>", xml)[1:]
    pages = []
    for chunk in chunks:
        words = [
            (float(a), float(b), float(c), float(d), t.strip())
            for a, b, c, d, t in re.findall(
                r'<word xMin="([^"]+)" yMin="([^"]+)" xMax="([^"]+)" yMax="([^"]+)">([^<]*)</word>',
                chunk,
            )
        ]
        pages.append(words)
    return pages


def question_starts(pages) -> list[tuple[int, int, float]]:
    found = []
    for pno, words in enumerate(pages, 1):
        for xmin, ymin, xmax, ymax, t in words:
            if xmin < 52 and re.fullmatch(r"\d+\.", t):
                n = int(t[:-1])
                if 1 <= n <= 90:
                    found.append((n, pno, ymin))
    found.sort(key=lambda x: x[0])
    nums = [n for n, _, _ in found]
    if nums != list(range(1, 91)):
        raise SystemExit(f"Question markers incomplete: {nums[:8]}… count={len(nums)}")
    return found


def render_hires() -> None:
    HIRES_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(HIRES_DIR.glob("page-*.png"))
    if len(existing) >= 51:
        return
    subprocess.check_call(
        ["pdftoppm", "-png", "-r", str(DPI), str(Q_PDF), str(HIRES_DIR / "page")]
    )


def pt_px(v: float) -> int:
    return int(round(v * SCALE))


def crop_slice(page_img: Image.Image, y0_pt: float, y1_pt: float) -> Image.Image:
    x0 = pt_px(PAD_X)
    x1 = pt_px(PAGE_W_PT - PAD_X)
    y0 = max(0, pt_px(y0_pt))
    y1 = min(page_img.height, pt_px(y1_pt))
    if y1 <= y0 + 4:
        return Image.new("RGB", (1, 1), "white")
    return page_img.crop((x0, y0, x1, y1))


def stitch(parts: list[Image.Image]) -> Image.Image:
    parts = [p for p in parts if p.width > 4 and p.height > 4]
    if not parts:
        raise SystemExit("empty crop")
    width = max(p.width for p in parts)
    height = sum(p.height for p in parts)
    out = Image.new("RGB", (width, height), "white")
    y = 0
    for p in parts:
        out.paste(p, (0, y))
        y += p.height
    return trim_whitespace(out)


def trim_whitespace(im: Image.Image, pad: int = 16) -> Image.Image:
    px = im.load()
    w, h = im.size

    def row_ink(y: int) -> bool:
        for x in range(0, w, 3):
            r, g, b = px[x, y]
            if r < 245 or g < 245 or b < 245:
                return True
        return False

    top, bottom = 0, h - 1
    left, right = 0, w - 1
    while top < h and not row_ink(top):
        top += 1
    while bottom > top and not row_ink(bottom):
        bottom -= 1

    def col_ink(x: int) -> bool:
        for y in range(top, bottom + 1, 3):
            r, g, b = px[x, y]
            if r < 245 or g < 245 or b < 245:
                return True
        return False

    while left < w and not col_ink(left):
        left += 1
    while right > left and not col_ink(right):
        right -= 1
    left = max(0, left - pad)
    right = min(w - 1, right + pad)
    top = max(0, top - pad)
    bottom = min(h - 1, bottom + pad)
    # Drop the exam-page footer rule if it is the last ink.
    for y in range(bottom, max(top, bottom - int(0.06 * h)), -1):
        ink_xs = [x for x in range(0, w, 2) if px[x, y][0] < 245]
        if len(ink_xs) > 0.55 * (w / 2):
            # likely a full-width rule
            above_clear = True
            for yy in range(max(top, y - 10), y):
                if row_ink(yy) and yy != y:
                    # content immediately above — keep
                    above_clear = False
                    break
            if above_clear or True:
                # if the next nonwhite above is more than 8px away, drop the rule
                prev = y - 1
                while prev > top and not row_ink(prev):
                    prev -= 1
                if y - prev > 8:
                    bottom = prev + pad
                    break
    bottom = min(h - 1, max(top + 20, bottom))
    return im.crop((left, top, right + 1, bottom + 1))


def words_in_rect(words, y0, y1):
    return [w for w in words if w[1] < y1 and w[3] > y0]


def slices_for(n, start_page, start_y, end_page, end_y, n_pages):
    out = []
    for p in range(start_page, end_page + 1):
        y0 = start_y - PAD_TOP if p == start_page else CONTENT_TOP
        y1 = end_y - PAD_BEFORE_NEXT if p == end_page else FOOTER_Y
        y0 = max(0.0, y0)
        y1 = min(PAGE_H_PT, y1)
        if y1 - y0 >= MIN_SLICE_PT:
            out.append((p, y0, y1))
    return out


def validate_crop(n, slices, pages) -> dict:
    letters = set()
    qnums = set()
    for p, y0, y1 in slices:
        for xmin, ymin, xmax, ymax, t in words_in_rect(pages[p - 1], y0, y1):
            if re.fullmatch(r"\([A-D]\)", t):
                letters.add(t[1])
            if xmin < 52 and re.fullmatch(r"\d+\.", t):
                qn = int(t[:-1])
                if 1 <= qn <= 90:
                    qnums.add(qn)
    extra = sorted(qnums - {n})
    missing = [L for L in "ABCD" if L not in letters]
    return {
        "n": n,
        "pages": [s[0] for s in slices],
        "slices": [(p, round(a, 1), round(b, 1)) for p, a, b in slices],
        "letters": "".join(L for L in "ABCD" if L in letters),
        "missing_choices": missing,
        "extra_questions": extra,
        "ok": not missing and extra == [],
    }


def crop_all(force: bool = False) -> list[dict]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    xml = pdf_bbox_xml(Q_PDF)
    pages = parse_pages(xml)
    starts = question_starts(pages)
    render_hires()
    page_imgs = {}
    reports = []
    n_pages = len(pages)

    for i, (n, p0, y0) in enumerate(starts):
        dest = FIG_DIR / f"q{n:02d}.png"
        if i + 1 < len(starts):
            _, p1, y1 = starts[i + 1]
        else:
            p1, y1 = n_pages, FOOTER_Y
            # last item: trim to last content on the final page
            last_words = pages[p1 - 1]
            content_ys = [w[3] for w in last_words if w[1] < FOOTER_Y and w[0] < 560]
            if content_ys:
                y1 = min(FOOTER_Y, max(content_ys) + 18)

        slices = slices_for(n, p0, y0, p1, y1, n_pages)
        report = validate_crop(n, slices, pages)
        report["file"] = dest.name

        if dest.exists() and not force and dest.stat().st_size > 8000 and report["ok"]:
            im = Image.open(dest)
            report["px"] = list(im.size)
            reports.append(report)
            continue

        parts = []
        for p, a, b in slices:
            if p not in page_imgs:
                img_path = HIRES_DIR / f"page-{p:02d}.png"
                if not img_path.exists():
                    raise SystemExit(f"missing hires page {img_path}")
                page_imgs[p] = Image.open(img_path).convert("RGB")
            parts.append(crop_slice(page_imgs[p], a, b))
        crop = stitch(parts)
        crop.save(dest, "PNG", optimize=True)
        report["px"] = list(crop.size)
        report["bytes"] = dest.stat().st_size
        reports.append(report)

    bad = [r for r in reports if not r["ok"]]
    REPORT.write_text(json.dumps({"dpi": DPI, "bad": bad, "all": reports}, indent=2))
    print(f"crops {len(reports)}  bad {len(bad)}")
    for r in bad:
        print(" FAIL", r)
    if bad:
        raise SystemExit("crop validation failed")
    return reports


if __name__ == "__main__":
    crop_all(force=True)
