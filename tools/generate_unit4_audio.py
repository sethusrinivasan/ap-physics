#!/usr/bin/env python3
"""Generate English narration audio files and manifest.json for all Unit 4 walkthroughs."""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/home/home/github/ap-physics")
UNIT4 = ROOT / "unit4"


def load_steps(html_path: Path) -> list[dict]:
    html = html_path.read_text()
    start = html.find("const STEPS = ")
    end = html.find("\n    const $ = (id)", start)
    if start < 0 or end < 0:
        raise ValueError(f"Could not find STEPS in {html_path}")
    json_str = html[start + len("const STEPS = ") : end].strip().rstrip(";")
    return json.loads(json_str)


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


def chunks(text: str, max_chars: int = 140) -> list[str]:
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


def google_tts(text: str, attempt: int = 1) -> bytes:
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=en-US&q={urllib.parse.quote(text)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "audio/mpeg,audio/webm,audio/*;q=0.9,*/*;q=0.8",
            "Referer": "https://translate.google.com/",
        },
    )
    for a in range(attempt, 6):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = resp.read()
                if len(data) >= 400:
                    return data
        except Exception:
            time.sleep(0.4 * a)
    raise RuntimeError(f"TTS failed for: {text[:60]}")


def generate_step_audio(audio_dir: Path, step_idx: int, step: dict, overwrite: bool = False) -> dict:
    step_num = step_idx + 1
    file_name = f"step-{step_num:02d}.mp3"
    dest = audio_dir / file_name
    
    text = step_speech(step)
    word_count = len(text.split())
    
    if not overwrite and dest.exists() and dest.stat().st_size > 2000:
        return {"file": file_name, "title": step["title"], "words": word_count}
    
    text_chunks = chunks(text)
    buffers = []
    for piece in text_chunks:
        buf = google_tts(piece)
        buffers.append(buf)
        time.sleep(0.08)  # slight pause between sub-chunk requests
    
    combined = b"".join(buffers)
    dest.write_bytes(combined)
    return {"file": file_name, "title": step["title"], "words": word_count}


def process_question(n: int, overwrite: bool = False) -> str:
    q_dir = UNIT4 / f"q{n}"
    html_path = q_dir / "index.html"
    if not html_path.exists():
        return f"Q{n}: missing index.html"
    
    audio_dir = q_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = audio_dir / "manifest.json"
    
    steps = load_steps(html_path)
    
    # Check if all steps already generated
    if not overwrite:
        all_exist = manifest_path.exists() and all(
            (audio_dir / f"step-{i+1:02d}.mp3").exists() and (audio_dir / f"step-{i+1:02d}.mp3").stat().st_size > 2000
            for i in range(len(steps))
        )
        if all_exist:
            return f"Q{n}: already complete"
    
    manifest = []
    for i, step in enumerate(steps):
        info = generate_step_audio(audio_dir, i, step, overwrite=overwrite)
        manifest.append(info)
        
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return f"Q{n}: generated {len(manifest)} audio steps"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing audio files")
    parser.add_argument("--questions", nargs="*", type=int, help="Specific question numbers to process")
    args = parser.parse_args()
    
    target_questions = args.questions if args.questions else list(range(1, 37))
    print(f"Starting Unit 4 audio generation across {len(target_questions)} problems (overwrite={args.overwrite})...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_question, n, args.overwrite): n for n in target_questions}
        for future in as_completed(futures):
            res = future.result()
            print(res)
    print("All Unit 4 audio processing finished.")


if __name__ == "__main__":
    main()
