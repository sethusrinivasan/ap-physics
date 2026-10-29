#!/usr/bin/env python3
"""AP Physics C Walkthrough Builder - Master Pipeline Orchestrator

Single-command entry point that runs all 6 stages:
1. crop_pdf.py       - High-DPI page rendering and question/answer slicing
2. parse_pdf.py      - Text, choices, correct keys, and rationale extraction
3. generate_specs.py - 7-step pedagogical specification synthesis
4. build_site.py     - HTML player pages, SVG QR codes, Unit TOC, sitemap update
5. generate_audio.py - Narration text chunking, TTS synthesis, manifest writing
6. verify_unit.py    - Comprehensive asset, KaTeX, navigation, and regression verification
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[2]


def check_dependencies() -> None:
    """Validate that all required system binaries and Python libraries are installed."""
    missing_bins = [b for b in ("pdftoppm", "pdftotext") if shutil.which(b) is None]
    missing_pkgs = []
    for pkg in ("PIL", "qrcode"):
        try:
            __import__(pkg)
        except ImportError:
            missing_pkgs.append(pkg)

    if missing_bins or missing_pkgs:
        print("\n❌ MISSING DEPENDENCIES FOR ap-physics-walkthrough:")
        if missing_bins:
            print(f"  • Missing system binaries: {', '.join(missing_bins)}")
            print("    👉 On Debian/Ubuntu: sudo apt-get install -y poppler-utils")
            print("    👉 On macOS:        brew install poppler")
        if missing_pkgs:
            print(f"  • Missing Python packages: {', '.join(missing_pkgs)}")
            print("    👉 Run: pip install -r requirements.txt")
        print("\n💡 Run the automated setup script to install everything:")
        print("    ./setup.sh")
        print("  or:")
        print("    ./skills/ap-physics-walkthrough/scripts/install_deps.sh\n")
        sys.exit(1)


def run_stage(stage_num: int, name: str, cmd: list[str]) -> None:
    """Execute a single pipeline stage with timing and status output."""
    print(f"\n{'='*70}")
    print(f"▶ STAGE {stage_num}: {name.upper()}")
    print(f"{'='*70}")
    start = time.time()
    try:
        subprocess.run(cmd, check=True)
        elapsed = time.time() - start
        print(f"✔ Stage {stage_num} completed in {elapsed:.2f}s")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR in Stage {stage_num} ({name}): Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build complete AP Physics C walkthrough unit from Question and Answer PDFs"
    )
    parser.add_argument("--unit", required=True, type=str, help="Unit identifier (e.g., 4 or '4_Test')")
    parser.add_argument("--title", required=True, type=str, help="Unit Title (e.g., 'Linear Momentum')")
    parser.add_argument("--questions", required=True, type=Path, help="Path to Question PDF")
    parser.add_argument("--answers", required=True, type=Path, help="Path to Answers/Solutions PDF")
    parser.add_argument("--dpi", type=int, default=250, help="Crop render resolution (default: 250 DPI)")
    parser.add_argument("--skip-audio", action="store_true", help="Skip audio synthesis for rapid preview")
    parser.add_argument("--limit-audio", type=int, default=None, help="Limit number of audio problems generated (for testing)")
    parser.add_argument("--overwrite-audio", action="store_true", help="Overwrite existing audio MP3 files")
    parser.add_argument("--no-root-update", action="store_true", help="Skip updating root index.html and sitemap.xml")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Path to repository root")
    args = parser.parse_args()
    check_dependencies()

    repo = args.repo_root.resolve()
    u_val = str(args.unit).strip()
    unit_slug = u_val.lower() if u_val.lower().startswith("unit") else f"unit{u_val.lower()}"
    unit_dir = repo / unit_slug
    unit_dir.mkdir(parents=True, exist_ok=True)
    
    parsed_json = repo / "tools" / f"{unit_slug}_parsed.json"
    specs_py = repo / "tools" / f"{unit_slug}_specs.py"
    
    print(f"\n🚀 STARTING AP PHYSICS C UNIT {args.unit} WALKTHROUGH BUILD")
    print(f"Title:     {args.title}")
    print(f"Questions: {args.questions}")
    print(f"Answers:   {args.answers}")
    print(f"Output:    {unit_dir}")
    
    # Stage 1: Crop PDFs
    crop_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "crop_pdf.py"),
        "--questions", str(args.questions),
        "--answers", str(args.answers),
        "--out", str(unit_dir),
        "--dpi", str(args.dpi)
    ]
    run_stage(1, "High-DPI Visual PDF Cropping", crop_cmd)

    # Stage 2: Parse text and answers
    parse_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "parse_pdf.py"),
        "--questions", str(args.questions),
        "--answers", str(args.answers),
        "--out", str(parsed_json)
    ]
    run_stage(2, "Multimodal Text & Solution Parsing", parse_cmd)

    # Stage 3: Synthesize pedagogical specs if not existing
    if not specs_py.exists():
        spec_cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "generate_specs.py"),
            "--parsed", str(parsed_json),
            "--out", str(specs_py)
        ]
        run_stage(3, "Pedagogical Specification Synthesis", spec_cmd)
    else:
        print(f"\nℹ Stage 3: Found existing audited specifications at {specs_py.name}, using as source.")

    # Stage 4: Build HTML walkthrough pages, QR codes, TOC, and sitemap
    build_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "build_site.py"),
        "--repo-root", str(repo),
        "--unit", str(args.unit),
        "--title", args.title,
        "--specs", str(specs_py),
        "--parsed", str(parsed_json)
    ]
    if args.no_root_update:
        build_cmd.append("--no-root-update")
    run_stage(4, "Player, QR Code & Navigation Builder", build_cmd)

    # Stage 5: Audio narration synthesis
    if not args.skip_audio:
        audio_cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "generate_audio.py"),
            "--unit-dir", str(unit_dir)
        ]
        if args.overwrite_audio:
            audio_cmd.append("--overwrite")
        if args.limit_audio is not None and args.limit_audio > 0:
            audio_cmd.extend(["--limit", str(args.limit_audio)])
        run_stage(5, "Narration Audio Synthesis", audio_cmd)
    else:
        print("\n⏩ Stage 5 skipped (--skip-audio requested).")

    # Stage 6: Comprehensive verification and regression testing
    verify_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "verify_unit.py"),
        "--repo-root", str(repo),
        "--unit", str(args.unit)
    ]
    if args.skip_audio or (args.limit_audio is not None and args.limit_audio > 0):
        verify_cmd.append("--allow-partial-audio")
    if args.no_root_update:
        verify_cmd.append("--no-root-update")
    run_stage(6, "Comprehensive Verification & Regression Suite", verify_cmd)

    print(f"\n{'='*70}")
    print(f"🎉 UNIT {args.unit} BUILD & VERIFICATION FULLY COMPLETE!")
    print(f"Walkthroughs ready at: file://{unit_dir}/index.html")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
