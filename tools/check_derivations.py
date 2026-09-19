#!/usr/bin/env python3
"""Flag walkthroughs that never substitute given values (the Q7 failure mode)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path("/home/home/ap-physics")
KEEP = {1, 2, 4, 5, 7}
GENERIC_APPLY = "Keep that same law while the numbers from the figure are substituted."
HOLEY = re.compile(
    r"(\bis\s+\.\s|to be and |the -axis|located at d|where and |of the sphere to be)",
    re.I,
)


def load_steps(html: str):
    start = html.index("const STEPS = ")
    end = html.index("\n    const $ = (id)", start)
    raw = html[start + len("const STEPS = ") : end].strip().rstrip(";")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_unquoted": True, "_raw": raw}


def explains(steps) -> list[str]:
    out = []
    for step in steps:
        for block in step.get("blocks") or []:
            if block.get("explain"):
                out.append(block["explain"])
            if block.get("speakFormula"):
                out.append(block["speakFormula"])
    return out


def main() -> None:
    empty_first = []
    generic = []
    holey = []
    repeated_tex = []
    ok = []
    for n in range(1, 91):
        html = (ROOT / f"unit2-q{n}" / "index.html").read_text()
        steps = load_steps(html)
        if isinstance(steps, dict) and steps.get("_unquoted"):
            raw = steps["_raw"]
            if GENERIC_APPLY in raw:
                generic.append(n)
            if HOLEY.search(raw):
                holey.append(n)
            if '"blocks": []' in raw or '"blocks":[]' in raw:
                empty_first.append(n)
            ok.append(n) if n in KEEP else None
            continue
        first = steps[0] if steps else {}
        if not (first.get("blocks") or []):
            empty_first.append(n)
        texts = []
        for step in steps:
            for block in step.get("blocks") or []:
                if block.get("tex"):
                    texts.append(block["tex"])
        blob = " ".join(explains(steps))
        if GENERIC_APPLY in blob:
            generic.append(n)
        if HOLEY.search(blob):
            holey.append(n)
        if texts and texts.count(texts[0]) >= 3:
            repeated_tex.append(n)
        if n not in empty_first and n not in generic and n not in holey and n not in repeated_tex:
            ok.append(n)
    print("empty_first", len(empty_first), empty_first)
    print("generic_apply_speech", len(generic), generic)
    print("holey_explain", len(holey), holey)
    print("same_tex_x3", len(repeated_tex), repeated_tex)
    bad = sorted(set(empty_first + generic + holey + repeated_tex) - KEEP)
    print("still_broken_generated", len(bad), bad)
    print("looks_ok", ok)


if __name__ == "__main__":
    main()
