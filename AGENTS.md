# Agent Guidelines: AP Physics C Walkthroughs

This document guides AI coding agents (**Google Gemini / Antigravity CLI**, **Cursor**, **OpenAI Codex**, **GitHub Copilot**, and **Claude Code**) working in this repository.

---

## 1. Repository Purpose & Architecture

This repository hosts interactive, audio-narrated, step-by-step AP Physics C walkthrough pages deployed to GitHub Pages:
- **Live URL**: https://sethusrinivasan.github.io/ap-physics/
- **Unit 2**: 90 problems (`unit2/q1` .. `unit2/q90`)
- **Unit 4**: 36 problems (`unit4/q1` .. `unit4/q36`)

Each problem has:
- A sticky problem bar with link to high-DPI exam crop (`figures/qNN.png`).
- Left-aligned KaTeX mathematical derivations (`fleqn: true`).
- A 7-step pedagogical flow: Setup -> Target -> Law -> Plug -> Carry -> Why other choices fail -> Answer.
- English audio narration for every step (`audio/step-01.mp3` .. `step-07.mp3`) with `audio/manifest.json`.
- A link to the official solution crop (`figures/aNN.png`).
- Mobile-friendly SVG QR code for handoff to phones.

---

## 2. Integrated Agent Skill: `ap-physics-walkthrough`

The repository contains an autonomous agent skill that takes two PDFs (**Questions PDF** and **Answers PDF**) and generates a complete unit walkthrough.

- **Skill Definition**: [`skills/ap-physics-walkthrough/SKILL.md`](skills/ap-physics-walkthrough/SKILL.md)
- **Agent Discovery Symlink**: [`.agents/skills/ap-physics-walkthrough`](.agents/skills/ap-physics-walkthrough)
- **Cursor Rule**: [`.cursor/rules/ap-physics-walkthrough.mdc`](.cursor/rules/ap-physics-walkthrough.mdc)
- **Pipeline Scripts**: [`skills/ap-physics-walkthrough/scripts/`](skills/ap-physics-walkthrough/scripts/)

### How Any Agent Can Run the Skill

```bash
python3 skills/ap-physics-walkthrough/scripts/run_unit_pipeline.py \
  --unit <N> \
  --title "<Unit Title>" \
  --questions <path/to/questions.pdf> \
  --answers <path/to/answers.pdf>
```

#### Pipeline Stages Executed:
1. `crop_pdf.py`: 250 DPI image extraction and slicing of questions and answers.
2. `parse_pdf.py`: Question text, choices A–D, correct answer key, and rationales.
3. `generate_specs.py`: 7-step pedagogical problem specifications.
4. `build_site.py`: HTML player pages, SVG QR codes, Unit TOC, sitemap update.
5. `generate_audio.py`: Edge TTS English audio synthesis and manifest files.
6. `verify_unit.py`: Comprehensive asset, KaTeX, navigation, and prior unit regression verification.

---

## 3. Strict Non-Regression & Quality Rules

When working in this repository, all agents MUST follow these invariants:

1. **Strictly Additive**:
   - Adding a new unit (e.g., Unit 5) must **NEVER** modify, overwrite, or delete existing unit folders (`unit2/`, `unit4/`).
   - Prior unit problem counts and assets must remain 100% intact.
2. **Symbols First**:
   - Always state the physical variable and its meaning in plain English **before** showing its formula.
3. **Subscript Conventions**:
   - Standard physics subscripts in lowercase ($v_{\text{cm}}$, $p_i$, $a_x$).
   - Numbered or uppercase subscripts ($K_0$, $m_1$, $F_T$) only when explicitly printed on the official exam.
4. **Left-Aligned KaTeX**:
   - Always use `\\[ ... \\]` block math configured with `fleqn: true`.
5. **Always Run Verification**:
   - After creating or editing walkthroughs, always run:
     ```bash
     python3 skills/ap-physics-walkthrough/scripts/verify_unit.py --unit <N>
     PYTHONPATH=. pytest tests/
     ```
