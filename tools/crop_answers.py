#!/usr/bin/env python3
"""Crop each official solution (Answer + explanation) from the Unit 2 solutions PDF."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from PIL import Image

from crop_questions import (
    CONTENT_TOP,
    DPI,
    FOOTER_Y,
    MIN_SLICE_PT,
    PAGE_H_PT,
    crop_slice,
    parse_pages,
    pdf_bbox_xml,
    slices_for,
    stitch,
)

ROOT = Path("/home/home/ap-physics")
S_PDF = Path("/home/home/Downloads/Unit 2 Topic Questions. Solutions.pdf")
FIG_DIR = ROOT / "figures"
HIRES_DIR = FIG_DIR / "sol-hires"
REPORT = FIG_DIR / "answer-crop-report.json"


def render_hires() -> None:
    HIRES_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(HIRES_DIR.glob("page-*.png"))
    if len(existing) >= 72:
        return
    subprocess.check_call(
        ["pdftoppm", "-png", "-r", str(DPI), str(S_PDF), str(HIRES_DIR / "page")]
    )


def question_starts(pages) -> list[tuple[int, int, float]]:
    found = []
    for pno, words in enumerate(pages, 1):
        for xmin, ymin, xmax, ymax, t in words:
            if xmin < 60 and re.fullmatch(r"\d+\.", t):
                n = int(t[:-1])
                if 1 <= n <= 90:
                    found.append((n, pno, ymin))
    found.sort(key=lambda x: (x[1], x[2], x[0]))
    nums = [n for n, _, _ in found]
    if nums != list(range(1, 91)):
        raise SystemExit(f"Solution question markers incomplete: {nums[:8]}… count={len(nums)}")
    return found


def answer_starts(pages) -> list[tuple[int, float]]:
    found = []
    for pno, words in enumerate(pages, 1):
        for xmin, ymin, xmax, ymax, t in words:
            if t == "Answer" and xmin < 80:
                found.append((pno, ymin))
    if len(found) != 90:
        raise SystemExit(f"Expected 90 Answer markers, got {len(found)}")
    return found


def validate_answer(n: int, slices, pages) -> dict:
    letters = set()
    qnums = set()
    has_answer = False
    for p, y0, y1 in slices:
        for xmin, ymin, xmax, ymax, t in pages[p - 1]:
            if ymin < y1 and ymax > y0:
                if t == "Answer":
                    has_answer = True
                if t in "ABCD" and xmin < 120:
                    letters.add(t)
                if xmin < 60 and re.fullmatch(r"\d+\.", t):
                    qn = int(t[:-1])
                    if 1 <= qn <= 90:
                        qnums.add(qn)
    extra = sorted(q for q in qnums if q != n)
    return {
        "n": n,
        "pages": [s[0] for s in slices],
        "slices": [(p, round(a, 1), round(b, 1)) for p, a, b in slices],
        "has_answer": has_answer,
        "letters": "".join(L for L in "ABCD" if L in letters),
        "extra_questions": extra,
        "ok": has_answer and extra == [],
    }


def crop_all(force: bool = False) -> list[dict]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    xml = pdf_bbox_xml(S_PDF)
    pages = parse_pages(xml)
    questions = question_starts(pages)
    answers = answer_starts(pages)
    render_hires()
    page_imgs = {}
    reports = []
    n_pages = len(pages)

    q_by_n = {n: (p, y) for n, p, y in questions}

    for i, (ap, ay) in enumerate(answers):
        n = i + 1
        dest = FIG_DIR / f"a{n:02d}.png"
        if n < 90:
            p1, y1 = q_by_n[n + 1]
        else:
            p1 = n_pages
            last_words = pages[p1 - 1]
            content_ys = [w[3] for w in last_words if w[1] < FOOTER_Y and w[0] < 560]
            y1 = min(FOOTER_Y, max(content_ys) + 18) if content_ys else FOOTER_Y

        slices = slices_for(n, ap, ay, p1, y1, n_pages)
        report = validate_answer(n, slices, pages)
        report["file"] = dest.name

        if dest.exists() and not force and dest.stat().st_size > 4000 and report["ok"]:
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
    print(f"answer crops {len(reports)}  bad {len(bad)}")
    if bad:
        print("bad", [(r["n"], r.get("extra_questions"), r.get("has_answer")) for r in bad[:12]])
    return reports


if __name__ == "__main__":
    crop_all(force=True)
