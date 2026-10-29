#!/usr/bin/env python3
"""Stage 1: High-DPI Visual PDF Cropper

Renders PDF pages to high-resolution PNGs and slices individual question and
answer bounding boxes to produce q01.png..qN.png and a01.png..aN.png.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from PIL import Image


def render_pdf_to_pages(pdf_path: Path, output_dir: Path, dpi: int = 250) -> list[Path]:
    """Render each page of a PDF file to a PNG image using pdftoppm."""
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = str(output_dir / "page")
    cmd = ["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), prefix]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    return sorted(output_dir.glob("page-*.png"))


def get_text_layout(pdf_path: Path) -> list[str]:
    """Extract layout-preserved text page by page using pdftotext."""
    cmd = ["pdftotext", "-layout", str(pdf_path), "-"]
    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
    # Form feed (\x0c) separates pages in pdftotext output
    return res.stdout.split("\x0c")


def crop_questions(page_images: list[Path], pages_text: list[str], output_dir: Path) -> list[dict]:
    """Slice question bounding boxes from high-resolution page renders."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = []
    
    # Locate question number anchors across pages
    q_pattern = re.compile(r"^\s*([0-9]{1,2})\.\s+", re.MULTILINE)
    
    for page_idx, (img_path, page_str) in enumerate(zip(page_images, pages_text)):
        matches = list(q_pattern.finditer(page_str))
        if not matches:
            continue
            
        lines = page_str.splitlines()
        total_lines = max(len(lines), 1)
        
        with Image.open(img_path) as img:
            w, h = img.size
            
            for i, match in enumerate(matches):
                q_num = int(match.group(1))
                char_idx = match.start()
                line_idx = page_str[:char_idx].count("\n")
                
                # Approximate vertical coordinates from line index
                y_top = int((line_idx / total_lines) * h) - 20
                y_top = max(0, y_top)
                
                # Bottom boundary is next question on same page or near bottom
                if i + 1 < len(matches):
                    next_char = matches[i + 1].start()
                    next_line = page_str[:next_char].count("\n")
                    y_bottom = int((next_line / total_lines) * h) - 10
                else:
                    y_bottom = int(h * 0.94)
                
                # Ensure minimum height
                y_bottom = max(y_top + 100, min(h, y_bottom))
                
                crop_box = (int(w * 0.04), y_top, int(w * 0.96), y_bottom)
                cropped = img.crop(crop_box)
                
                dest_file = output_dir / f"q{q_num:02d}.png"
                cropped.save(dest_file, "PNG", optimize=True)
                
                report.append({
                    "n": q_num,
                    "file": dest_file.name,
                    "page": page_idx + 1,
                    "box": crop_box,
                    "size": [cropped.width, cropped.height]
                })
                
    return sorted(report, key=lambda x: x["n"])


def crop_answers(page_images: list[Path], pages_text: list[str], output_dir: Path) -> list[dict]:
    """Slice answer and solution explanation crops from high-resolution page renders."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = []
    
    # Locate answer headers (e.g., 'Answer A', 'Answer B')
    ans_pattern = re.compile(r"^\s*Answer\s+([A-D])", re.MULTILINE)
    q_counter = 1
    
    for page_idx, (img_path, page_str) in enumerate(zip(page_images, pages_text)):
        matches = list(ans_pattern.finditer(page_str))
        if not matches:
            continue
            
        lines = page_str.splitlines()
        total_lines = max(len(lines), 1)
        
        with Image.open(img_path) as img:
            w, h = img.size
            
            for i, match in enumerate(matches):
                ans_letter = match.group(1)
                char_idx = match.start()
                line_idx = page_str[:char_idx].count("\n")
                
                y_top = int((line_idx / total_lines) * h) - 20
                y_top = max(0, y_top)
                
                if i + 1 < len(matches):
                    next_char = matches[i + 1].start()
                    next_line = page_str[:next_char].count("\n")
                    y_bottom = int((next_line / total_lines) * h) - 10
                else:
                    y_bottom = int(h * 0.92)
                
                y_bottom = max(y_top + 80, min(h, y_bottom))
                
                crop_box = (int(w * 0.04), y_top, int(w * 0.96), y_bottom)
                cropped = img.crop(crop_box)
                
                dest_file = output_dir / f"a{q_counter:02d}.png"
                cropped.save(dest_file, "PNG", optimize=True)
                
                report.append({
                    "n": q_counter,
                    "answer": ans_letter,
                    "file": dest_file.name,
                    "page": page_idx + 1,
                    "box": crop_box,
                    "size": [cropped.width, cropped.height]
                })
                q_counter += 1
                
    return sorted(report, key=lambda x: x["n"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Render and crop PDF questions and answers")
    parser.add_argument("--questions", required=True, type=Path, help="Path to Questions PDF")
    parser.add_argument("--answers", required=True, type=Path, help="Path to Answers PDF")
    parser.add_argument("--out", required=True, type=Path, help="Output unit directory (e.g. unit4/)")
    parser.add_argument("--dpi", type=int, default=250, help="Rendering resolution (default: 250 DPI)")
    args = parser.parse_args()
    
    figures_dir = args.out / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Render and crop questions
    q_hires = figures_dir / "hires"
    print(f"Rendering questions PDF at {args.dpi} DPI...")
    q_pages = render_pdf_to_pages(args.questions, q_hires, dpi=args.dpi)
    q_text = get_text_layout(args.questions)
    print("Slicing question figures...")
    q_report = crop_questions(q_pages, q_text, figures_dir)
    (figures_dir / "crop-report.json").write_text(json.dumps(q_report, indent=2))
    print(f"Cropped {len(q_report)} questions.")
    
    # 2. Render and crop answers
    a_hires = figures_dir / "sol-hires"
    print(f"Rendering answers PDF at {args.dpi} DPI...")
    a_pages = render_pdf_to_pages(args.answers, a_hires, dpi=args.dpi)
    a_text = get_text_layout(args.answers)
    print("Slicing answer figures...")
    a_report = crop_answers(a_pages, a_text, figures_dir)
    (figures_dir / "answer-crop-report.json").write_text(json.dumps(a_report, indent=2))
    print(f"Cropped {len(a_report)} solutions.")


if __name__ == "__main__":
    main()
