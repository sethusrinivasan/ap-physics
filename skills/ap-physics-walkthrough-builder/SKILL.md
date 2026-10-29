---
name: ap-physics-walkthrough-builder
description: End-to-end agent skill to convert AP Physics C Question and Answer PDFs into interactive audio-narrated walkthrough pages with visual crops, KaTeX math, QR codes, and automated regression verification.
---

# AP Physics C Walkthrough Builder Skill

A universal, cross-platform agent skill designed for **Google Gemini (Antigravity CLI)**, **Cursor**, and **OpenAI Codex / CLI Agents**.

This skill accepts two PDF files:
1. **Questions PDF** (e.g., `Unit5_Questions.pdf`)
2. **Answers PDF** (e.g., `Unit5_Answers.pdf`)

and autonomously transforms them into interactive, accessible, step-by-step AP Physics C walkthrough web pages following the proven pedagogical structure of the repository.

---

## 1. Pipeline Overview

The skill executes six deterministic, automated stages:

```
[ Question PDF + Answer PDF ]
              │
              ▼
    Stage 1: High-DPI Visual Cropping
    (Renders 250 DPI images, locates anchors, slices q01..qN & a01..aN)
              │
              ▼
    Stage 2: Multimodal Text & Symbol Extraction
    (Extracts questions, choices A-D, correct keys, and rationale)
              │
              ▼
    Stage 3: 7-Step Pedagogical Synthesis
    (Generates setup, target, law, plug, carry, fail reasons, answer)
              │
              ▼
    Stage 4: Player, QR Code & Navigation Builder
    (Generates index.html for each question, SVG QRs, TOC, sitemap)
              │
              ▼
    Stage 5: Narration Audio Synthesis
    (Chunks English text, generates MP3s and step manifests)
              │
              ▼
    Stage 6: Comprehensive Verification & Regression
    (Validates all assets, KaTeX math, navigation, and prior unit safety)
```

---

## 2. CLI Usage

### Quick Single-Command Run
Run the master pipeline script from the repository root:

```bash
python3 skills/ap-physics-walkthrough-builder/scripts/run_unit_pipeline.py \
  --unit 5 \
  --title "Work, Energy, and Power" \
  --questions /path/to/Unit5_Questions.pdf \
  --answers /path/to/Unit5_Answers.pdf
```

### Optional Flags
* `--dpi 250` — Resolution for rendered crop images (default: 250 DPI).
* `--skip-audio` — Build pages and crops first, skipping audio generation for rapid preview.
* `--overwrite-audio` — Re-synthesize existing MP3 audio files.
* `--dry-run` — Parse and inspect questions without writing site files.

---

## 3. Platform Invocation Guide

### A. Google Gemini / Antigravity CLI (AGY)
* **Triggering**: Say `"Build Unit 5 using the walkthrough builder skill with /path/to/q.pdf and /path/to/a.pdf"`.
* **Behavior**: The agent locates this skill in `.agents/skills/` or `skills/`, inspects PDF crops using multimodal vision (`read_file`), verifies math formulas, and executes `run_unit_pipeline.py`.

### B. Cursor ("Cursoft")
* **Triggering**: In Cursor chat or Composer, type:
  `@walkthrough-builder Build Unit 5 using Questions.pdf and Answers.pdf`
* **Behavior**: Cursor references `.cursor/rules/walkthrough-builder.mdc` and runs the pipeline scripts in the integrated terminal.

### C. OpenAI Codex / Claude Code / Standalone Shell
* **Triggering**: Run `python3 skills/ap-physics-walkthrough-builder/scripts/run_unit_pipeline.py ...` directly in terminal.

---

## 4. Strict Pedagogical & Architectural Rules

1. **Additive Only**: Adding a new unit must never touch, break, or modify existing unit folders (e.g., `unit2/`, `unit4/`).
2. **Double-Linked Navigation**:
   * First problem has `<span class="off">Previous problem</span>` and an active `Next problem` link.
   * Final problem has an active `Previous problem` and `<span class="off">Next problem</span>`.
   * All intermediate problems link cleanly forward and backward.
3. **Symbols First**: Every physical variable must be defined in plain English before appearing in equations.
4. **Subscript Conventions**:
   * Lowercase for standard subscripts ($v_x$, $p_i$, $v_{\text{cm}}$).
   * Uppercase/numbers only when explicitly printed on the exam ($K_0$, $m_1$, $F_T$, $v_{\text{Pcm}}$).
5. **Left-Aligned KaTeX Math**: Math equations use `\\[ ... \\]` blocks formatted with `fleqn: true`.
6. **Mobile QR Code**: Every problem page features an SVG QR code for seamless handoff to mobile phones.

---

## 5. Verification Checklist (Stage 6)

The pipeline automatically validates:
* [x] $N$ question crops (`q01.png` .. `qN.png`) and $N$ solution crops (`a01.png` .. `aN.png`) exist with non-zero size.
* [x] $N \times 7$ audio MP3 files exist (> 2KB each) with matching `manifest.json`.
* [x] All HTML pages contain required player CSS classes (`.player`, `.stage`, `.problem-bar`, `.eq`, `.caption`, `.controls`).
* [x] KaTeX syntax is valid and free of unescaped TeX errors.
* [x] Table of Contents (`unitN/index.html`) links to all $N$ problems.
* [x] Root `index.html` lists the new unit without disturbing existing units.
* [x] `sitemap.xml` includes all new canonical problem URLs.
* [x] Prior units regression test passes with zero file modifications.
