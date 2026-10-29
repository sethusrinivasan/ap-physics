#!/usr/bin/env python3
"""Stage 4: Player, QR Code & Navigation Builder

Generates individual problem pages (q1/index.html..qN/index.html), SVG QR codes,
the Unit Table of Contents, and updates root index.html and sitemap.xml.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
import qrcode
import qrcode.image.svg


def make_qr_svg(url: str, dest_path: Path) -> None:
    """Generate an SVG QR code for mobile handoff."""
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(image_factory=factory, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    dest_path.write_bytes(img.to_string())


def load_specs(specs_path: Path) -> dict[int, dict]:
    """Dynamically import specs module."""
    spec = importlib.util.spec_from_file_location("unit_specs", specs_path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load specs from {specs_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "SPECS")


def make_steps(n: int, spec: dict, ans: str) -> list[dict]:
    """Assemble 7 pedagogical steps matching the interactive player schema."""
    others = [c for c in "ABCD" if c != ans]
    other_str = ", ".join(others[:-1]) + f" and {others[-1]}"
    
    return [
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


def build_page_html(unit_num: int, n: int, total: int, spec: dict, parsed: dict, steps: list[dict], template_html: str) -> str:
    """Build single walkthrough page using shared player layout and templates."""
    title_text = f"AP Physics C Unit {unit_num} Question {n}: {spec['title']}"
    desc_text = f"Step-by-step AP Physics C Mechanics walkthrough for Unit {unit_num}, question {n}, on {spec['title']}. Symbols are named before each formula, and the steps are narrated in English."
    canonical_url = f"https://sethusrinivasan.github.io/ap-physics/unit{unit_num}/q{n}/"
    
    prev_link = '<span class="off">Previous problem</span>' if n == 1 else f'<a href="../q{n-1}/index.html">Previous problem</a>'
    next_link = f'<a href="../q{n+1}/index.html">Next problem</a>' if n < total else '<span class="off">Next problem</span>'
    
    # Replace metadata and dynamic contents
    html = template_html
    html = re.sub(r"<title>.*?</title>", f"<title>{title_text}</title>", html)
    html = re.sub(r'<meta name="description" content=".*?" />', f'<meta name="description" content="{desc_text}" />', html)
    html = re.sub(r'<link rel="canonical" href=".*?" />', f'<link rel="canonical" href="{canonical_url}" />', html)
    html = re.sub(r'<meta property="og:title" content=".*?" />', f'<meta property="og:title" content="{title_text}" />', html)
    html = re.sub(r'<meta property="og:description" content=".*?" />', f'<meta property="og:description" content="{desc_text}" />', html)
    html = re.sub(r'<meta property="og:url" content=".*?" />', f'<meta property="og:url" content="{canonical_url}" />', html)
    
    # JSON-LD
    json_ld = {
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": title_text,
        "description": desc_text,
        "learningResourceType": "Walkthrough",
        "educationalLevel": "High school",
        "teaches": spec["title"],
        "inLanguage": "en",
        "url": canonical_url,
        "isPartOf": {
            "@type": "WebSite",
            "name": "AP Physics C walkthroughs",
            "url": "https://sethusrinivasan.github.io/ap-physics/"
        }
    }
    json_ld_str = json.dumps(json_ld, indent=2)
    html = re.sub(
        r'<script type="application/ld\+json">.*?</script>',
        lambda _: f'<script type="application/ld+json">\n{json_ld_str}\n  </script>',
        html,
        flags=re.DOTALL
    )
    
    # Header & Nav
    html = re.sub(r'<h1>Interactive walkthrough · Unit \d+, Question \d+</h1>', f'<h1>Interactive walkthrough · Unit {unit_num}, Question {n}</h1>', html)
    html = re.sub(r'<h1>Question \d+ · .*?</h1>', f'<h1>Question {n} · {spec["title"]}</h1>', html)
    
    nav_markup = f"""      <nav class="problem-nav" aria-label="Problem navigation">
        {prev_link}
        <a href="../index.html">Contents</a>
        {next_link}
      </nav>"""
    html = re.sub(r'<nav class="(?:problem-)?nav".*?</nav>', lambda _: nav_markup, html, flags=re.DOTALL)
    
    # Problem Bar figures & QR links
    html = re.sub(r'href="https://sethusrinivasan\.github\.io/ap-physics/[^"]+/q\d+/"', f'href="{canonical_url}"', html)
    html = re.sub(r'aria-label="QR code to open [^"]+"', f'aria-label="QR code to open Unit {unit_num} Question {n} on a phone"', html)
    html = re.sub(r'\.\./figures/q\d+\.png', f'../figures/q{n:02d}.png', html)
    html = re.sub(r'\.\./figures/a\d+\.png', f'../figures/a{n:02d}.png', html)
    html = re.sub(r'alt="Question \d+ exact exam item', f'alt="Question {n} exact exam item', html)
    
    # STEPS array in JS (use literal string replacement to avoid regex backslash escape parsing)
    steps_json = json.dumps(steps, indent=2)
    start_marker = "const STEPS = ["
    end_marker = "\n    const $ = (id)"
    start_idx = html.find(start_marker)
    end_idx = html.find(end_marker, start_idx)
    if start_idx >= 0 and end_idx >= 0:
        html = html[:start_idx] + f"const STEPS = {steps_json};" + html[end_idx:]
    else:
        html = re.sub(
            r"const STEPS = \[.*?\];\n    const \$ =",
            lambda _: f"const STEPS = {steps_json};\n    const $ =",
            html,
            flags=re.DOTALL
        )
    
    return html


def build_toc_html(unit_display: str | int, unit_slug: str, title: str, count: int, specs: dict[int, dict], parsed: list[dict]) -> str:
    """Generate Unit Table of Contents page conforming to canonical site table layout."""
    rows = []
    for item in parsed:
        n = item["n"]
        spec = specs.get(n, {})
        sub_title = spec.get("title", f"Question {n}")
        blurb = spec.get("blurb", "")
        
        rows.append(f"""        <tr>
          <td class="num">Question {n}</td>
          <td>
            <div class="topic">{sub_title}</div>
            <p class="blurb">{blurb}</p>
          </td>
          <td><a class="open" href="q{n}/index.html">Open walkthrough</a></td>
        </tr>""")
        
    rows_html = "\n".join(rows)
    canonical_url = f"https://sethusrinivasan.github.io/ap-physics/{unit_slug}/"
    desc_text = f"Step-by-step interactive walkthroughs for all {count} problems in AP Physics C Mechanics Unit {unit_display}: {title}."
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AP Physics C Unit {unit_display}: {title}</title>
  <meta name="description" content="{desc_text}" />
  <link rel="canonical" href="{canonical_url}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="AP Physics C Unit {unit_display}: {title}" />
  <meta property="og:description" content="{desc_text}" />
  <meta property="og:url" content="{canonical_url}" />
  <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LearningResource",
  "name": "AP Physics C Unit {unit_display}: {title}",
  "description": "{desc_text}",
  "learningResourceType": "Walkthrough",
  "educationalLevel": "High school",
  "teaches": "AP Physics C Unit {unit_display} {title}",
  "inLanguage": "en",
  "url": "{canonical_url}",
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
        <h1>AP Physics C Unit {unit_display}: {title}</h1>
        <button type="button" class="qr-toggle" id="qrToggle" aria-expanded="true" aria-controls="pageQr">Hide QR</button>
      </div>
      <p>Open a problem for the step-by-step walkthrough with captions and English audio. Each problem has Previous, Contents, and Next.</p>
      <a class="page-qr" id="pageQr" href="{canonical_url}" target="_blank" rel="noopener noreferrer" aria-label="QR code to open Unit {unit_display} on a phone">
        <img src="qr.svg" alt="" width="120" height="120" />
        <span>Scan</span>
      </a>
    </header>
    <h2>Questions 1–{count}</h2>
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
</html>"""


def update_root_index(repo_root: Path, unit_id: str | int, title: str, count: int) -> None:
    """Add new unit to root index.html list if not already present."""
    u_str = str(unit_id).strip()
    unit_slug = u_str.lower() if u_str.lower().startswith("unit") else f"unit{u_str.lower()}"
    index_file = repo_root / "index.html"
    if not index_file.exists():
        return
    content = index_file.read_text()
    link_token = f'href="{unit_slug}/index.html"'
    if link_token in content:
        return
        
    unit_entry = f"""      <li>
        <h2><a href="{unit_slug}/index.html">Unit {unit_id}: {title}</a></h2>
        <p>{count} multiple-choice problems with step-by-step interactive player and audio narration.</p>
      </li>"""
    content = re.sub(r"(</ul>)", f"{unit_entry}\n    \\1", content, count=1)
    index_file.write_text(content)


def update_sitemap(repo_root: Path, unit_id: str | int, count: int) -> None:
    """Add new unit pages to sitemap.xml."""
    u_str = str(unit_id).strip()
    unit_slug = u_str.lower() if u_str.lower().startswith("unit") else f"unit{u_str.lower()}"
    sitemap_file = repo_root / "sitemap.xml"
    if not sitemap_file.exists():
        return
    content = sitemap_file.read_text()
    if f"{unit_slug}/" in content:
        return
        
    urls = [f"  <url><loc>https://sethusrinivasan.github.io/ap-physics/{unit_slug}/</loc></url>"]
    for n in range(1, count + 1):
        urls.append(f"  <url><loc>https://sethusrinivasan.github.io/ap-physics/{unit_slug}/q{n}/</loc></url>")
    block = "\n".join(urls)
    content = re.sub(r"(</urlset>)", f"{block}\n\\1", content)
    sitemap_file.write_text(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build interactive walkthrough pages")
    parser.add_argument("--repo-root", required=True, type=Path, help="AP Physics repository root")
    parser.add_argument("--unit", required=True, type=str, help="Unit number or identifier")
    parser.add_argument("--title", required=True, type=str, help="Unit title")
    parser.add_argument("--specs", required=True, type=Path, help="Path to unit specs python file")
    parser.add_argument("--parsed", required=True, type=Path, help="Path to unit parsed json")
    parser.add_argument("--no-root-update", action="store_true", help="Skip updating root index.html and sitemap.xml")
    args = parser.parse_args()
    
    u_val = str(args.unit).strip()
    unit_slug = u_val.lower() if u_val.lower().startswith("unit") else f"unit{u_val.lower()}"
    unit_display = args.unit.replace("unit", "").replace("Unit", "").strip() or args.unit
    unit_dir = args.repo_root / unit_slug
    unit_dir.mkdir(parents=True, exist_ok=True)
    
    specs = load_specs(args.specs)
    with open(args.parsed) as f:
        parsed_list = json.load(f)
    total = len(parsed_list)
    
    # Template extracted from latest complete walkthrough
    template_html = (args.repo_root / "unit2" / "q90" / "index.html").read_text()
    
    # Build each problem page and QR code
    for item in parsed_list:
        n = item["n"]
        spec = specs.get(n, {})
        ans = item.get("answer", "A")
        q_dir = unit_dir / f"q{n}"
        q_dir.mkdir(parents=True, exist_ok=True)
        
        steps = make_steps(n, spec, ans)
        page_html = build_page_html(unit_display, n, total, spec, item, steps, template_html)
        (q_dir / "index.html").write_text(page_html)
        
        qr_url = f"https://sethusrinivasan.github.io/ap-physics/{unit_slug}/q{n}/"
        make_qr_svg(qr_url, q_dir / "qr.svg")
        print(f"Generated Q{n} page and QR code.")
        
    # Build TOC and QR
    toc_html = build_toc_html(unit_display, unit_slug, args.title, total, specs, parsed_list)
    (unit_dir / "index.html").write_text(toc_html)
    make_qr_svg(f"https://sethusrinivasan.github.io/ap-physics/{unit_slug}/", unit_dir / "qr.svg")
    print(f"Unit {args.unit} TOC created.")
    
    # Update root index & sitemap
    if not args.no_root_update:
        update_root_index(args.repo_root, args.unit, args.title, total)
        update_sitemap(args.repo_root, args.unit, total)
        print("Site index and sitemap updated.")
    else:
        print("Skipped root index and sitemap update (--no-root-update requested).")


if __name__ == "__main__":
    main()
