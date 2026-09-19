#!/usr/bin/env python3
"""Build Unit 2 walkthroughs 3–90 from the question and solutions PDFs."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from html import escape
from pathlib import Path

ROOT = Path("/home/home/ap-physics")
Q_PDF = Path("/home/home/Downloads/Unit 2 Topic Questions.pdf")
S_PDF = Path("/home/home/Downloads/Unit 2 Topic Questions. Solutions.pdf")
UNIT2 = ROOT / "unit2"
FIG_DIR = UNIT2 / "figures"
AUDIO_GEN = (UNIT2 / "q2" / "generate-audio.mjs").read_text()
Q2 = (UNIT2 / "q2" / "index.html").read_text()

JUNK = re.compile(
    r"(AP PHYSICS C: MECHANICS|Scoring Guide|Test Booklet|"
    r"Unit 2: Topic Questions|AP Physics C: Mechanics|"
    r"Page \d+ of \d+|)",
    re.I,
)


def pdf_text(path: Path, page: int | None = None) -> str:
    cmd = ["pdftotext", "-layout", str(path), "-"]
    if page is not None:
        cmd = ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(path), "-"]
    return subprocess.check_output(cmd, text=True, errors="replace")


def split_items(text: str) -> dict[int, str]:
    parts = re.split(r"(?m)^(\d+)\.\s", text)
    out = {}
    for i in range(1, len(parts), 2):
        out[int(parts[i])] = parts[i + 1]
    return out


def clean(text: str) -> str:
    text = JUNK.sub(" ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def parse_choices(body: str) -> tuple[str, list[tuple[str, str]]]:
    m = re.search(r"\n\s*\(A\)\s", body)
    if not m:
        return clean(body), []
    stem = clean(body[: m.start()])
    rest = body[m.start() :]
    chunks = re.split(r"\n\s*\(([A-D])\)\s*", rest)
    choices = []
    for i in range(1, len(chunks), 2):
        letter = chunks[i]
        txt = clean(chunks[i + 1])
        txt = re.split(r"\n\s*Answer\s+[A-D]", txt, maxsplit=1)[0]
        txt = clean(txt)
        txt = re.sub(r"\s+", " ", txt)
        if txt:
            choices.append((letter, txt))
    return stem, choices


def parse_solution(body: str) -> tuple[str, str]:
    ans = re.search(r"Answer\s+([A-D])", body)
    letter = ans.group(1) if ans else "A"
    expl = body
    if "Correct." in body:
        expl = body.split("Correct.", 1)[1]
    expl = re.split(r"\n\s*\d+\.\s", expl, maxsplit=1)[0]
    expl = clean(expl)
    expl = re.sub(r"\s+", " ", expl)
    return letter, expl


def sentences(text: str) -> list[str]:
    bits = re.split(r"(?<=[.!?])\s+", text.strip())
    return [b.strip() for b in bits if len(b.strip()) > 8]


def question_pages() -> dict[int, int]:
    mapping = {}
    info = subprocess.check_output(["pdfinfo", str(Q_PDF)], text=True)
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    current = None
    for p in range(1, pages + 1):
        t = pdf_text(Q_PDF, p)
        found = [int(n) for n in re.findall(r"(?m)^(\d+)\.\s", t)]
        for n in found:
            mapping[n] = p
            current = n
        if current is not None:
            # later questions on a continuation page already recorded
            pass
    return mapping


def render_pages():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    if list(FIG_DIR.glob("qpage-*.png")):
        return
    subprocess.check_call(
        ["pdftoppm", "-png", "-r", "130", str(Q_PDF), str(FIG_DIR / "qpage")]
    )


def js_string(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def tex_text(s: str) -> str:
    s = s.replace("\\", "\\textbackslash{}")
    s = s.replace("{", "\\{").replace("}", "\\}")
    s = s.replace("%", "\\%")
    return "\\text{" + s.replace("&", "\\&") + "}"


def choice_tex(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "\\;"
    if len(text) > 90:
        text = text[:87] + "..."
    return tex_text(text)


def make_steps(n: int, stem: str, reason: str, answer: str) -> list[dict]:
    stem_one = re.sub(r"\s+", " ", stem)
    if len(stem_one) > 420:
        stem_one = stem_one[:417] + "..."
    why = sentences(reason) or [
        "Use the center-of-mass and force ideas from the figure and the statement."
    ]
    chunks = []
    buf = ""
    for s in why:
        if len(buf) + len(s) < 280:
            buf = (buf + " " + s).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)
    while len(chunks) < 3:
        chunks.append(chunks[-1] if chunks else why[0])
    chunks = chunks[:4]

    steps = [
        {
            "title": "Read the problem",
            "blurb": "Keep the statement and figure in view",
            "caption": "The problem stays at the top. Read the figure as well as the words.",
            "lead": f"First, read the problem at the top. This is Unit 2, Question {n}. {stem_one}",
            "blocks": [
                {
                    "vars": [
                        {
                            "tex": "\\text{figure}",
                            "say": "the figure",
                            "meaning": "the diagram in the sticky problem bar; use it with the written statement",
                        }
                    ],
                    "explain": "Do not skip the figure. Missing lengths, masses, or directions are usually drawn there.",
                    "tex": tex_text(f"Question {n}: start from the statement and the figure"),
                }
            ],
        },
        {
            "title": "Name what the question asks",
            "blurb": "Identify the target before formulas",
            "caption": "State the goal in words first. Then the solution can name symbols.",
            "lead": "Next, name the quantity we must find or compare. Every later formula is only a tool for that target.",
            "blocks": [
                {
                    "vars": [
                        {
                            "tex": "\\text{goal}",
                            "say": "the goal",
                            "meaning": "what the multiple-choice question is asking you to decide",
                        }
                    ],
                    "explain": "Keep that goal in view so extra details in the figure do not pull you off the path.",
                    "tex": tex_text("Find the choice that matches the goal"),
                }
            ],
        },
    ]
    titles = [
        "Use the governing idea",
        "Apply it to the given objects",
        "Compare the options",
        "Check the leftover details",
    ]
    blurbs = [
        "Define the idea first",
        "Bring in the given values",
        "See which choice matches",
        "Discard choices that fail",
    ]
    for i, chunk in enumerate(chunks):
        steps.append(
            {
                "title": titles[i],
                "blurb": blurbs[i],
                "caption": chunk[:180],
                "lead": "Here is the next piece of the solution, with the idea named before any formula.",
                "blocks": [
                    {
                        "vars": [
                            {
                                "tex": "\\text{idea}",
                                "say": "this idea",
                                "meaning": chunk[:160],
                            }
                        ],
                        "explain": chunk,
                        "tex": tex_text(chunk[:110]),
                        "speakFormula": "Keep that idea, then look at the next step.",
                    }
                ],
            }
        )
    steps.append(
        {
            "title": f"The answer is {answer}",
            "blurb": "Select the matching choice",
            "caption": f"Choice {answer}. The other letters disagree with the center-of-mass or force argument above.",
            "lead": f"The correct choice is {answer}. It is the one that matches the reasoning we just built from the figure and the definitions.",
            "blocks": [
                {
                    "vars": [
                        {
                            "tex": "\\text{choice}",
                            "say": f"choice {answer}",
                            "meaning": "the letter that matches the solution",
                        }
                    ],
                    "explain": reason[:400] if reason else f"Choice {answer} is consistent with the walkthrough.",
                    "tex": tex_text(f"Answer {answer}"),
                    "speakFormula": f"The correct choice is {answer}.",
                }
            ],
            "highlight": True,
        }
    )
    return steps


def player_parts():
    css = Q2[Q2.find("<style>") : Q2.find("</style>")]
    extra = """
    .viz.pagefig { height: 168px; }
    .eq.page-eq { top: 230px; }
    .problem-bar { grid-template-columns: minmax(220px, 32%) 1fr; align-items: start; }
    .mini-bar { width: 100%; max-height: 220px; object-fit: contain; background: #0a1824; border-radius: 6px; }
    .fig { width: 100%; height: 100%; object-fit: contain; background: #061018; }
    .problem-bar p { font-size: 13px; }
    .choices { max-height: 7.5em; overflow: auto; }
"""
    css = css + extra
    js = Q2[Q2.find("    const $ = (id)") :]
    pre = js[: js.find("    function choiceRow")]
    mid = js[js.find("    function words(text)") : js.find("    function renderVisual")]
    rest = js[js.find("    function paintStep(i)") :]
    return css, pre, mid, rest


CSS, JS_PRE, JS_MID, JS_REST = player_parts()


def build_html(n: int, total: int, stem: str, choices: list[tuple[str, str]], answer: str, page: int, steps: list[dict]) -> str:
    prev = f'<a href="../q{n-1}/index.html">Previous problem</a>' if n > 1 else '<span class="off">Previous problem</span>'
    nxt = f'<a href="../q{n+1}/index.html">Next problem</a>' if n < total else '<span class="off">Next problem</span>'
    fig = f"../figures/qpage-{page:02d}.png"
    ans = f"../figures/a{n:02d}.png"
    stem_html = escape(stem)
    if not choices:
        choices = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]
    items = ",\n        ".join(
        f'["{let}", {js_string(choice_tex(txt))}, "choice{let}"]' for let, txt in choices[:4]
    )
    css = CSS.replace(
        ".choice.win, .problem-bar.answered #choiceB",
        f".choice.win, .problem-bar.answered #choice{answer}",
    )
    steps_js = "    const STEPS = " + json.dumps(steps, ensure_ascii=False, indent=6) + ";\n"
    choice_js = f"""
    const ANSWER = {js_string(answer)};
    function choiceRow(winner) {{
      const items = [
        {items}
      ];
      return items.map(([letter, tex, id]) =>
        `<span class="choice${{winner && letter === ANSWER ? " win" : ""}}" id="${{id}}">(${{letter}}) ${{renderTex(tex, false)}}</span>`
      ).join("");
    }}
"""
    visual_js = """
    function renderVisual(step) {
      const fig = $("stageFig");
      if (fig) fig.style.filter = step.highlight ? "none" : "none";
    }
"""
    title = f"Unit 2 Q{n} · Walkthrough"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.css" />
  {css}
  </style>
</head>
<body>
  <div class="app">
    <header>
      <h1>Interactive walkthrough · Unit 2, Question {n}</h1>
      <nav class="problem-nav" aria-label="Problem navigation">
        {prev}
        <a href="../index.html">Contents</a>
        {nxt}
      </nav>
    </header>
    <section class="problem-bar" id="problemBar" aria-label="Problem statement">
      <img class="mini-bar" src="{fig}" alt="Question {n} figure from the exam page" />
      <div>
        <div class="problem-tools">
        <h2><a href="{fig}" target="_blank" rel="noopener noreferrer">The problem</a><span class="dot"> · </span><a href="{ans}" target="_blank" rel="noopener noreferrer">The answer is</a></h2>
        <button type="button" class="problem-toggle" id="problemToggle" aria-expanded="true" aria-controls="problemBar">Hide question</button>
        </div>
        <p>{stem_html}</p>
        <div class="choices" id="problemChoices"></div>
      </div>
    </section>
    <div class="player">
      <div class="stage-wrap">
        <div class="stage" id="stage" role="region" aria-label="Physics walkthrough video">
          <div class="badge">Working diagram · formulas explained first</div>
          <h2 class="scene-title" id="sceneTitle">Read the problem</h2>
          <div class="viz pagefig" id="viz">
            <img class="fig" id="stageFig" src="{fig}" alt="Question figure" />
          </div>
          <div class="eq page-eq" id="eq"></div>
          <div class="caption"><span class="cc" id="caption">Press Play. The problem remains visible at the top.</span></div>
        </div>
        <div class="controls">
          <button id="prevBtn" type="button" aria-label="Previous step">Prev</button>
          <button id="playBtn" class="primary" type="button">Play</button>
          <button id="nextBtn" type="button" aria-label="Next step">Next</button>
          <div class="timeline" id="timeline" role="slider" aria-label="Video progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
            <div class="fill" id="fill"></div>
            <div class="marks" id="marks"></div>
          </div>
          <div class="time" id="time">0:00 / 0:00</div>
          <button id="muteBtn" type="button">Mute</button>
          <label class="hint">Speed
            <select id="rate" aria-label="Playback speed">
              <option value="0.85">0.85x</option>
              <option value="1" selected>1x</option>
              <option value="1.15">1.15x</option>
            </select>
          </label>
        </div>
        <audio id="narration" preload="auto"></audio>
      </div>
      <aside class="chapters" aria-label="Steps">
        <h2>Steps</h2>
        <div id="chapterList"></div>
      </aside>
    </div>
    <p class="hint">English narration is recorded MP3 audio for each step. Use Play, and keep the tab unmuted.</p>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.js"></script>
  <script>
{steps_js}
{JS_PRE}{choice_js}{JS_MID}{visual_js}
{JS_REST}
"""


def toc_row(n: int, stem: str) -> str:
    blurb = re.sub(r"\s+", " ", stem)
    if len(blurb) > 160:
        blurb = blurb[:157] + "..."
    topic = blurb.split(".")[0][:80]
    return f"""        <tr>
          <td class="num">Question {n}</td>
          <td>
            <div class="topic">{escape(topic)}</div>
            <p class="blurb">{escape(blurb)}</p>
          </td>
          <td><a class="open" href="q{n}/index.html">Open walkthrough</a></td>
        </tr>"""


def write_toc(rows: list[str]):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AP Physics C · Unit 2</title>
  <style>
    :root {{
      --bg: #071018; --panel: #102033; --ink: #e8eef6; --muted: #9bb0c7;
      --line: #27415c; --accent: #5ec8ff; --gold: #f0c75e;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; min-height: 100%; background: var(--bg); color: var(--ink);
      font-family: "Liberation Sans", "Ubuntu", "Segoe UI", sans-serif; }}
    body {{ display: grid; place-items: start center; padding: 24px 16px 40px; }}
    .app {{ width: min(920px, 100%); }}
    header h1 {{ margin: 0; font-size: 26px; font-weight: 700; }}
    header p {{ margin: 8px 0 22px; color: var(--muted); font-size: 14px; line-height: 1.45; }}
    h2 {{ margin: 0 0 10px; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--gold); }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }}
    th, td {{ text-align: left; padding: 12px 14px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #132536; }}
    .num {{ white-space: nowrap; color: var(--gold); font-weight: 700; width: 7.5em; }}
    .topic {{ color: var(--accent); font-weight: 700; }}
    .blurb {{ margin: 4px 0 0; color: var(--muted); font-size: 13px; line-height: 1.4; }}
    a.open {{ display: inline-block; border: 1px solid var(--line); background: #132536; color: var(--ink);
      border-radius: 7px; padding: 8px 12px; font-size: 13px; text-decoration: none; white-space: nowrap; }}
    a.open:hover {{ border-color: var(--accent); }}
    .hint {{ margin-top: 16px; color: var(--muted); font-size: 12px; }}
    .back {{ margin: 0 0 10px; font-size: 13px; }}
    .back a {{ color: var(--accent); text-decoration: none; }}
    .back a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="app">
    <header>
      <p class="back"><a href="index.html">All units</a></p>
      <h1>Unit 2 · Topic questions</h1>
      <p>Open a problem for the step-by-step walkthrough with captions and English audio. Each problem has Previous, Contents, and Next.</p>
    </header>
    <h2>Questions 1–90</h2>
    <table>
      <thead>
        <tr><th>Problem</th><th>Topic</th><th></th></tr>
      </thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table>
    <p class="hint">To add another problem, follow <a href="../tools/PROMPT.md" style="color: var(--accent);">PROMPT.md</a>.</p>
  </div>
</body>
</html>
"""
    (UNIT2 / "index.html").write_text(html)


def patch_nav(n: int, total: int):
    path = UNIT2 / f"q{n}" / "index.html"
    if not path.exists():
        return
    text = path.read_text()
    prev = (
        '<span class="off">Previous problem</span>'
        if n == 1
        else f'<a href="../q{n-1}/index.html">Previous problem</a>'
    )
    nxt = (
        '<span class="off">Next problem</span>'
        if n == total
        else f'<a href="../q{n+1}/index.html">Next problem</a>'
    )
    text = re.sub(
        r'<nav class="problem-nav" aria-label="Problem navigation">.*?</nav>',
        '<nav class="problem-nav" aria-label="Problem navigation">\n        '
        + prev
        + '\n        <a href="../index.html">Contents</a>\n        '
        + nxt
        + "\n      </nav>",
        text,
        count=1,
        flags=re.S,
    )
    path.write_text(text)


def main():
    print("Extracting PDFs...")
    q_items = split_items(pdf_text(Q_PDF))
    s_items = split_items(pdf_text(S_PDF))
    pages = question_pages()
    total = max(q_items)
    print(f"{total} questions, pages mapped {len(pages)}")
    render_pages()
    print("figures", len(list(FIG_DIR.glob("qpage-*.png"))))

    toc = []
    for n in range(1, total + 1):
        qbody = q_items.get(n, s_items.get(n, ""))
        stem, choices = parse_choices(qbody)
        if not stem:
            stem, choices = parse_choices(s_items.get(n, ""))
        answer, reason = parse_solution(s_items.get(n, qbody))
        page = pages.get(n, 1)
        toc.append(toc_row(n, stem or f"Question {n}"))
        if n in (1, 2):
            continue
        steps = make_steps(n, stem, reason, answer)
        dest = UNIT2 / f"q{n}"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "audio").mkdir(exist_ok=True)
        (dest / "generate-audio.mjs").write_text(AUDIO_GEN)
        html = build_html(n, total, stem, choices, answer, page, steps)
        (dest / "index.html").write_text(html)
        if n % 10 == 0:
            print("built", n)

    write_toc(toc)
    for n in range(1, total + 1):
        patch_nav(n, total)
    prompt = (ROOT / "tools" / "PROMPT.md").read_text()
    prompt = prompt.replace("currently `unit2/q90/`", "currently `unit2/q90/`")
    (ROOT / "tools" / "PROMPT.md").write_text(prompt)
    print("done", total)


if __name__ == "__main__":
    main()
