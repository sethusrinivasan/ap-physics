#!/usr/bin/env python3
"""Stage 2: Multimodal Text & Solution Parser

Extracts question stems, multiple choice options (A, B, C, D), correct answers,
and solution rationale into a normalized JSON structure.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def parse_questions_text(text: str) -> dict[int, dict]:
    """Parse question blocks from raw text."""
    # Split text by question number markers: '1. ', '2. ', etc.
    q_splits = re.split(r"\n(?=\s*\d{1,2}\.\s+)", text)
    questions = {}
    
    for block in q_splits:
        m = re.match(r"^\s*(\d{1,2})\.\s+(.*)", block, re.DOTALL)
        if not m:
            continue
        n = int(m.group(1))
        content = m.group(2).strip()
        
        # Extract choices (A), (B), (C), (D)
        choice_matches = list(re.finditer(r"\(([A-D])\)\s+([^\n]+(?:\n(?!\([A-D]\)).*)*)", content))
        choices = {}
        stem = content
        
        if choice_matches:
            stem = content[:choice_matches[0].start()].strip()
            for cm in choice_matches:
                letter = cm.group(1)
                choice_text = re.sub(r"\s+", " ", cm.group(2).strip())
                choices[letter] = choice_text
                
        stem_clean = re.sub(r"\s+", " ", stem)
        questions[n] = {
            "n": n,
            "stem": stem_clean,
            "choices": choices
        }
        
    return questions


def parse_answers_text(text: str) -> dict[int, dict]:
    """Parse official solution blocks and answer letters."""
    # Split by 'Answer [A-D]' markers
    splits = re.split(r"\n(?=\s*Answer\s+[A-D])", text)
    answers = {}
    counter = 1
    
    for block in splits:
        m = re.match(r"^\s*Answer\s+([A-D])\s+(.*)", block, re.DOTALL)
        if not m:
            continue
        ans_letter = m.group(1)
        body = m.group(2).strip()
        
        # Clean whitespace and extract rationale
        body_clean = re.sub(r"\s+", " ", body)
        answers[counter] = {
            "n": counter,
            "answer": ans_letter,
            "rationale": body_clean
        }
        counter += 1
        
    return answers


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse question and answer text into JSON")
    parser.add_argument("--questions", required=True, type=Path, help="Questions PDF")
    parser.add_argument("--answers", required=True, type=Path, help="Answers PDF")
    parser.add_argument("--out", required=True, type=Path, help="Output JSON path")
    args = parser.parse_args()
    
    # Extract text using pdftotext
    q_res = subprocess.run(["pdftotext", str(args.questions), "-"], capture_output=True, text=True, check=True)
    a_res = subprocess.run(["pdftotext", str(args.answers), "-"], capture_output=True, text=True, check=True)
    
    q_data = parse_questions_text(q_res.stdout)
    a_data = parse_answers_text(a_res.stdout)
    
    # Merge questions and answers
    combined = []
    total = max(max(q_data.keys(), default=0), max(a_data.keys(), default=0))
    for n in range(1, total + 1):
        q = q_data.get(n, {"n": n, "stem": f"Question {n}", "choices": {}})
        a = a_data.get(n, {"n": n, "answer": "A", "rationale": ""})
        combined.append({
            "n": n,
            "stem": q["stem"],
            "choices": q["choices"],
            "answer": a["answer"],
            "rationale": a["rationale"]
        })
        
    args.out.write_text(json.dumps(combined, indent=2))
    print(f"Parsed {len(combined)} questions to {args.out}")


if __name__ == "__main__":
    main()
