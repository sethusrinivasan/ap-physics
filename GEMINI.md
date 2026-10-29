# Gemini & Antigravity CLI Agent Instructions

This project includes the custom agent skill **`ap-physics-walkthrough`** designed for processing AP Physics C Question and Answer PDFs into interactive walkthrough units.

## Available Skill
- **Name**: `ap-physics-walkthrough`
- **Location**: [`skills/ap-physics-walkthrough/SKILL.md`](skills/ap-physics-walkthrough/SKILL.md)
- **Symlink**: [`.agents/skills/ap-physics-walkthrough`](.agents/skills/ap-physics-walkthrough)

## Orchestrator
When asked to build, update, or audit AP Physics units from PDFs, run:
```bash
python3 skills/ap-physics-walkthrough/scripts/run_unit_pipeline.py \
  --unit <N> \
  --title "<Unit Title>" \
  --questions <questions.pdf> \
  --answers <answers.pdf>
```

## Quality Invariants
1. Prior units (`unit2/`, `unit4/`) are additive and immutable. Never disturb their files or navigation links.
2. Every physical symbol must be defined in text before appearing in equations.
3. Equations must be left-aligned KaTeX (`fleqn: true`).
4. Always run verification: `python3 skills/ap-physics-walkthrough/scripts/verify_unit.py --unit <N>`.
