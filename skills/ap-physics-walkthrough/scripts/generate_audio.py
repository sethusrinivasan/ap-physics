#!/usr/bin/env python3
"""Stage 5: Narration Audio Synthesizer

Extracts speech narration text from step definitions, chunks text for natural pacing,
synthesizes MP3 audio files using Google TTS, and writes manifest.json.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def load_steps(html_path: Path) -> list[dict]:
    """Parse the STEPS array embedded in the walkthrough page."""
    html = html_path.read_text()
    start = html.find("const STEPS = ")
    end = html.find("\n    const $ = (id)", start)
    if start < 0 or end < 0:
        raise ValueError(f"Could not find STEPS in {html_path}")
    json_str = html[start + len("const STEPS = ") : end].strip().rstrip(";")
    return json.loads(json_str)


def step_speech(step: dict) -> str:
    """Compose natural English narration for a single step."""
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


def chunk_text(text: str, max_chars: int = 140) -> list[str]:
    """Split text into sentence-level chunks suitable for TTS synthesis."""
    text = re.sub(r"[’‘]", "'", str(text))
    text = re.sub(r"[“”]", '"', text)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    cur = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) > max_chars:
            if cur:
                chunks.append(cur)
                cur = ""
            for w in s.split():
                nxt = f"{cur} {w}".strip()
                if len(nxt) > max_chars and cur:
                    chunks.append(cur)
                    cur = w
                else:
                    cur = nxt
            continue
        nxt = f"{cur} {s}".strip() if cur else s
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    return chunks


def fetch_tts(text: str, max_retries: int = 5) -> bytes:
    """Fetch audio bytes from Google TTS API with exponential backoff."""
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=en-US&q={urllib.parse.quote(text)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://translate.google.com/",
        },
    )
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = resp.read()
                if len(data) >= 400:
                    return data
        except Exception:
            time.sleep(0.3 * attempt)
    raise RuntimeError(f"TTS fetch failed for chunk: {text[:60]}")


def generate_step_audio(audio_dir: Path, step_idx: int, step: dict, overwrite: bool = False) -> dict:
    """Generate audio MP3 for a single step."""
    step_num = step_idx + 1
    file_name = f"step-{step_num:02d}.mp3"
    dest = audio_dir / file_name
    
    text = step_speech(step)
    word_count = len(text.split())
    
    if not overwrite and dest.exists() and dest.stat().st_size > 2000:
        return {"file": file_name, "title": step["title"], "words": word_count}
    
    chunks = chunk_text(text)
    buffers = [fetch_tts(c) for c in chunks]
    combined = b"".join(buffers)
    dest.write_bytes(combined)
    return {"file": file_name, "title": step["title"], "words": word_count}


def process_question_audio(q_dir: Path, overwrite: bool = False) -> str:
    """Process audio for all steps of a single question."""
    html_path = q_dir / "index.html"
    if not html_path.exists():
        return f"{q_dir.name}: missing index.html"
        
    audio_dir = q_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = audio_dir / "manifest.json"
    
    steps = load_steps(html_path)
    
    if not overwrite and manifest_path.exists():
        all_exist = all(
            (audio_dir / f"step-{i+1:02d}.mp3").exists() and (audio_dir / f"step-{i+1:02d}.mp3").stat().st_size > 2000
            for i in range(len(steps))
        )
        if all_exist:
            return f"{q_dir.name}: audio already complete"
            
    manifest = []
    for i, step in enumerate(steps):
        info = generate_step_audio(audio_dir, i, step, overwrite=overwrite)
        manifest.append(info)
        
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return f"{q_dir.name}: generated {len(manifest)} audio steps"


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize narration audio for a unit")
    parser.add_argument("--unit-dir", required=True, type=Path, help="Path to unit directory (e.g. unit4/)")
    parser.add_argument("--overwrite", action="store_true", help="Force overwrite of existing audio files")
    parser.add_argument("--limit", type=int, default=None, help="Process at most N problems (default: all)")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent worker threads (default: 4)")
    args = parser.parse_args()
    
    q_dirs = sorted([d for d in args.unit_dir.glob("q*") if d.is_dir()], key=lambda p: int(p.name[1:]))
    if args.limit is not None and args.limit > 0:
        q_dirs = q_dirs[:args.limit]
    print(f"Synthesizing audio across {len(q_dirs)} problems (overwrite={args.overwrite})...")
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_question_audio, q, args.overwrite): q for q in q_dirs}
        for future in as_completed(futures):
            res = future.result()
            print(res)
            
    print("All unit narration audio generation finished.")


if __name__ == "__main__":
    main()
