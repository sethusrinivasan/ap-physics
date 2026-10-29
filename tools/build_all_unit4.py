#!/usr/bin/env python3
"""Build all 36 Unit 4 walkthrough pages, QR codes, TOC, and update root index & sitemap."""
from __future__ import annotations

import json
import re
from pathlib import Path
import qrcode
import qrcode.image.svg

from unit4_specs import SPECS

ROOT = Path("/home/home/github/ap-physics")
UNIT4 = ROOT / "unit4"
FIG_DIR = UNIT4 / "figures"
PARSED_JSON = ROOT / "tools" / "unit4_parsed.json"

# Load parsed questions
with open(PARSED_JSON) as f:
    PARSED = {item["n"]: item for item in json.load(f)}

# Extract layout CSS and player JS template from unit2/q90/index.html
Q90_HTML = (ROOT / "unit2" / "q90" / "index.html").read_text()

STYLE_START = Q90_HTML.find("<style>")
STYLE_END = Q90_HTML.find("</style>")
CSS_CONTENT = Q90_HTML[STYLE_START + len("<style>\n") : STYLE_END].strip()

JS_DOLLAR = Q90_HTML.find("    const $ = (id) => document.getElementById(id);")
JS_END = Q90_HTML.rfind("  </script>")
JS_ENGINE = Q90_HTML[JS_DOLLAR:JS_END].strip()


def make_qr_svg(url: str, dest_path: Path) -> None:
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(image_factory=factory, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    dest_path.write_bytes(img.to_string())


def make_steps(n: int, spec: dict, ans: str) -> list[dict]:
    others = [c for c in "ABCD" if c != ans]
    other_str = ", ".join(others[:-1]) + f" and {others[-1]}"
    
    steps = [
        {
            "title": "Look at the setup",
            "blurb": "Name the system before any formula",
            "caption": spec["setup_text"],
            "lead": f"Look at Question {n} at the top. {spec['setup_text']} First establish what is given in the problem.",
            "blocks": [{
                "vars": spec["setup_vars"],
                "explain": "Before computing, identify the objects in the system and determine which quantities are held constant versus changing."
            }]
        },
        {
            "title": "Name what the question asks",
            "blurb": "Identify the target before formulas",
            "caption": f"Target: {spec['goal_var']['meaning']}.",
            "lead": "Next, name the target quantity the question asks you to find. All later formulas are tools to reach this target.",
            "blocks": [{
                "vars": [spec["goal_var"]],
                "explain": f"The target quantity is {spec['goal_var']['meaning']}. Keep this target clearly in view so you do not get pulled off course by extra details in the figure."
            }]
        },
        {
            "title": "Use the governing idea",
            "blurb": "Name symbols then write the law",
            "caption": f"{spec['law_say']} is named first, then the law is written.",
            "lead": f"Here is the governing law for Question {n}. Each symbol is named in plain English before it appears in the formula.",
            "blocks": [{
                "vars": [{
                    "tex": spec["law_tex"].split("=")[0].strip() if "=" in spec["law_tex"] else spec["goal_var"]["tex"],
                    "say": spec["law_say"].split("equals")[0].strip(),
                    "meaning": spec["law_meaning"]
                }],
                "explain": "Write down the governing physics law only after its variables and symbols are defined.",
                "tex": spec["law_tex"],
                "speakFormula": f"{spec['law_say']}."
            }]
        },
        {
            "title": "Substitute the given values",
            "blurb": "Plug the setup into the law",
            "caption": spec["plug_explain"],
            "lead": "Now apply the law to the specific objects, coordinates, or graphs shown in the exam question.",
            "blocks": [{
                "vars": spec.get("plug_vars", [spec["goal_var"]]),
                "explain": spec["plug_explain"],
                "tex": spec["plug_tex"],
                "speakFormula": spec["plug_say"]
            }]
        },
        {
            "title": "Carry the argument through",
            "blurb": "Simplify to a result",
            "caption": spec["carry_explain"],
            "lead": "Simplify the algebraic expression to see which multiple choice option matches the derivation.",
            "blocks": [{
                "vars": [spec["goal_var"]],
                "explain": spec["carry_explain"],
                "tex": spec["carry_tex"],
                "speakFormula": spec["carry_say"]
            }]
        },
        {
            "title": "Why the other choices fail",
            "blurb": "Discard letters that break the law",
            "caption": spec["fail_explain"],
            "lead": f"Choices {other_str} fail because they contradict the physical laws or miscalculate the quantities.",
            "blocks": [{
                "vars": [{
                    "tex": rf"\text{{not }} {ans}",
                    "say": f"not {ans}",
                    "meaning": f"choices {other_str}, which do not match the physics"
                }],
                "explain": spec["fail_explain"],
                "tex": rf"\text{{reject choices }} {other_str}"
            }]
        },
        {
            "title": f"The answer is {ans}",
            "blurb": "Select the matching choice",
            "caption": f"Choice {ans} is the correct letter matching the exam item.",
            "lead": f"The correct choice is {ans}. It is the only option consistent with the derivation above and the official AP scoring guide.",
            "blocks": [{
                "vars": [{
                    "tex": rf"\text{{{ans}}}",
                    "say": f"choice {ans}",
                    "meaning": "the letter that matches the solution"
                }],
                "explain": f"Choice {ans} matches the official College Board solution: {spec['blurb']}",
                "tex": rf"\text{{answer }} {ans}",
                "speakFormula": f"The correct choice is {ans}."
            }],
            "highlight": True
        }
    ]
    return steps


def build_page_html(n: int, total: int, spec: dict, ans: str, steps: list[dict]) -> str:
    title_text = f"AP Physics C Unit 4 Question {n}: {spec['title']}"
    desc_text = f"Step-by-step AP Physics C Mechanics walkthrough for Unit 4, question {n}, on {spec['title']}. Symbols are named before each formula, and the steps are narrated in English."
    canonical_url = f"https://sethusrinivasan.github.io/ap-physics/unit4/q{n}/"
    
    prev_link = '<span class="off">Previous problem</span>' if n == 1 else f'<a href="../q{n-1}/index.html">Previous problem</a>'
    next_link = '<span class="off">Next problem</span>' if n == total else f'<a href="../q{n+1}/index.html">Next problem</a>'
    
    # Adapt CSS for this question's answer
    css = CSS_CONTENT.replace("#choiceC", f"#choice{ans}")
    steps_json = json.dumps(steps, indent=6)
    
    # Inject ANSWER constant in JS
    js = JS_ENGINE.replace('const ANSWER = "C";', f'const ANSWER = "{ans}";')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title_text}</title>
  <meta name="description" content="{desc_text}" />
  <link rel="canonical" href="{canonical_url}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{title_text}" />
  <meta property="og:description" content="{desc_text}" />
  <meta property="og:url" content="{canonical_url}" />
  <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LearningResource",
  "name": "{title_text}",
  "description": "{desc_text}",
  "learningResourceType": "Walkthrough",
  "educationalLevel": "High school",
  "teaches": "{spec['title']}",
  "inLanguage": "en",
  "url": "{canonical_url}",
  "isPartOf": {{
    "@type": "WebSite",
    "name": "AP Physics C walkthroughs",
    "url": "https://sethusrinivasan.github.io/ap-physics/"
  }}
}}
  </script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.css" />
  <style>
{css}
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="title-row">
        <h1>Interactive walkthrough · Unit 4, Question {n}</h1>
        <button type="button" class="qr-toggle" id="qrToggle" aria-expanded="true" aria-controls="pageQr">Hide QR</button>
      </div>
      <nav class="problem-nav" aria-label="Problem navigation">
        {prev_link}
        <a href="../index.html">Contents</a>
        {next_link}
      </nav>
      <a class="page-qr" id="pageQr" href="{canonical_url}" target="_blank" rel="noopener noreferrer" aria-label="QR code to open Unit 4 Question {n} on a phone">
        <img src="qr.svg" alt="" width="120" height="120" />
        <span>Scan</span>
      </a>
    </header>
    <section class="problem-bar exam" id="problemBar" aria-label="Problem statement">
      <div class="exam-frame">
        <img class="exam-cut" src="../figures/q{n:02d}.png" alt="Question {n} exact exam item, including figure and choices" />
      </div>
      <div class="exam-meta">
        <div class="problem-tools">
          <h2><a href="../figures/q{n:02d}.png" target="_blank" rel="noopener noreferrer">The problem</a><span class="dot"> · </span><a href="../figures/a{n:02d}.png" target="_blank" rel="noopener noreferrer">The answer is</a></h2>
          <button type="button" class="problem-toggle" id="problemToggle" aria-expanded="true" aria-controls="problemBar">Hide question</button>
        </div>
        <p>Exact exam cut from the source PDF: wording, figure, and choices A–D. The walkthrough names each symbol before the formula.</p>
        <div class="choices" id="problemChoices"></div>
      </div>
    </section>
    <div class="player">
      <div class="stage-wrap">
        <div class="stage" id="stage" role="region" aria-label="Physics walkthrough video">
          <h2 class="scene-title" id="sceneTitle">Read the problem</h2>
          <div class="viz pagefig" id="viz" hidden></div>
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
  </div>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.js"></script>
  <script>
    const STEPS = {steps_json};
    {js}
  </script>
  <script data-goatcounter="https://ap-physics.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""
    return html


def build_unit4_toc() -> None:
    rows = []
    for n in range(1, 37):
        spec = SPECS[n]
        rows.append(f"""        <tr>
          <td class="num">Question {n}</td>
          <td>
            <div class="topic">{spec['title']}</div>
            <p class="blurb">{spec['blurb']}</p>
          </td>
          <td><a class="open" href="q{n}/index.html">Open walkthrough</a></td>
        </tr>""")
    
    rows_html = "\n".join(rows)
    toc_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AP Physics C Unit 4 topic questions</title>
  <meta name="description" content="Thirty-six AP Physics C Mechanics walkthroughs for Unit 4: Linear Momentum, Impulse, and Collisions. Each problem stays on screen while the derivation is narrated." />
  <link rel="canonical" href="https://sethusrinivasan.github.io/ap-physics/unit4/" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="AP Physics C Unit 4 topic questions" />
  <meta property="og:description" content="Thirty-six AP Physics C Mechanics walkthroughs for Unit 4: Linear Momentum, Impulse, and Collisions. Each problem stays on screen while the derivation is narrated." />
  <meta property="og:url" content="https://sethusrinivasan.github.io/ap-physics/unit4/" />
  <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LearningResource",
  "name": "AP Physics C Unit 4 topic questions",
  "description": "Thirty-six AP Physics C Mechanics walkthroughs for Unit 4: Linear Momentum, Impulse, and Collisions. Each problem stays on screen while the derivation is narrated.",
  "learningResourceType": "Walkthrough",
  "educationalLevel": "High school",
  "teaches": "AP Physics C Unit 4 Linear Momentum and Collisions",
  "inLanguage": "en",
  "url": "https://sethusrinivasan.github.io/ap-physics/unit4/",
  "isPartOf": {{
    "@type": "WebSite",
    "name": "AP Physics C walkthroughs",
    "url": "https://sethusrinivasan.github.io/ap-physics/"
  }}
}}
  </script>
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
    .title-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .page-qr {{
      position: fixed;
      top: 12px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 30;
      display: grid;
      justify-items: center;
      width: 136px;
      padding: 6px 6px 4px;
      background: #fff;
      color: #071018;
      border-radius: 8px;
      text-decoration: none;
      box-shadow: 0 8px 22px rgba(0, 0, 0, 0.35);
    }}
    .page-qr img {{ width: 124px; height: 124px; display: block; }}
    .page-qr span {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      line-height: 1.2;
    }}
    @media (min-width: 901px) {{
      body:not(.qr-off) {{ padding-top: 168px; }}
    }}
    body.qr-off .page-qr {{ display: none; }}
    @media (max-width: 900px) {{
      .page-qr, .qr-toggle {{ display: none; }}
    }}
    .qr-toggle {{
      flex: 0 0 auto;
      border: 1px solid var(--line);
      background: #132536;
      color: var(--ink);
      border-radius: 7px;
      padding: 6px 10px;
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      cursor: pointer;
    }}
    .qr-toggle:hover {{
      border-color: var(--accent);
      color: var(--accent);
    }}
  </style>
</head>
<body>
  <div class="app">
    <p class="back"><a href="../index.html">← All units</a></p>
    <header>
      <div class="title-row">
        <h1>AP Physics C Unit 4: Linear Momentum</h1>
        <button type="button" class="qr-toggle" id="qrToggle" aria-expanded="true" aria-controls="pageQr">Hide QR</button>
      </div>
      <p>Open a problem for the step-by-step walkthrough with captions and English audio. Each problem has Previous, Contents, and Next.</p>
      <a class="page-qr" id="pageQr" href="https://sethusrinivasan.github.io/ap-physics/unit4/" target="_blank" rel="noopener noreferrer" aria-label="QR code to open Unit 4 on a phone">
        <img src="qr.svg" alt="" width="120" height="120" />
        <span>Scan</span>
      </a>
    </header>
    <h2>Questions 1–36</h2>
    <table>
      <thead>
        <tr><th>Problem</th><th>Topic</th><th></th></tr>
      </thead>
      <tbody>
{rows_html}
      </tbody>
    </table>
  </div>
  <script>
    const qrToggle = document.getElementById("qrToggle");
    function setQrOpen(open) {{
      document.body.classList.toggle("qr-off", !open);
      if (qrToggle) {{
        qrToggle.setAttribute("aria-expanded", open ? "true" : "false");
        qrToggle.textContent = open ? "Hide QR" : "Show QR";
      }}
      try {{ sessionStorage.setItem("ap-hide-qr", open ? "0" : "1"); }} catch (err) {{}}
    }}
    if (qrToggle) {{
      setQrOpen(sessionStorage.getItem("ap-hide-qr") !== "1");
      qrToggle.addEventListener("click", () => {{
        setQrOpen(document.body.classList.contains("qr-off"));
      }});
    }}
  </script>
  <script data-goatcounter="https://ap-physics.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""
    (UNIT4 / "index.html").write_text(toc_html)
    make_qr_svg("https://sethusrinivasan.github.io/ap-physics/unit4/", UNIT4 / "qr.svg")
    print("Unit 4 TOC and QR created.")


def update_root_index() -> None:
    index_path = ROOT / "index.html"
    content = index_path.read_text()
    if 'href="unit4/index.html"' in content:
        print("Root index.html already lists Unit 4.")
        return
    
    unit4_row = """        <tr>
          <td class="num">Unit 4</td>
          <td>
            <div class="topic">Linear momentum, impulse, and collisions</div>
            <p class="blurb">36 problems. Linear momentum, impulse-momentum theorem, conservation of momentum, center of mass velocity, and elastic vs. inelastic collisions.</p>
          </td>
          <td><a class="open" href="unit4/index.html">Open unit</a></td>
        </tr>
      </tbody>"""
    content = content.replace("      </tbody>", unit4_row)
    index_path.write_text(content)
    print("Updated root index.html with Unit 4 entry.")


def update_sitemap() -> None:
    sitemap_path = ROOT / "sitemap.xml"
    content = sitemap_path.read_text()
    if "unit4/q36/" in content:
        print("Sitemap already contains Unit 4.")
        return
    
    lines = ["  <url><loc>https://sethusrinivasan.github.io/ap-physics/unit4/</loc></url>"]
    for n in range(1, 37):
        lines.append(f"  <url><loc>https://sethusrinivasan.github.io/ap-physics/unit4/q{n}/</loc></url>")
    
    insert_pos = content.rfind("</urlset>")
    new_content = content[:insert_pos] + "\n".join(lines) + "\n</urlset>\n"
    sitemap_path.write_text(new_content)
    print("Updated sitemap.xml with Unit 4 URLs.")


def build_all() -> None:
    UNIT4.mkdir(parents=True, exist_ok=True)
    total = 36
    
    for n in range(1, total + 1):
        q_dir = UNIT4 / f"q{n}"
        q_dir.mkdir(parents=True, exist_ok=True)
        spec = SPECS[n]
        ans = PARSED[n]["answer"]
        
        steps = make_steps(n, spec, ans)
        html = build_page_html(n, total, spec, ans, steps)
        (q_dir / "index.html").write_text(html)
        
        # Make QR SVG
        make_qr_svg(f"https://sethusrinivasan.github.io/ap-physics/unit4/q{n}/", q_dir / "qr.svg")
        print(f"Generated Q{n} page and QR code.")

    build_unit4_toc()
    update_root_index()
    update_sitemap()


if __name__ == "__main__":
    build_all()
