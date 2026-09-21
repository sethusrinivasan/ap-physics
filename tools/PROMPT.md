# Prompt: add the next AP Physics walkthrough

Use this file to restart the same workflow for a new problem. Copy the prompt below into a new Cursor chat, or mention `@tools/PROMPT.md` and attach the problem PDF(s).

---

Follow the same pattern as the existing walkthroughs in this folder and create an interactive step-by-step walkthrough for the next problem I give in the PDF files.

Requirements (keep these exactly):

- English audio only. Generate MP3 snippets (`audio/step-01.mp3`, …) and use them as playback for each step. Do not rely on silent browser TTS.
- State the problem first. Keep the problem statement visible at the top during interactive navigation (sticky problem bar).
- When stating a formula or variable, explain the variable first, then show the formula.
- Formulas in LaTeX (KaTeX), left-aligned, not centered. Use `fleqn`.
- Keep suffix letters in lowercase, never digits (`M_a`, `F_b`, not `F_{24}`, `m_1`, or `M_A`). Give each quantity a one-letter suffix even when the stem is a number. Keep a numbered suffix only if the exam itself printed that symbol (such as \(F_1\) in the choices).
- Previous / Next problem links, plus a Contents link back to that unit’s table of contents (`unitN/index.html`).
- After the new problem exists, add it to `unitN/index.html` and wire Previous/Next between neighbors. If this is the first problem in a new unit, also add the unit to the root `index.html`.
- Make the heading **The problem** a link that opens the exact exam-cut image (`../figures/qNN.png`) in a new browser window (`target="_blank"`).
- Crop the official solution from the answers PDF (`../figures/aNN.png`). Make the heading **The answer is** a `target="_blank"` link to that image.

How to build it:

1. Read the question PDF and the solutions PDF. If text extraction drops figures or choices, render PDF pages to images and read those.
2. Copy the latest complete walkthrough folder (currently `unit2/q90/`) to `unitN/qM/` using the unit and question numbers. Copy the **full** `index.html` stylesheet — do not slice out `.problem-bar`, `.player`, `.stage`, `.eq`, `.caption`, or `.controls`.
3. Replace the title, sticky problem text, figure/SVG, multiple-choice row, `STEPS` array, and `renderVisual` so they match the new problem. Remove leftover visuals from the previous problem.
4. Keep the player, captions, Play/Pause/Mute/speed, and `generate-audio.mjs` pattern.
5. Run `node generate-audio.mjs` in the new folder to write the MP3s and `audio/manifest.json`.
6. **Required:** add a row for the new problem to `unitN/index.html` in the same pass. Do not leave the unit TOC listing only older problems. New units also get a row on the root `index.html`.
7. Update Previous/Next on the neighboring walkthroughs. Each walkthrough nav should look like: Previous | Contents (`../index.html`) | Next.
8. Serve from the project root so relative links work. Verify in the browser: root units page → unit TOC lists the new problem → open it → Play audio, jump steps, Previous/Next/Contents, **The problem** opens the exam image, and **The answer is** opens the official solution image.

Pedagogy for each step:

- Name every symbol before it appears in a formula.
- One idea per step; 6–10 steps is typical.
- End with the letter choice and why the other choices fail.

Do not add extra markdown files unless asked. Do not commit unless asked.
