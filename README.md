**Live site:** [https://sethusrinivasan.github.io/ap-physics/](https://sethusrinivasan.github.io/ap-physics/)

# AP Physics C walkthroughs

[![Site](https://img.shields.io/website?url=https%3A%2F%2Fsethusrinivasan.github.io%2Fap-physics%2F&up_message=online&down_message=down&label=site)](https://sethusrinivasan.github.io/ap-physics/)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-live-2088FF?logo=githubpages&logoColor=white)](https://sethusrinivasan.github.io/ap-physics/)
[![Live site tests](https://github.com/sethusrinivasan/ap-physics/actions/workflows/live-site.yml/badge.svg)](https://github.com/sethusrinivasan/ap-physics/actions/workflows/live-site.yml)
[![CodeQL](https://github.com/sethusrinivasan/ap-physics/actions/workflows/codeql.yml/badge.svg)](https://github.com/sethusrinivasan/ap-physics/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/sethusrinivasan/ap-physics/badge)](https://scorecard.dev/viewer/?uri=github.com/sethusrinivasan/ap-physics)
[![Dependabot](https://img.shields.io/badge/dependabot-enabled-025E8C?logo=dependabot&logoColor=white)](https://github.com/sethusrinivasan/ap-physics/network/updates)
[![License: MIT](https://img.shields.io/github/license/sethusrinivasan/ap-physics)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](requirements.txt)
[![Playwright](https://img.shields.io/badge/Playwright-browser_tests-2EAD33?logo=playwright&logoColor=white)](tests/test_browser.py)
[![KaTeX](https://img.shields.io/badge/KaTeX-left--aligned_math-3298dc?logo=katex&logoColor=white)](https://katex.org)
[![Audio](https://img.shields.io/badge/Audio-Edge_TTS_Narration-FF8C00)](skills/ap-physics-walkthrough/)
[![Agent Skill: ap-physics-walkthrough](https://img.shields.io/badge/Agent_Skill-ap--physics--walkthrough-8A2BE2?logo=probot&logoColor=white)](skills/ap-physics-walkthrough/SKILL.md)
[![Pair Programmed with Google Gemini](https://img.shields.io/badge/AI_Agent-Google_Gemini-4285F4?logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Built with Cursor](https://img.shields.io/badge/AI_IDE-Cursor-000000?logo=cursor&logoColor=white)](https://cursor.com)
[![Codex Ready](https://img.shields.io/badge/AI_Agent-OpenAI_Codex-412991?logo=openai&logoColor=white)](https://openai.com)

Step-by-step interactive solutions for AP Physics C topic questions. Each problem keeps the exam item on screen, names every symbol before the formula, and plays English audio through the derivation to the answer choice.

- **Unit 2**: 90 problems covering center of mass, Newton’s laws, gravity, friction, springs, drag, and circular motion.
- **Unit 4**: 36 problems covering linear momentum, impulse, conservation of linear momentum, center of mass velocity, and collisions.

---

## Agent Skill: `ap-physics-walkthrough`

This repository includes a universal, cross-platform **AI Agent Skill** located at [`skills/ap-physics-walkthrough/`](skills/ap-physics-walkthrough/SKILL.md) (discoverable via [`.agents/skills/ap-physics-walkthrough`](.agents/skills/ap-physics-walkthrough) and [`.cursor/rules/ap-physics-walkthrough.mdc`](.cursor/rules/ap-physics-walkthrough.mdc)).

Given two PDF files (**Questions PDF** and **Answers PDF**), any AI coding agent can autonomously build, crop, narrate, and verify a complete unit.

### 1-Step Dependency Installation

Install all system binaries (`poppler-utils` for `pdftoppm`/`pdftotext`) and Python packages (`Pillow`, `qrcode`, `pytest`, `playwright`) in one command:

```bash
./setup.sh
# or directly:
./skills/ap-physics-walkthrough/scripts/install_deps.sh
```

### Running the Pipeline

```bash
python3 skills/ap-physics-walkthrough/scripts/run_unit_pipeline.py \
  --unit 5 \
  --title "Work, Energy, and Power" \
  --questions /path/to/Unit5_Questions.pdf \
  --answers /path/to/Unit5_Answers.pdf
```

### Self-Discovery for Coding Agents

Coding agents self-discover instructions and configuration from:
- **Universal Agent Standard**: [`AGENTS.md`](AGENTS.md)
- **Google Gemini / Antigravity CLI**: [`GEMINI.md`](GEMINI.md) & [`.agents/skills/ap-physics-walkthrough/SKILL.md`](.agents/skills/ap-physics-walkthrough/SKILL.md)
- **Cursor ("Cursoft")**: [`.cursor/rules/ap-physics-walkthrough.mdc`](.cursor/rules/ap-physics-walkthrough.mdc) & [`.cursorrules`](.cursorrules) (trigger with `@ap-physics-walkthrough`)
- **OpenAI Codex & GitHub Copilot**: [`.github/copilot-instructions.md`](.github/copilot-instructions.md) & standalone CLI scripts

### Pipeline Stages & Quality Invariants

1. **High-DPI Visual Cropping**: 250 DPI image extraction for question figures (`q01.png` .. `qN.png`) and answer keys (`a01.png` .. `aN.png`).
2. **Symbols First Pedagogy**: Physical variables and notation are explicitly stated in plain English before mathematical formulas.
3. **Left-Aligned KaTeX Math**: All equations use `\\[ ... \\]` formatted with `fleqn: true`.
4. **Step-by-Step Audio Narration**: 7 audio MP3 snippets per problem synthesized using Edge TTS.
5. **Strict Non-Regression**: Prior units (e.g., `unit2/`, `unit4/`) are strictly immutable and guaranteed untouched.
6. **Automated Verification**:
   ```bash
   python3 skills/ap-physics-walkthrough/scripts/verify_unit.py --unit 4
   ```

---

## Coding Agents & Attribution

This project is built and maintained through human-AI pair programming across leading AI coding agents:

- **[Google Gemini](https://deepmind.google/technologies/gemini/) (via [Antigravity CLI](https://deepmind.google))**:
  - Performed comprehensive visual and variable audits of all Unit 4 questions and official answers to guarantee 100% mathematical fidelity.
  - Rewrote problem specs to ensure all spoken audio narration matches exact exam variables ($m_0, 2m_0, p_0, K_0, v_{\text{cm}}$).
  - Architected and packaged the cross-platform **`ap-physics-walkthrough`** autonomous agent skill, regression test suite, and agent self-discovery metadata.
- **[Cursor](https://cursor.com) ("Cursoft")**:
  - Designed the initial web player layout, sticky problem bar, KaTeX formula step slider, and mobile SVG QR code integration.
  - Authored the foundational interactive walkthroughs for the 90 problems of Unit 2.
- **[OpenAI Codex](https://openai.com)**:
  - Supported initial script automation, parsing utilities, and cross-platform command-line integration.

Questions and official solution images come from AP Physics C problem sets shared by a school teacher. They remain the property of the College Board. This project is an independent study aid and is not affiliated with or endorsed by the College Board.

---

## Repository Structure

- [`index.html`](index.html) — Unit list (GitHub Pages home)
- [`unit2/`](unit2/) — Unit 2 TOC, problems `q1`–`q90`, and exam/solution crops
- [`unit4/`](unit4/) — Unit 4 TOC, problems `q1`–`q36`, and exam/solution crops
- [`skills/ap-physics-walkthrough/`](skills/ap-physics-walkthrough/) — Universal agent skill specification, references, and pipeline scripts
- [`.agents/skills/`](.agents/skills/) — Antigravity agent discovery symlink
- [`.cursor/rules/`](.cursor/rules/) — Cursor rule configuration
- [`AGENTS.md`](AGENTS.md) — Universal coding agent guidelines and rules
- [`GEMINI.md`](GEMINI.md) — Gemini / Antigravity CLI project configuration
- [`tools/`](tools/) — Build scripts and problem generators
- [`tests/`](tests/) — HTTP and Playwright smoke tests
- [`LICENSE`](LICENSE) — MIT

---

## Tests

Need **Python 3.10+**. From the repo root, install dependencies and run every test (HTTP + browser):

```bash
./run-tests.sh
```

That script creates `.venv`, installs [`requirements.txt`](requirements.txt), downloads Playwright Chromium, and runs `unittest` against https://sethusrinivasan.github.io/ap-physics/. To hit a local server instead:

```bash
python3 -m http.server 8771 --bind 127.0.0.1
BASE_URL=http://127.0.0.1:8771/ ./run-tests.sh
```

Manual setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python -m unittest discover -s tests -v
```

HTTP-only checks (no Chromium):
```bash
python3 -m unittest tests.test_live_site -v
```

Unit & Skill Verification:
```bash
python3 skills/ap-physics-walkthrough/scripts/verify_unit.py --unit 4
PYTHONPATH=. pytest tests/
```

On Debian/Ubuntu, a full venv needs the `python3-venv` package. `./run-tests.sh` still works without it: it bootstraps pip in `.venv` or falls back to `pip --user`. GitHub Actions runs `./run-tests.sh` as well as CodeQL, OpenSSF Scorecard, and dependency review.
