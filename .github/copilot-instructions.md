# GitHub Copilot & Codex Instructions

When interacting with this AP Physics C repository:

1. **Integrated Skill**:
   - The repository includes a standardized pipeline skill located at `skills/ap-physics-walkthrough/`.
   - Master orchestrator: `skills/ap-physics-walkthrough/scripts/run_unit_pipeline.py`.

2. **Quality & Formatting Guidelines**:
   - Never modify or break existing units (`unit2/`, `unit4/`). All new units are additive.
   - Symbols must be explicitly defined in English before formulas appear.
   - KaTeX formulas must be rendered left-aligned using `fleqn: true`.
   - Each problem has English audio narration MP3s for every step.

3. **Verification**:
   - Always run `python3 skills/ap-physics-walkthrough/scripts/verify_unit.py --unit <N>` to ensure all assets, player CSS classes, and regression tests pass.
