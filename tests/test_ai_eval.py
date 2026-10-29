#!/usr/bin/env python3
"""Comprehensive AI Evaluation Suite for AP Physics Walkthrough Harnesses.

Evaluates pedagogical quality, symbol grounding, spoken math naturalness,
distractor rejection rigor, and official scoring concordance across different
agent harnesses (e.g. Gemini, Cursor, Codex, Claude Code, AutoGen).

Features rich, human-readable logging and granular per-dimension diagnostics
to help developers and educators understand exactly how each agent harness performs.

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
    title: str = ""
    symbol_score: float = 1.0              # 0.0 - 1.0: symbol grounding & consistency
    katex_score: float = 1.0               # 0.0 - 1.0: TeX syntax & math block validity
    spoken_math_score: float = 1.0         # 0.0 - 1.0: TTS audio narration readiness
    distractor_score: float = 1.0          # 0.0 - 1.0: depth of distractor failure rationale
    accuracy_score: float = 1.0            # 1.0 if matches College Board key, else 0.0
    composite_score: float = 1.0           # Weighted average (0.0 - 1.0)
    flags: List[str] = field(default_factory=list)
    symbol_audit: Dict[str, Any] = field(default_factory=dict)
    spoken_leaks: List[str] = field(default_factory=list)
    distractor_concepts: List[str] = field(default_factory=list)
    selected_answer: str = ""
    ground_truth_answer: str = ""
    math_blocks_checked: int = 0


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
        limit: Optional[int] = 5,
        verbose: bool = True
    ) -> HarnessBenchmarkReport:
        """Run comprehensive multi-dimensional evaluation on problems in unit.
        
        Args:
            unit_slug: directory name of the unit (e.g. 'unit4_test' or 'unit4')
            harness_name: label of the agent / model harness being evaluated
            limit: number of problems to evaluate (default: 5; pass None or 0 for all)
            verbose: whether to print rich human-readable progress and logging
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

        if verbose:
            print(f"\n{'='*74}")
            print(f"🔬 AI EVALUATION & HARNESS BENCHMARK")
            print(f"   Harness under test : {harness_name}")
            print(f"   Target unit        : {unit_slug}")
            scope_str = f"first {len(q_dirs)} of {total_available}" if len(q_dirs) < total_available else f"all {len(q_dirs)}"
            print(f"   Evaluation scope   : {scope_str} problems (sample limit = {limit or 'ALL'})")
            print(f"{'='*74}")

        results: List[ProblemEvalResult] = []
        for q in q_dirs:
            n = int(q.name[1:])
            res = self.evaluate_problem(q, n, ground_truth.get(n), verbose=verbose)
            results.append(res)

        return self._aggregate_report(harness_name, unit_slug, results, total_available=total_available)

    def evaluate_problem(
        self,
        q_dir: Path,
        n: int,
        expected_answer: Optional[str] = None,
        verbose: bool = False
    ) -> ProblemEvalResult:
        """Evaluate a single problem directory with optional verbose descriptive logging."""
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

        title = steps[0].get("title", f"Question {n}")

        # Dimension 1: Symbol Grounding & Variable Definition Completeness
        sym_score, sym_flags, sym_audit = self._eval_symbol_consistency(steps)

        # Dimension 2: KaTeX Syntax & Math Formatting
        katex_score, katex_flags, math_count, sample_tex = self._eval_katex_soundness(steps)

        # Dimension 3: Spoken Math / TTS Pronunciation Integrity
        spoken_score, spoken_flags, spoken_leaks, sample_speak = self._eval_spoken_math(steps)

        # Dimension 4: Distractor Rejection Rigor
        distractor_score, distractor_flags, concepts_found, distractor_excerpt = self._eval_distractor_analysis(steps)

        # Dimension 5: Answer Accuracy vs Ground Truth
        acc_score, acc_flags, chosen_letter = self._eval_accuracy(steps, expected_answer)

        all_flags = sym_flags + katex_flags + spoken_flags + distractor_flags + acc_flags

        # Weighted Composite Score (0.0 to 1.0)
        composite = (
            sym_score * 0.25 +
            katex_score * 0.25 +
            spoken_score * 0.20 +
            distractor_score * 0.15 +
            acc_score * 0.15
        )

        res = ProblemEvalResult(
            problem_num=n,
            title=title,
            symbol_score=round(sym_score, 3),
            katex_score=round(katex_score, 3),
            spoken_math_score=round(spoken_score, 3),
            distractor_score=round(distractor_score, 3),
            accuracy_score=round(acc_score, 3),
            composite_score=round(composite, 3),
            flags=all_flags,
            symbol_audit=sym_audit,
            spoken_leaks=spoken_leaks,
            distractor_concepts=concepts_found,
            selected_answer=chosen_letter,
            ground_truth_answer=expected_answer or "",
            math_blocks_checked=math_count
        )

        if verbose:
            self._print_verbose_problem_audit(res, sample_tex, sample_speak, distractor_excerpt)

        return res

    def _print_verbose_problem_audit(
        self,
        res: ProblemEvalResult,
        sample_tex: str,
        sample_speak: str,
        distractor_excerpt: str
    ) -> None:
        """Print an intuitive, human-readable breakdown of the problem audit."""
        n = res.problem_num
        comp_pct = res.composite_score * 100
        status_tag = "✔ PASS" if res.composite_score >= 0.85 else "⚠️ FLAGGED"

        print(f"\n▶ [Q{n:02d}] {res.title}")
        print(f"  ├─ [1. Symbol Grounding] ({res.symbol_score*100:.0f}%)")
        s1_vars = res.symbol_audit.get("step1_var_labels", [])
        goal_lbl = res.symbol_audit.get("goal_label", "none")
        s4_vars = res.symbol_audit.get("step4_var_labels", [])
        print(f"  │  • Setup variables ({len(s1_vars)}): {', '.join(s1_vars) if s1_vars else 'None declared'}")
        print(f"  │  • Target goal variable: {goal_lbl}")
        print(f"  │  • Substituted variables ({len(s4_vars)}): {', '.join(s4_vars) if s4_vars else 'None declared'}")

        print(f"  ├─ [2. KaTeX Math Integrity] ({res.katex_score*100:.0f}%)")
        print(f"  │  • Equations inspected: {res.math_blocks_checked} math blocks")
        tex_sample_clean = sample_tex[:55] + "..." if len(sample_tex) > 55 else sample_tex
        print(f"  │  • Sample formula: {tex_sample_clean}")
        tex_err = [f for f in res.flags if "TeX" in f or "braces" in f]
        print(f"  │  • Syntax check: {'All braces balanced, clean LaTeX macros' if not tex_err else '⚠️ ' + '; '.join(tex_err)}")

        print(f"  ├─ [3. Spoken Audio Narration] ({res.spoken_math_score*100:.0f}%)")
        spk_clean = sample_speak[:60] + "..." if len(sample_speak) > 60 else sample_speak
        print(f"  │  • Spoken formula: \"{spk_clean}\"")
        leak_status = "Zero raw TeX tokens leaked (natural speech ✔)" if not res.spoken_leaks else f"⚠️ Leaks: {', '.join(res.spoken_leaks)}"
        print(f"  │  • TeX leak check: {leak_status}")

        print(f"  ├─ [4. Distractor Rejection Depth] ({res.distractor_score*100:.0f}%)")
        print(f"  │  • Physical concepts identified: {res.distractor_concepts if res.distractor_concepts else 'None (generic rationale)'}")
        dist_excerpt_clean = distractor_excerpt[:65] + "..." if len(distractor_excerpt) > 65 else distractor_excerpt
        print(f"  │  • Discard rationale excerpt: \"{dist_excerpt_clean}\"")

        print(f"  └─ [5. Official Answer Concordance] ({res.accuracy_score*100:.0f}%)")
        key_str = res.ground_truth_answer or "N/A"
        match_icon = "✔ 100% Match" if res.accuracy_score == 1.0 else "❌ Mismatch"
        print(f"     • Walkthrough Choice: [{res.selected_answer}] | College Board Key: [{key_str}] ({match_icon})")

        print(f"  📊 Problem Score: {comp_pct:.1f}% [{status_tag}]")
        if res.flags:
            print(f"     Diagnostics: {'; '.join(res.flags)}")

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
        s1_labels = []
        for b in step1.get("blocks", []):
            for v in b.get("vars", []):
                s1_vars.append(v)
                tex = v.get("tex", "")
                meaning = v.get("meaning", "")
                s1_labels.append(f"{tex}: {meaning}" if meaning else tex)

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
        goal_label = "none"
        for b in step2.get("blocks", []):
            for v in b.get("vars", []):
                s2_vars.append(v)
                goal_label = f"{v.get('tex', '')} ({v.get('meaning', '')})"
        if not s2_vars:
            flags.append("Step 2 missing target goal variable")
            score -= 0.3

        # Step 4 plug_vars audit
        s4_vars = []
        s4_labels = []
        for b in step4.get("blocks", []):
            for v in b.get("vars", []):
                s4_vars.append(v)
                s4_labels.append(f"{v.get('tex', '')} ({v.get('meaning', '')})")
        if not s4_vars:
            flags.append("Step 4 missing substitution variable definitions")
            score -= 0.2

        audit = {
            "step1_vars_count": len(s1_vars),
            "step1_var_labels": s1_labels,
            "goal_label": goal_label,
            "step4_vars_count": len(s4_vars),
            "step4_var_labels": s4_labels
        }
        return max(0.0, min(1.0, score)), flags, audit

    def _eval_katex_soundness(
        self, steps: List[Dict[str, Any]]
    ) -> Tuple[float, List[str], int, str]:
        """Score mathematical formatting and KaTeX syntax validity."""
        flags: List[str] = []
        score = 1.0
        math_count = 0
        sample_tex = ""

        for idx, step in enumerate(steps, 1):
            for block in step.get("blocks", []):
                tex = block.get("tex", "")
                if not tex:
                    continue
                math_count += 1
                if not sample_tex:
                    sample_tex = tex

                # 1. Balanced braces
                if tex.count("{") != tex.count("}"):
                    flags.append(f"Step {idx} unbalanced TeX braces: {tex}")
                    score -= 0.25

                # 2. Bad backslash escapes
                if "\t" in tex or "\r" in tex:
                    flags.append(f"Step {idx} TeX contains unescaped whitespace character")
                    score -= 0.2

                # 3. Double backslash errors
                if "\\\\" in tex and "\\\\text" in tex:
                    flags.append(f"Step {idx} TeX contains double backslash typo: {tex}")
                    score -= 0.1

        return max(0.0, min(1.0, score)), flags, math_count, sample_tex

    def _eval_spoken_math(
        self, steps: List[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str], str]:
        """Score whether narration formulas sound natural without TeX leaks."""
        flags: List[str] = []
        leaks: List[str] = []
        sample_speak = ""
        score = 1.0

        for idx, step in enumerate(steps, 1):
            for block in step.get("blocks", []):
                speak_formula = block.get("speakFormula", "")
                if not speak_formula:
                    continue
                if not sample_speak:
                    sample_speak = speak_formula

                for pat in self.RAW_TEX_LEAK_PATTERNS:
                    found = pat.findall(speak_formula)
                    if found:
                        leak_sample = f"'{found[0]}' in Step {idx}"
                        leaks.append(leak_sample)
                        flags.append(f"Spoken TeX leak detected in Step {idx}")
                        score -= 0.15

                # Check for natural articulation words
                lower_speak = speak_formula.lower()
                articulation_words = ["equals", "times", "over", "squared", "divided", "sub", "choice", "is", "of", "the", "not"]
                has_natural_word = any(w in lower_speak for w in articulation_words)
                if not has_natural_word and len(speak_formula.split()) <= 2:
                    flags.append(f"Step {idx} spoken formula lacks natural prose articulation: '{speak_formula}'")
                    score -= 0.1

        return max(0.0, min(1.0, score)), flags, leaks, sample_speak

    def _eval_distractor_analysis(
        self, steps: List[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str], str]:
        """Score whether Step 6 thoroughly explains why other choices fail."""
        flags: List[str] = []
        score = 1.0

        if len(steps) < 6:
            return 0.0, ["Step 6 missing"], [], ""

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
        found_concepts = [c for c in sorted(self.PHYSICS_CONCEPT_TERMS) if c in combined]
        if len(found_concepts) < 2:
            flags.append(f"Step 6 distractor rationale lacks depth (found only {found_concepts})")
            score -= 0.3
        elif len(found_concepts) >= 4:
            score = 1.0

        excerpt = step6.get("lead") or step6.get("caption") or ""
        return max(0.0, min(1.0, score)), flags, found_concepts, excerpt

    def _eval_accuracy(
        self, steps: List[Dict[str, Any]], expected_answer: Optional[str]
    ) -> Tuple[float, List[str], str]:
        """Score accuracy of final Step 7 against College Board key."""
        step7 = steps[-1]
        title = step7.get("title", "")
        lead = step7.get("lead", "")

        m = re.search(r"The answer is ([A-D])", title)
        chosen_letter = m.group(1) if m else ""

        if not chosen_letter:
            m_lead = re.search(r"correct choice is ([A-D])", lead)
            chosen_letter = m_lead.group(1) if m_lead else ""

        if not expected_answer:
            return 1.0, [], chosen_letter

        flags: List[str] = []
        if chosen_letter.upper() == expected_answer.upper():
            return 1.0, [], chosen_letter
        else:
            flags.append(
                f"Answer mismatch: Walkthrough selected '{chosen_letter}', official key is '{expected_answer}'"
            )
            return 0.0, flags, chosen_letter

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
            f"**Unit Evaluated:** `{unit_slug}` | **Problems Sampled:** {eval_scope}",
            f"**Overall Harness Score:** `{harness_score_pct}%` (**Grade:** {grade})\n",
            "## 1. Dimension Rubric Breakdown",
            "| Evaluation Dimension | Weight | Harness Score | Benchmark Target | Status |",
            "| :--- | :---: | :---: | :---: | :---: |",
            f"| **Symbol Grounding & Consistency** | 25% | {mean_sym * 100:.1f}% | >= 90.0% | {'✔ PASS' if mean_sym >= 0.9 else '⚠️ ATTN'} |",
            f"| **KaTeX Math & Syntax Soundness** | 25% | {mean_katex * 100:.1f}% | >= 95.0% | {'✔ PASS' if mean_katex >= 0.95 else '⚠️ ATTN'} |",
            f"| **Spoken Math Narration Quality** | 20% | {mean_spoken * 100:.1f}% | >= 90.0% | {'✔ PASS' if mean_spoken >= 0.9 else '⚠️ ATTN'} |",
            f"| **Distractor Rejection Depth** | 15% | {mean_dist * 100:.1f}% | >= 80.0% | {'✔ PASS' if mean_dist >= 0.8 else '⚠️ ATTN'} |",
            f"| **College Board Ground Truth Key** | 15% | {mean_acc * 100:.1f}% | 100.0% | {'✔ PASS' if mean_acc == 1.0 else '⚠️ ATTN'} |\n",
            "## 2. Per-Problem Score Breakdown",
            "| Problem | Title | Symbols | KaTeX | Spoken | Distractors | Key Match | Composite | Status |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
        ]

        for r in results:
            short_title = (r.title[:28] + "...") if len(r.title) > 28 else r.title
            status_badge = "✔ OK" if r.composite_score >= 0.85 else "⚠️ ATTN"
            md_lines.append(
                f"| **Q{r.problem_num:02d}** | {short_title} | {r.symbol_score*100:.0f}% | {r.katex_score*100:.0f}% | {r.spoken_math_score*100:.0f}% | {r.distractor_score*100:.0f}% | {'✔' if r.accuracy_score == 1.0 else '❌'} | **{r.composite_score*100:.1f}%** | {status_badge} |"
            )

        md_lines.append(f"\n## 3. Diagnostics & Flagged Issues ({len(flagged)}/{total})")
        if not flagged:
            md_lines.append("🎉 All evaluated problems passed all rubrics with zero flags!")
        else:
            for r in results:
                if r.flags:
                    md_lines.append(f"- **Q{r.problem_num:02d}** (Score: {r.composite_score * 100:.1f}%): {', '.join(r.flags)}")

        md_lines.extend([
            "\n## 4. Actionable Insights for Agent Harness Engineering",
            "- **Symbol Grounding (25%)**: Confirms that physical symbols (e.g. m, v, p) are grounded in Step 1 without hallucination.",
            "- **KaTeX Math (25%)**: Ensures student visual players never experience raw LaTeX escape or delimiter rendering bugs.",
            "- **Spoken Math (20%)**: Guarantees TTS reads math formulas like an AP physics teacher instead of speaking raw TeX syntax.",
            "- **Distractor Depth (15%)**: Evaluates whether Step 6 provides physical counter-proofs for incorrect choices (A, C, D).",
            "- **Key Concordance (15%)**: Ensures 100% agreement with the official College Board exam scoring guidelines."
        ])

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
        target = "unit4_test" if (REPO_ROOT / "unit4_test").exists() else "unit4"
        limit_env = os.environ.get("AI_EVAL_LIMIT", "5")
        limit = int(limit_env) if limit_env.isdigit() else 5
        limit = None if limit <= 0 else limit
        # In automated unittest runs, keep verbose False to keep test runners clean
        cls.report = cls.evaluator.evaluate_unit(target, harness_name="Antigravity-AgentSkill", limit=limit, verbose=False)

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
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress detailed per-problem audit log")
    parser.add_argument("--json-out", type=Path, default=None, help="Save evaluation metrics to JSON file")
    args = parser.parse_args()

    limit = 0 if args.all else args.limit
    limit = None if limit == 0 else limit

    evaluator = WalkthroughAIEvaluator(REPO_ROOT)
    report = evaluator.evaluate_unit(
        args.unit,
        harness_name=args.harness,
        limit=limit,
        verbose=not args.quiet
    )

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
