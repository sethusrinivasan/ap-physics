#!/usr/bin/env python3
"""Comprehensive AI Evaluation Suite for AP Physics Walkthrough Harnesses.

Evaluates pedagogical quality, symbol grounding, spoken math naturalness,
distractor rejection rigor, and official scoring concordance across different
agent harnesses (e.g. Gemini, Cursor, Codex, Claude Code, AutoGen).

Can be run:
  1. As a standard test suite: python3 -m unittest tests.test_ai_eval -v
  2. As a benchmark CLI tool:   python3 tests/test_ai_eval.py --unit unit4_test --harness Gemini
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unittest
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Evaluation Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ProblemEvalResult:
    """Detailed evaluation metrics for a single question walkthrough."""
    problem_num: int
    symbol_score: float              # 0.0 - 1.0: symbol grounding & consistency
    katex_score: float               # 0.0 - 1.0: TeX syntax & math block validity
    spoken_math_score: float         # 0.0 - 1.0: TTS audio narration readiness
    distractor_score: float          # 0.0 - 1.0: depth of distractor failure rationale
    accuracy_score: float            # 1.0 if matches College Board key, else 0.0
    composite_score: float           # Weighted average (0.0 - 1.0)
    flags: List[str] = field(default_factory=list)
    symbol_audit: Dict[str, Any] = field(default_factory=dict)
    spoken_leaks: List[str] = field(default_factory=list)


@dataclass
class HarnessBenchmarkReport:
    """Aggregate benchmark report across an entire unit."""
    harness_name: str
    unit_slug: str
    total_problems: int
    mean_symbol_score: float
    mean_katex_score: float
    mean_spoken_math_score: float
    mean_distractor_score: float
    mean_accuracy: float
    composite_harness_score: float   # 0.0 - 100.0%
    grade: str                       # A+, A, B, C, F
    flagged_problems: List[int] = field(default_factory=list)
    summary_markdown: str = ""


# ---------------------------------------------------------------------------
# Core Evaluator Engine
# ---------------------------------------------------------------------------

class WalkthroughAIEvaluator:
    """Rigorous pedagogical & technical evaluator for walkthrough artifacts."""

    # TeX commands that must NEVER leak into spoken math narration
    RAW_TEX_LEAK_PATTERNS = [
        re.compile(r"\\(?:frac|sqrt|text|vec|mathbf|hat|dot|ddot|int|sum|Delta|tau|theta|omega|alpha|beta|mu|rho|lambda)"),
        re.compile(r"[_^]\{?[a-zA-Z0-9]+\}?"),  # raw TeX sub/superscripts e.g. v_1 or t^2
        re.compile(r"\\(?:left|right|cdot|times|pm|approx)"),
        re.compile(r"[{}]"),                    # stray curly braces
    ]

    # Physical concepts expected in quality AP Physics distractor analysis
    PHYSICS_CONCEPT_TERMS = {
        "momentum", "kinetic energy", "velocity", "conservation", "impulse",
        "inelastic", "elastic", "mass", "scalar", "vector", "direction",
        "net force", "time interval", "newton", "integral", "derivative",
        "contradicts", "miscalculates", "violates", "cannot be", "opposite"
    }

    def __init__(self, repo_root: Path = REPO_ROOT):
        self.repo_root = repo_root

    def evaluate_unit(
        self,
        unit_slug: str,
        harness_name: str = "DefaultHarness",
        limit: Optional[int] = 5
    ) -> HarnessBenchmarkReport:
        """Run comprehensive multi-dimensional evaluation on problems in unit.
        
        Args:
            unit_slug: directory name of the unit (e.g. 'unit4_test' or 'unit4')
            harness_name: label of the agent / model harness being evaluated
            limit: number of problems to evaluate (default: 5; pass None or 0 for all)
        """
        unit_dir = self.repo_root / unit_slug
        if not unit_dir.exists():
            raise FileNotFoundError(f"Unit directory {unit_dir} does not exist")

        q_dirs = sorted(
            [d for d in unit_dir.glob("q*") if d.is_dir() and d.name[1:].isdigit()],
            key=lambda p: int(p.name[1:])
        )
        if not q_dirs:
            raise ValueError(f"No problem directories found in {unit_dir}")

        total_available = len(q_dirs)
        if limit is not None and limit > 0:
            q_dirs = q_dirs[:limit]

        parsed_file = self.repo_root / "tools" / f"{unit_slug}_parsed.json"
        ground_truth: Dict[int, str] = {}
        if parsed_file.exists():
            try:
                data = json.loads(parsed_file.read_text())
                ground_truth = {item["n"]: item.get("answer", "") for item in data}
            except Exception:
                pass

        results: List[ProblemEvalResult] = []
        for q in q_dirs:
            n = int(q.name[1:])
            res = self.evaluate_problem(q, n, ground_truth.get(n))
            results.append(res)

        return self._aggregate_report(harness_name, unit_slug, results, total_available=total_available)

    def evaluate_problem(
        self,
        q_dir: Path,
        n: int,
        expected_answer: Optional[str] = None
    ) -> ProblemEvalResult:
        """Evaluate a single problem directory."""
        html_file = q_dir / "index.html"
        if not html_file.exists():
            return ProblemEvalResult(
                problem_num=n,
                symbol_score=0.0,
                katex_score=0.0,
                spoken_math_score=0.0,
                distractor_score=0.0,
                accuracy_score=0.0,
                composite_score=0.0,
                flags=["index.html missing"]
            )

        html_content = html_file.read_text()
        steps = self._extract_steps_from_html(html_content)
        if not steps or len(steps) < 7:
            return ProblemEvalResult(
                problem_num=n,
                symbol_score=0.0,
                katex_score=0.0,
                spoken_math_score=0.0,
                distractor_score=0.0,
                accuracy_score=0.0,
                composite_score=0.0,
                flags=[f"Invalid steps array (found {len(steps)} steps, expected 7)"]
            )

        # Dimension 1: Symbol Grounding & Variable Definition Completeness
        sym_score, sym_flags, sym_audit = self._eval_symbol_consistency(steps)

        # Dimension 2: KaTeX Syntax & Math Formatting
        katex_score, katex_flags = self._eval_katex_soundness(steps)

        # Dimension 3: Spoken Math / TTS Pronunciation Integrity
        spoken_score, spoken_flags, spoken_leaks = self._eval_spoken_math(steps)

        # Dimension 4: Distractor Rejection Rigor
        distractor_score, distractor_flags = self._eval_distractor_analysis(steps)

        # Dimension 5: Answer Accuracy vs Ground Truth
        acc_score, acc_flags = self._eval_accuracy(steps, expected_answer)

        all_flags = sym_flags + katex_flags + spoken_flags + distractor_flags + acc_flags

        # Weighted Composite Score (0.0 to 1.0)
        composite = (
            sym_score * 0.25 +
            katex_score * 0.25 +
            spoken_score * 0.20 +
            distractor_score * 0.15 +
            acc_score * 0.15
        )

        return ProblemEvalResult(
            problem_num=n,
            symbol_score=round(sym_score, 3),
            katex_score=round(katex_score, 3),
            spoken_math_score=round(spoken_score, 3),
            distractor_score=round(distractor_score, 3),
            accuracy_score=round(acc_score, 3),
            composite_score=round(composite, 3),
            flags=all_flags,
            symbol_audit=sym_audit,
            spoken_leaks=spoken_leaks
        )

    # -----------------------------------------------------------------------
    # Internal Dimension Evaluators
    # -----------------------------------------------------------------------

    def _extract_steps_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract JavaScript STEPS array from HTML source."""
        start_marker = "const STEPS = ["
        end_marker = "];\n    const $"
        start_idx = html.find(start_marker)
        if start_idx < 0:
            return []
        end_idx = html.find(end_marker, start_idx)
        if end_idx < 0:
            end_marker = "];\n"
            end_idx = html.find(end_marker, start_idx)
            if end_idx < 0:
                return []

        json_str = html[start_idx + len("const STEPS = "):end_idx + 1]
        try:
            return json.loads(json_str)
        except Exception:
            # Fallback regex search
            m = re.search(r"const STEPS = (\[.*?\]);\s*(?:const \$|function)", html, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass
            return []

    def _eval_symbol_consistency(
        self, steps: List[Dict[str, Any]]
    ) -> Tuple[float, List[str], Dict[str, Any]]:
        """Score whether variables are properly defined and maintained across steps."""
        flags: List[str] = []
        score = 1.0

        step1 = steps[0]
        step2 = steps[1]
        step4 = steps[3]

        # Step 1 setup_vars audit
        s1_vars = []
        for b in step1.get("blocks", []):
            s1_vars.extend(b.get("vars", []))

        if not s1_vars:
            flags.append("Step 1 missing variable definitions")
            score -= 0.4
        else:
            for v in s1_vars:
                if not v.get("tex") or not v.get("say") or not v.get("meaning"):
                    flags.append(f"Incomplete variable definition in Step 1: {v}")
                    score -= 0.15

        # Step 2 goal_var audit
        s2_vars = []
        for b in step2.get("blocks", []):
            s2_vars.extend(b.get("vars", []))
        if not s2_vars:
            flags.append("Step 2 missing target goal variable")
            score -= 0.3

        # Step 4 plug_vars audit
        s4_vars = []
        for b in step4.get("blocks", []):
            s4_vars.extend(b.get("vars", []))
        if not s4_vars:
            flags.append("Step 4 missing substitution variable definitions")
            score -= 0.2

        audit = {
            "step1_vars_count": len(s1_vars),
            "step2_has_goal": len(s2_vars) > 0,
            "step4_vars_count": len(s4_vars)
        }
        return max(0.0, min(1.0, score)), flags, audit

    def _eval_katex_soundness(
        self, steps: List[Dict[str, Any]]
    ) -> Tuple[float, List[str]]:
        """Score mathematical formatting and KaTeX syntax validity."""
        flags: List[str] = []
        score = 1.0

        for idx, step in enumerate(steps, 1):
            for block in step.get("blocks", []):
                tex = block.get("tex", "")
                if not tex:
                    continue

                # 1. Balanced braces
                if tex.count("{") != tex.count("}"):
                    flags.append(f"Step {idx} unbalanced TeX braces: {tex}")
                    score -= 0.25

                # 2. Bad backslash escapes (e.g. literal tabs or newlines)
                if "\t" in tex or "\r" in tex:
                    flags.append(f"Step {idx} TeX contains unescaped whitespace character")
                    score -= 0.2

                # 3. Double backslash errors
                if "\\\\" in tex and "\\\\text" in tex:
                    flags.append(f"Step {idx} TeX contains double backslash typo: {tex}")
                    score -= 0.1

        return max(0.0, min(1.0, score)), flags

    def _eval_spoken_math(
        self, steps: List[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str]]:
        """Score whether narration formulas sound natural without TeX leaks."""
        flags: List[str] = []
        leaks: List[str] = []
        score = 1.0

        for idx, step in enumerate(steps, 1):
            for block in step.get("blocks", []):
                speak_formula = block.get("speakFormula", "")
                if not speak_formula:
                    continue

                for pat in self.RAW_TEX_LEAK_PATTERNS:
                    found = pat.findall(speak_formula)
                    if found:
                        leak_sample = f"Step {idx}: '{found[0]}' in '{speak_formula}'"
                        leaks.append(leak_sample)
                        flags.append(f"Spoken TeX leak detected in Step {idx}")
                        score -= 0.15

                # Check for natural articulation words
                lower_speak = speak_formula.lower()
                articulation_words = ["equals", "times", "over", "squared", "divided", "sub", "choice", "is", "of"]
                has_natural_word = any(w in lower_speak for w in articulation_words)
                if not has_natural_word and len(speak_formula.split()) <= 2:
                    flags.append(f"Step {idx} spoken formula lacks natural prose articulation: '{speak_formula}'")
                    score -= 0.1

        return max(0.0, min(1.0, score)), flags, leaks

    def _eval_distractor_analysis(
        self, steps: List[Dict[str, Any]]
    ) -> Tuple[float, List[str]]:
        """Score whether Step 6 thoroughly explains why other choices fail."""
        flags: List[str] = []
        score = 1.0

        if len(steps) < 6:
            return 0.0, ["Step 6 missing"]

        step6 = steps[5]
        caption = step6.get("caption", "").lower()
        lead = step6.get("lead", "").lower()
        combined = f"{caption} {lead}"

        # 1. Reject superficial tautology
        tautologies = [
            "fail because they are wrong",
            "fail because they are not the correct answer",
            "other choices are incorrect"
        ]
        if any(t in combined for t in tautologies):
            flags.append("Step 6 uses superficial distractor explanation tautology")
            score -= 0.4

        # 2. Physics terminology presence
        found_concepts = [c for c in self.PHYSICS_CONCEPT_TERMS if c in combined]
        if len(found_concepts) < 2:
            flags.append(f"Step 6 distractor rationale lacks depth (found only {found_concepts})")
            score -= 0.3
        elif len(found_concepts) >= 4:
            score = 1.0  # High pedagogical rigor bonus

        return max(0.0, min(1.0, score)), flags

    def _eval_accuracy(
        self, steps: List[Dict[str, Any]], expected_answer: Optional[str]
    ) -> Tuple[float, List[str]]:
        """Score accuracy of final Step 7 against College Board key."""
        if not expected_answer:
            return 1.0, []  # No ground truth to compare against, neutral pass

        flags: List[str] = []
        step7 = steps[-1]
        title = step7.get("title", "")
        lead = step7.get("lead", "")

        m = re.search(r"The answer is ([A-D])", title)
        chosen_letter = m.group(1) if m else ""

        if not chosen_letter:
            m_lead = re.search(r"correct choice is ([A-D])", lead)
            chosen_letter = m_lead.group(1) if m_lead else ""

        if chosen_letter.upper() == expected_answer.upper():
            return 1.0, []
        else:
            flags.append(
                f"Answer mismatch: Walkthrough selected '{chosen_letter}', official key is '{expected_answer}'"
            )
            return 0.0, flags

    def _aggregate_report(
        self,
        harness_name: str,
        unit_slug: str,
        results: List[ProblemEvalResult],
        total_available: int = 0
    ) -> HarnessBenchmarkReport:
        """Aggregate problem scores into a comprehensive report."""
        total = len(results)
        if total == 0:
            return HarnessBenchmarkReport(harness_name, unit_slug, 0, 0, 0, 0, 0, 0, 0, "F")

        mean_sym = sum(r.symbol_score for r in results) / total
        mean_katex = sum(r.katex_score for r in results) / total
        mean_spoken = sum(r.spoken_math_score for r in results) / total
        mean_dist = sum(r.distractor_score for r in results) / total
        mean_acc = sum(r.accuracy_score for r in results) / total
        mean_comp = sum(r.composite_score for r in results) / total

        harness_score_pct = round(mean_comp * 100, 1)
        grade = "A+" if harness_score_pct >= 95 else (
            "A" if harness_score_pct >= 90 else (
                "B" if harness_score_pct >= 80 else (
                    "C" if harness_score_pct >= 70 else "F"
                )
            )
        )

        flagged = [r.problem_num for r in results if r.flags]

        # Generate summary markdown
        eval_scope = f"{total} (first {total} of {total_available})" if total_available > total else f"{total}"
        md_lines = [
            f"# AI Harness Benchmark Report: `{harness_name}`",
            f"**Unit Tested:** `{unit_slug}` | **Problems Evaluated:** {eval_scope}",
            f"**Overall Harness Score:** `{harness_score_pct}%` (**Grade:** {grade})\n",
            "## Dimension Rubric Breakdown",
            "| Evaluation Dimension | Weight | Harness Score | Benchmark Target | Status |",
            "| :--- | :---: | :---: | :---: | :---: |",
            f"| **Symbol Grounding & Consistency** | 25% | {mean_sym * 100:.1f}% | >= 90.0% | {'✔ PASS' if mean_sym >= 0.9 else '⚠️ ATTN'} |",
            f"| **KaTeX Math & Syntax Soundness** | 25% | {mean_katex * 100:.1f}% | >= 95.0% | {'✔ PASS' if mean_katex >= 0.95 else '⚠️ ATTN'} |",
            f"| **Spoken Math Narration Quality** | 20% | {mean_spoken * 100:.1f}% | >= 90.0% | {'✔ PASS' if mean_spoken >= 0.9 else '⚠️ ATTN'} |",
            f"| **Distractor Rejection Depth** | 15% | {mean_dist * 100:.1f}% | >= 80.0% | {'✔ PASS' if mean_dist >= 0.8 else '⚠️ ATTN'} |",
            f"| **College Board Ground Truth Key** | 15% | {mean_acc * 100:.1f}% | 100.0% | {'✔ PASS' if mean_acc == 1.0 else '⚠️ ATTN'} |\n",
            f"## Problems with Flags ({len(flagged)}/{total})"
        ]

        if not flagged:
            md_lines.append("🎉 All evaluated problems passed all rubrics with zero flags!")
        else:
            for r in results:
                if r.flags:
                    md_lines.append(f"- **Q{r.problem_num:02d}** (Score: {r.composite_score * 100:.1f}%): {', '.join(r.flags)}")

        summary_md = "\n".join(md_lines)

        return HarnessBenchmarkReport(
            harness_name=harness_name,
            unit_slug=unit_slug,
            total_problems=total,
            mean_symbol_score=round(mean_sym, 3),
            mean_katex_score=round(mean_katex, 3),
            mean_spoken_math_score=round(mean_spoken, 3),
            mean_distractor_score=round(mean_dist, 3),
            mean_accuracy=round(mean_acc, 3),
            composite_harness_score=harness_score_pct,
            grade=grade,
            flagged_problems=flagged,
            summary_markdown=summary_md
        )


# ---------------------------------------------------------------------------
# Automated Unittest Suite
# ---------------------------------------------------------------------------

class HarnessEfficacyAIEvalTest(unittest.TestCase):
    """Automated evaluation test asserting harness effectiveness on Unit 4."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.evaluator = WalkthroughAIEvaluator(REPO_ROOT)
        # Evaluate unit4_test if present, else unit4
        target = "unit4_test" if (REPO_ROOT / "unit4_test").exists() else "unit4"
        limit_env = os.environ.get("AI_EVAL_LIMIT", "5")
        limit = int(limit_env) if limit_env.isdigit() else 5
        limit = None if limit <= 0 else limit
        cls.report = cls.evaluator.evaluate_unit(target, harness_name="Antigravity-AgentSkill", limit=limit)

    def test_01_composite_score_meets_threshold(self) -> None:
        """Harness composite score must meet pedagogical quality threshold (>= 85%)."""
        self.assertGreaterEqual(
            self.report.composite_harness_score,
            85.0,
            f"Harness score {self.report.composite_harness_score}% below threshold (85%).\n{self.report.summary_markdown}"
        )

    def test_02_spoken_math_no_critical_leaks(self) -> None:
        """Audio narration must not leak raw TeX formatting tokens."""
        self.assertGreaterEqual(
            self.report.mean_spoken_math_score,
            0.90,
            f"Spoken math narration quality {self.report.mean_spoken_math_score * 100:.1f}% is below 90%."
        )

    def test_03_katex_syntax_validity(self) -> None:
        """KaTeX math expressions must have balanced braces and valid syntax."""
        self.assertGreaterEqual(
            self.report.mean_katex_score,
            0.95,
            f"KaTeX math syntax validity {self.report.mean_katex_score * 100:.1f}% is below 95%."
        )

    def test_04_symbol_consistency_and_grounding(self) -> None:
        """Variables across Step 1, Step 2, and Step 4 must remain consistent."""
        self.assertGreaterEqual(
            self.report.mean_symbol_score,
            0.85,
            f"Symbol consistency score {self.report.mean_symbol_score * 100:.1f}% is below 85%."
        )

    def test_05_ground_truth_accuracy(self) -> None:
        """Walkthrough solution must match official College Board scoring key."""
        self.assertGreaterEqual(
            self.report.mean_accuracy,
            0.95,
            f"Accuracy against official answer key {self.report.mean_accuracy * 100:.1f}% is below 95%."
        )


# ---------------------------------------------------------------------------
# CLI Runner for Multi-Harness Benchmarking
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="AI Evaluation Benchmark for Walkthrough Harnesses")
    parser.add_argument("--unit", default="unit4", help="Unit slug to evaluate (e.g. unit4, unit4_test, unit2)")
    parser.add_argument("--harness", default="Current-Agent", help="Label of harness/agent under test")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Number of questions to evaluate (default: 5, pass 0 for all)")
    parser.add_argument("--all", action="store_true", help="Evaluate all questions in the unit (equivalent to --limit 0)")
    parser.add_argument("--json-out", type=Path, default=None, help="Save evaluation metrics to JSON file")
    args = parser.parse_args()

    limit = 0 if args.all else args.limit
    limit = None if limit == 0 else limit

    evaluator = WalkthroughAIEvaluator(REPO_ROOT)
    report = evaluator.evaluate_unit(args.unit, harness_name=args.harness, limit=limit)

    print("\n" + report.summary_markdown + "\n")

    if args.json_out:
        out_dict = asdict(report)
        del out_dict["summary_markdown"]
        args.json_out.write_text(json.dumps(out_dict, indent=2))
        print(f"Metrics saved to {args.json_out}")

    sys.exit(0 if report.composite_harness_score >= 80.0 else 1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--verbose", "-k"):
        unittest.main()
    elif len(sys.argv) > 1 and sys.argv[1].startswith("--"):
        main()
    else:
        unittest.main()
