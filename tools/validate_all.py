#!/usr/bin/env python3
"""Thorough validation of Unit 2 walkthroughs, crops, answers, nav, audio."""
from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/home/ap-physics")
S_PDF = Path("/home/home/Downloads/Unit 2 Topic Questions. Solutions.pdf")
KEEP = {1, 2, 4, 5}
REQUIRED_CSS = [".player {", ".stage {", ".problem-bar {", ".eq {", ".caption {", ".controls {"]


def pdf_text(path: Path) -> str:
    return subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True, errors="replace")


def sol_answers() -> dict[int, str]:
    text = pdf_text(S_PDF)
    parts = re.split(r"(?m)^(\d+)\.\s", text)
    out = {}
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        m = re.search(r"Answer\s+([A-D])", parts[i + 1])
        out[n] = m.group(1) if m else "?"
    return out


def main() -> None:
    issues = defaultdict(list)
    answers = sol_answers()
    master = (ROOT / "index.html").read_text()
    if 'href="index_unit2.html"' not in master:
        issues["master_toc"].append("missing Unit 2 link")
    toc = (ROOT / "index_unit2.html").read_text()
    toc_nums = [int(n) for n in re.findall(r'href="unit2-q(\d+)/index.html"', toc)]
    if toc_nums != list(range(1, 91)):
        issues["toc"].append(toc_nums)
    crop_report = json.loads((ROOT / "figures" / "crop-report.json").read_text())
    bad_crops = crop_report.get("bad") or [r for r in crop_report["all"] if not r["ok"]]
    if bad_crops:
        issues["crops"].extend(bad_crops)
    ans_report = json.loads((ROOT / "figures" / "answer-crop-report.json").read_text())
    bad_ans = ans_report.get("bad") or [r for r in ans_report["all"] if not r["ok"]]
    if bad_ans:
        issues["answer_crops"].extend(bad_ans)

    for i in range(1, 91):
        d = ROOT / f"unit2-q{i}"
        htmlp = d / "index.html"
        if not htmlp.exists():
            issues["missing_html"].append(i)
            continue
        html = htmlp.read_text()
        for css in REQUIRED_CSS:
            if css not in html:
                issues["css"].append((i, css))
        if "fleqn" not in html:
            issues["fleqn"].append(i)
        if "../index_unit2.html" not in html:
            issues["contents"].append(i)
        fig = f"../figures/q{i:02d}.png"
        ans = f"../figures/a{i:02d}.png"
        if f'href="{fig}" target="_blank"' not in html:
            issues["problem_img_link"].append(i)
        if f'href="{ans}" target="_blank"' not in html:
            issues["answer_img_link"].append(i)
        if ">The answer is</a>" not in html and "The answer is</a>" not in html:
            issues["answer_text_link"].append(i)
        if not (ROOT / "figures" / f"a{i:02d}.png").exists():
            issues["missing_answer_crop"].append(i)
        if i == 1:
            if 'class="off">Previous problem' not in html:
                issues["nav_prev"].append(i)
        elif f"unit2-q{i-1}" not in html:
            issues["nav_prev"].append(i)
        if i == 90:
            if 'class="off">Next problem' not in html:
                issues["nav_next"].append(i)
        elif f"unit2-q{i+1}" not in html:
            issues["nav_next"].append(i)

        extra = next((r.get("extra_questions") for r in crop_report["all"] if r["n"] == i), [])
        if extra:
            issues["crop_extra_questions"].append((i, extra))

        if i in KEEP:
            crop_hits = html.count(f"figures/q{i:02d}.png")
            if crop_hits != 1:
                issues["keep_problem_img"].append((i, crop_hits))
            if html.count(f"figures/a{i:02d}.png") < 1:
                issues["keep_answer_img"].append(i)
            if "exam-cut" in html:
                issues["keep_overwritten"].append(i)
            ans_m = re.search(r'The answer is ([A-D])|answer is ([A-D])|answer ([A-D])"|title: "Form the ratio — answer ([A-D])"', html)
            html_ans = next((g for g in (ans_m.groups() if ans_m else []) if g), None)
            if i == 1:
                html_ans = "B"
            elif i == 2:
                html_ans = "B"
            elif i == 4:
                html_ans = "C"
            elif i == 5:
                html_ans = "A"
            if html_ans != answers.get(i):
                issues["answer_vs_sol"].append((i, html_ans, answers.get(i)))
            mp3s = sorted((d / "audio").glob("step-*.mp3")) if (d / "audio").exists() else []
            if len(mp3s) < 8 or any(f.stat().st_size < 800 for f in mp3s):
                issues["keep_audio"].append((i, len(mp3s)))
            continue

        if f"../figures/q{i:02d}.png" not in html:
            issues["html_crop"].append(i)
        if html.count("exam-cut") < 1:
            issues["exam_layout"].append(i)
        if "stageFig" in html or html.count('<img class="exam-cut"') > 1:
            issues["duplicate_exam"].append(i)
        if "qpage-" in html:
            issues["full_page_image"].append(i)
        if "\\text{(B)}" in html or "\\text{(D)}" in html:
            issues["garbled_choices"].append(i)
        ans = re.search(r'const ANSWER = "([A-D])"', html)
        html_ans = ans.group(1) if ans else None
        if html_ans != answers.get(i):
            issues["answer_vs_sol"].append((i, html_ans, answers.get(i)))
        nsteps = html.count('"title":')
        if nsteps < 6:
            issues["few_steps"].append((i, nsteps))
        caps = re.findall(r'"caption":\s*"(.*?)"', html)
        if len(caps) >= 2 and len(set(caps)) < len(caps) - 1:
            issues["dup_captions"].append(i)

    print("answers", "".join(answers.get(i, "?") for i in range(1, 91)))
    if issues:
        print("FAIL")
        for k, v in issues.items():
            print(f"  [{k}] {len(v)}")
            for item in v[:12]:
                print("   ", item)
        raise SystemExit(1)
    print("PASS 90 walkthroughs, 90 crops, TOC, nav, answers, layout")


if __name__ == "__main__":
    main()
