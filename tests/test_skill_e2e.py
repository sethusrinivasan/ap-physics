#!/usr/bin/env python3
"""End-to-end test for the ap-physics-walkthrough agent skill.

Takes Unit 4 PDFs as input and runs the full 6-stage pipeline under 'Unit4_Test':
1. Visual cropping of question and answer figures
2. Text & rationale parsing
3. Pedagogical specification synthesis
4. Walkthrough player pages, SVG QR codes, and unit TOC generation
5. Narration audio synthesis and manifest creation
6. Automated verification and prior-unit regression assertions
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_SCRIPT = REPO_ROOT / "skills" / "ap-physics-walkthrough" / "scripts" / "run_unit_pipeline.py"
VERIFY_SCRIPT = REPO_ROOT / "skills" / "ap-physics-walkthrough" / "scripts" / "verify_unit.py"

# Unit 4 PDFs (defaults to bundled test inputs fixture, with environment / local download fallbacks)
FIXTURE_QUESTIONS = REPO_ROOT / "tests" / "test_inputs" / "unit4_questions.pdf"
FIXTURE_ANSWERS = REPO_ROOT / "tests" / "test_inputs" / "unit4_solutions.pdf"

QUESTIONS_PDF = Path(os.environ.get(
    "TEST_QUESTIONS_PDF",
    str(FIXTURE_QUESTIONS) if FIXTURE_QUESTIONS.exists() else "/home/home/Downloads/Unit 4 Topic Questions.pdf"
))
ANSWERS_PDF = Path(os.environ.get(
    "TEST_ANSWERS_PDF",
    str(FIXTURE_ANSWERS) if FIXTURE_ANSWERS.exists() else "/home/home/Downloads/Unit 4 Topic Questions. Solutions.pdf"
))

TEST_UNIT_ID = "Unit4_Test"
TEST_UNIT_DIR = REPO_ROOT / "unit4_test"
TEST_PARSED_JSON = REPO_ROOT / "tools" / "unit4_test_parsed.json"
TEST_SPECS_PY = REPO_ROOT / "tools" / "unit4_test_specs.py"


@unittest.skipUnless(
    QUESTIONS_PDF.exists() and ANSWERS_PDF.exists(),
    f"Unit 4 PDFs not found at {QUESTIONS_PDF} and {ANSWERS_PDF}",
)
class AgentSkillE2ETest(unittest.TestCase):
    """End-to-End Test Suite for ap-physics-walkthrough agent skill."""

    @classmethod
    def setUpClass(cls) -> None:
        """Ensure clean state before running E2E pipeline."""
        cls._cleanup()

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up test artifacts after suite completes."""
        cls._cleanup()

    @classmethod
    def _cleanup(cls) -> None:
        """Remove test unit directory and generated tool specs."""
        if TEST_UNIT_DIR.exists():
            shutil.rmtree(TEST_UNIT_DIR, ignore_errors=True)
        if TEST_PARSED_JSON.exists():
            TEST_PARSED_JSON.unlink(missing_ok=True)
        if TEST_SPECS_PY.exists():
            TEST_SPECS_PY.unlink(missing_ok=True)

    def test_01_execute_pipeline_end_to_end(self) -> None:
        """Run the full 6-stage agent skill pipeline with Unit 4 input."""
        cmd = [
            sys.executable,
            str(PIPELINE_SCRIPT),
            "--unit", TEST_UNIT_ID,
            "--title", "Linear Momentum (E2E Test)",
            "--questions", str(QUESTIONS_PDF),
            "--answers", str(ANSWERS_PDF),
            "--dpi", "150",
            "--limit-audio", "2",
            "--no-root-update",
            "--repo-root", str(REPO_ROOT),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(
            res.returncode,
            0,
            f"run_unit_pipeline.py failed with returncode {res.returncode}:\n{res.stdout}\n{res.stderr}",
        )
        self.assertIn("UNIT Unit4_Test BUILD & VERIFICATION FULLY COMPLETE", res.stdout)

    def test_02_validate_cropped_figures(self) -> None:
        """Assert that high-DPI crops for questions and answers were generated."""
        figures_dir = TEST_UNIT_DIR / "figures"
        self.assertTrue(figures_dir.is_dir(), "figures directory missing")

        # Questions Q1..Q36
        q_crops = list(figures_dir.glob("q*.png"))
        self.assertGreaterEqual(len(q_crops), 36, f"Expected >= 36 question crops, found {len(q_crops)}")
        for q in q_crops:
            self.assertGreater(q.stat().st_size, 1000, f"Crop {q.name} is too small (<1KB)")

        # Answers A1..A36
        a_crops = list(figures_dir.glob("a*.png"))
        self.assertGreaterEqual(len(a_crops), 36, f"Expected >= 36 answer crops, found {len(a_crops)}")
        for a in a_crops:
            self.assertGreater(a.stat().st_size, 1000, f"Crop {a.name} is too small (<1KB)")

    def test_03_validate_parsed_data_and_specs(self) -> None:
        """Assert parsed JSON and generated Python specs are valid and complete."""
        self.assertTrue(TEST_PARSED_JSON.exists(), "unit4_test_parsed.json was not created")
        parsed_data = json.loads(TEST_PARSED_JSON.read_text())
        self.assertEqual(len(parsed_data), 36, f"Expected 36 parsed questions, got {len(parsed_data)}")

        self.assertTrue(TEST_SPECS_PY.exists(), "unit4_test_specs.py was not created")
        specs_content = TEST_SPECS_PY.read_text()
        self.assertIn("SPECS = {", specs_content)
        self.assertIn("setup_text", specs_content)
        self.assertIn("law_tex", specs_content)

    def test_04_validate_html_walkthrough_pages(self) -> None:
        """Assert walkthrough HTML pages contain player, KaTeX math, and QR codes."""
        # TOC
        toc_file = TEST_UNIT_DIR / "index.html"
        self.assertTrue(toc_file.exists(), "TOC index.html missing")
        toc_html = toc_file.read_text()
        self.assertIn("Linear Momentum (E2E Test)", toc_html)
        self.assertIn("Question 1</td>", toc_html)
        self.assertIn("Question 36</td>", toc_html)
        self.assertIn("<table>", toc_html)
        self.assertIn("Open walkthrough</a>", toc_html)
        self.assertIn('class="page-qr"', toc_html)

        # Unit QR code
        self.assertTrue((TEST_UNIT_DIR / "qr.svg").exists(), "Unit qr.svg missing")

        # Problem pages
        for n in range(1, 37):
            q_page = TEST_UNIT_DIR / f"q{n}" / "index.html"
            self.assertTrue(q_page.exists(), f"Q{n} index.html missing")
            content = q_page.read_text()
            self.assertIn('class="player"', content, f"Q{n} missing player container")
            self.assertIn('class="problem-bar', content, f"Q{n} missing problem bar")
            self.assertIn('const STEPS = [', content, f"Q{n} missing STEPS array")
            self.assertTrue((TEST_UNIT_DIR / f"q{n}" / "qr.svg").exists(), f"Q{n} qr.svg missing")

    def test_05_validate_audio_synthesis_and_manifest(self) -> None:
        """Assert audio MP3s and manifests were synthesized for tested problems."""
        for n in (1, 2):
            audio_dir = TEST_UNIT_DIR / f"q{n}" / "audio"
            manifest_path = audio_dir / "manifest.json"
            self.assertTrue(manifest_path.exists(), f"Q{n} manifest.json missing")
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(len(manifest), 7, f"Q{n} manifest does not have 7 steps")

            for step in range(1, 8):
                mp3 = audio_dir / f"step-{step:02d}.mp3"
                self.assertTrue(mp3.exists(), f"Q{n} step-{step:02d}.mp3 missing")
                self.assertGreater(mp3.stat().st_size, 2000, f"Q{n} step-{step:02d}.mp3 is <2KB")

    def test_06_verify_prior_units_untouched(self) -> None:
        """Verify that production Unit 2 (90 problems) and Unit 4 (36 problems) remain untouched."""
        u2 = REPO_ROOT / "unit2"
        u4 = REPO_ROOT / "unit4"

        self.assertTrue(u2.is_dir() and (u2 / "index.html").exists(), "Unit 2 missing or corrupted")
        self.assertEqual(len([d for d in u2.glob("q*") if d.is_dir()]), 90, "Unit 2 problem count altered")

        self.assertTrue(u4.is_dir() and (u4 / "index.html").exists(), "Unit 4 missing or corrupted")
        self.assertEqual(len([d for d in u4.glob("q*") if d.is_dir()]), 36, "Unit 4 problem count altered")


if __name__ == "__main__":
    unittest.main()
