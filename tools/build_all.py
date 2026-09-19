#!/usr/bin/env python3
"""Build Unit 2 walkthroughs with the FULL working layout CSS. Never slice layout rules."""
from __future__ import annotations

import json
import re
import subprocess
from html import escape
from pathlib import Path

from crop_questions import crop_all

ROOT = Path("/home/home/ap-physics")
Q_PDF = Path("/home/home/Downloads/Unit 2 Topic Questions.pdf")
S_PDF = Path("/home/home/Downloads/Unit 2 Topic Questions. Solutions.pdf")
UNIT2 = ROOT / "unit2"
FIG_DIR = UNIT2 / "figures"
KEEP = {1, 2, 4, 5}  # hand-built pages; only patch nav + TOC
REQUIRED_CSS = [
    ".problem-bar {",
    ".player {",
    ".stage {",
    ".eq {",
    ".caption {",
    ".controls {",
    ".chapters {",
    ".choices {",
]
Q5 = (UNIT2 / "q5" / "index.html").read_text()
AUDIO_GEN = (UNIT2 / "q5" / "generate-audio.mjs").read_text()
JUNK = re.compile(
    r"(AP PHYSICS C: MECHANICS|Scoring Guide|Test Booklet|"
    r"Unit 2: Topic Questions|AP Physics C: Mechanics|"
    r"Page \d+ of \d+|)",
    re.I,
)
Q5_ONLY = """    .viz.platform { height: 168px; }
    .eq.platform-eq { top: 228px; }
    .rock-lab { font-size: 11px; fill: #e8eef6; }
"""
PAGE_CSS = """
    .problem-bar.exam {
      grid-template-columns: 1fr;
      align-items: start;
      gap: 8px;
    }
    .exam-frame {
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 8px;
      max-height: min(42vh, 440px);
      overflow: auto;
    }
    .exam-frame img.exam-cut {
      width: 100%;
      height: auto;
      display: block;
      background: #ffffff;
    }
    .exam-meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px 12px;
    }
    .exam-meta h2 { margin: 0; }
    .exam-meta p { display: none; }
    .viz.pagefig {
      display: none;
      height: 0;
    }
    .eq.page-eq {
      top: 56px;
      bottom: 54px;
    }
    .eq.page-eq .eq-block {
      padding: 12px 14px 14px;
    }
    .eq.page-eq .why {
      font-size: 15px;
      line-height: 1.5;
    }
    .eq.page-eq .katex { font-size: 1.28em; }
    .eq.page-eq .vars li {
      grid-template-columns: 140px 1fr;
      font-size: 14px;
    }
"""

CUSTOM_TOC = {
    1: ("Composite bar cut at the center of mass",
        "Two 12 cm materials, A and B. Density of B is twice A. Find the mass ratio of the left piece to the right piece after the cut."),
    2: ("Y-coordinate of two triangular sphere arrangements",
        "Six identical spheres form triangles A and B. Compare y<sub>cm,a</sub> to y<sub>cm,b</sub>."),
    4: ("Projectile bar orientations that maximize d",
        "A non-uniform bar is launched and lands at the same level. Distance d runs from the right end at launch to the left end at landing. Choose the x<sub>cm</sub> orientations that maximize d."),
    5: ("Third rock that keeps a platform balanced",
        "A platform is balanced at P (7.0 m, 1.0 m). Place a 4.0 kg rock so the three-rock platform system stays balanced with the 1.0 kg and 3.0 kg rocks already on it."),
}


def assert_layout(html: str, label: str) -> None:
    missing = [item for item in REQUIRED_CSS if item not in html]
    if missing:
        raise SystemExit(f"LAYOUT FAIL {label}: missing {missing}")


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
        txt = re.split(r"\n\s*Answer\s+[A-D]", chunks[i + 1], maxsplit=1)[0]
        txt = re.sub(r"\s+", " ", clean(txt))
        choices.append((letter, txt or letter))
    return stem, choices


def parse_solution(body: str) -> tuple[str, str]:
    ans = re.search(r"Answer\s+([A-D])", body)
    letter = ans.group(1) if ans else "A"
    expl = body.split("Correct.", 1)[1] if "Correct." in body else body
    expl = re.split(r"\n\s*\d+\.\s", expl, maxsplit=1)[0]
    expl = re.sub(r"\s+", " ", clean(expl))
    return letter, expl


def sentences(text: str) -> list[str]:
    bits = re.split(r"(?<=[.!?])\s+", text.strip())
    return [b.strip() for b in bits if len(b.strip()) > 8]


def question_pages() -> dict[int, int]:
    info = subprocess.check_output(["pdfinfo", str(Q_PDF)], text=True)
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    mapping = {}
    for p in range(1, pages + 1):
        found = [int(n) for n in re.findall(r"(?m)^(\d+)\.\s", pdf_text(Q_PDF, p))]
        for n in found:
            mapping[n] = p
    return mapping


def render_pages() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    if list(FIG_DIR.glob("qpage-*.png")):
        return
    subprocess.check_call(["pdftoppm", "-png", "-r", "140", str(Q_PDF), str(FIG_DIR / "qpage")])


def clean_speech(s: str) -> str:
    s = s.replace("ⅆ", " d ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("�", "")
    return s


def usable_reason(reason: str) -> str:
    r = clean_speech(reason)
    holey = re.compile(
        r"(\bd d\b|located at d|the -axis|where and |is \.\s|At location ,)",
        re.I,
    )
    keep = [s for s in sentences(r) if len(s) > 35 and not holey.search(s)]
    if holey.search(r) and keep:
        return " ".join(keep)
    if holey.search(r) and not keep:
        return (
            "Use the symbols, lengths, and numbers printed in the exam cut. "
            "Apply the governing law named in this walkthrough, then match the result to one of the four letters in the cut."
        )
    return r


def unique_chunks(reason: str) -> list[str]:
    why = [clean_speech(s) for s in sentences(reason)]
    why = [s for s in why if s]
    chunks: list[str] = []
    buf = ""
    for s in why:
        if buf and s[:80] == buf[:80]:
            continue
        if len(buf) + len(s) < 280:
            buf = (buf + " " + s).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)
    out = []
    seen = set()
    for c in chunks:
        key = c[:90]
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out[:4]


def governing_formula(stem: str, reason: str) -> tuple[str, str, str]:
    text = f"{stem} {reason}".lower()
    if "center of mass" in text or "centre of mass" in text:
        return (
            r"x_{\mathrm{cm}} = \dfrac{\sum m_i x_i}{\sum m_i}",
            "x cm",
            "the mass-weighted average position of the system",
        )
    if "gravitational field" in text:
        return r"g(r) = \dfrac{G M}{r^{2}}", "g of r", "the gravitational field at distance r from the center"
    if "gravitational force" in text or "newton's law of gravitation" in text:
        return r"F_g = \dfrac{G M m}{r^{2}}", "F g", "the gravitational force between two masses"
    if "spring" in text:
        return r"F_s = -k x", "F s", "the spring force, with k the spring constant and x the stretch from equilibrium"
    if "static friction" in text:
        return r"f_s \le \mu_s N", "f s", "static friction, at most mu s times the normal force N"
    if "kinetic friction" in text or "friction" in text:
        return r"f_k = \mu_k N", "f k", "kinetic friction, mu k times the normal force N"
    if "resistive" in text or "drag" in text:
        return r"F_r = -b v", "F r", "the resistive force, opposite the velocity"
    if "circular" in text or "centripetal" in text or "vertical circle" in text:
        return r"a_c = \dfrac{v^{2}}{r}", "a c", "the centripetal acceleration toward the center of the circle"
    if "period" in text and "orbit" in text:
        return r"T^{2} = \dfrac{4\pi^{2}}{G M} r^{3}", "T", "the orbital period for a circular orbit of radius r"
    return r"F_{\mathrm{net}} = m a", "F net", "the net force, equal to mass times acceleration"


def ask_sentence(stem: str) -> str:
    sents = sentences(re.sub(r"\s+", " ", stem))
    for s in reversed(sents):
        if re.match(
            r"^(Which|What|How|At which|Could|Does|If |In which|When |Where )\b",
            s,
            re.I,
        ):
            return s[:240]
    return (sents[-1] if sents else stem)[:240]


def clip_sentence(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    i = cut.rfind(".")
    return cut[: i + 1] if i > 80 else cut.rstrip() + "."


def first_read_step(n: int, stem: str) -> dict | None:
    """Problem-specific first look. No answer letter, no formula that solves it."""
    stem = re.sub(r"\s+", " ", clean_speech(stem))
    if len(stem) < 48:
        return None
    t = stem.lower()
    ask = ask_sentence(stem)
    vars_: list[dict] = []
    title = "Look at the setup"
    blurb = "Name the system before any formula"
    prompt = (
        "Before you compute, decide which objects belong in the system and which quantity "
        "the question is actually asking for."
    )

    def add(tex, say, meaning):
        if len(vars_) < 2:
            vars_.append({"tex": tex, "say": say, "meaning": meaning})

    only_neg_friction = t.count("friction") == 1 and "negligible friction" in t
    hanging_shape = (
        "held vertically" in t
        or "supported by the string" in t
        or ("folded" in t and "hang" in t)
    )
    gravity_setup = any(w in t for w in (
        "gravitational field", "gravitational force", "spherical shell", "planet",
        "satellite", "asteroid", "star", "rocket", "orbit", "kepler",
    ))
    third_law = (
        "third law" in t
        or "newton's third" in t
        or "newton’s third" in t
        or "action-reaction" in t
        or "action reaction" in t
    )
    forces_on_named = (
        "exert" in t
        and "force" in t
        and any(w in t for w in ("on the block", "on the box", "on the cart", "on the object"))
    )

    if "free-body" in t or "free body" in t:
        title = "Whose forces are in the diagram?"
        blurb = "One object, only real forces"
        prompt = (
            "A free-body diagram is for one object. Every arrow must be a force exerted ON that object, "
            "not its acceleration and not a force it exerts on something else. Check the figure for contact, "
            "strings, and whether friction is said to be negligible."
        )
        add(r"\sum \vec F", "net force", "the vector sum of forces drawn on the chosen object")
        add(r"\vec a", "a", "the object's acceleration; it is not itself a force arrow")
    elif "spring" in t:
        title = "Read the spring arrangement"
        blurb = "Series, parallel, cut, or identical"
        prompt = (
            "The figure's arrangement changes the effective k: series vs parallel, one spring vs two, "
            "whole spring vs a cut piece. Name that arrangement and whether the block is hanging at rest "
            "before writing a stretch formula."
        )
        add("k", "k", "the spring constant of one spring as drawn")
        add("x", "x", "the stretch or compression from that spring's unstretched length")
    elif "resistive" in t or "terminal" in t or "coffee filter" in t:
        title = "Which moment in the motion?"
        blurb = "Start, mid-fall, or terminal"
        prompt = (
            "Two kinds of force compete: a nearly constant gravitational force and a speed-dependent resistance. "
            "Decide whether the question is about t = 0, a given speed, or the long-time limit where acceleration "
            "has died away. Do not assume terminal speed unless the prompt is about that limit."
        )
        add(r"F_g", "F g", "the gravitational force, roughly constant near Earth")
        add(r"F_r", "F r", "the resistive force; it grows with speed and opposes the velocity")
    elif gravity_setup:
        title = "Inside, on, or outside?"
        blurb = "Where the test mass sits"
        prompt = (
            "Newton's inverse-square law is for a point outside a spherical mass. Inside a uniform sphere "
            "or a shell the field is different. For orbits, gravity is the force that supplies the needed "
            "inward acceleration — mark radii and periods in the figure before writing a ratio."
        )
        add("r", "r", "the distance from the relevant center to the location or orbit asked about")
        add("M", "M", "the mass that actually sources the field or holds the orbit")
    elif "center of mass" in t or "centre of mass" in t:
        title = "Name the system in the figure"
        blurb = "Which masses, which coordinate"
        prompt = (
            "Center of mass is a mass-weighted average of positions. Read the figure and decide which "
            "objects are in the system and whether the question wants x, y, or a distance from a marked point. "
            "If density is not uniform, a geometric midpoint is the wrong first guess — wait for the weighted integral or sum."
        )
        add(r"x_{\mathrm{cm}}", "x cm", "the mass-weighted average position of the system in the figure")
        if "density" in t or "linear density" in t:
            add(r"\lambda", "lambda", "linear density; check whether it is constant along the object")
        else:
            add(r"m_i", "m sub i", "each mass that belongs in the system, not masses outside it")
    elif hanging_shape:
        title = "Where does it hang?"
        blurb = "Support point and center of mass"
        prompt = (
            "In equilibrium, a hanging object's center of mass lies on the vertical line through the support. "
            "Look at the shape, mark that line, and only then match a diagram."
        )
        add("P", "P", "the support point where the string is attached")
        add(r"y_{\mathrm{cm}}", "y cm", "the center of mass; it hangs directly below P if the object is at rest")
    elif any(w in t for w in (
        "circular", "centripetal", "vertical circle", "conical", "loop-the-loop",
        "rotating platform", "rotating disk", "rotating cylinder",
    )):
        title = "Where on the path?"
        blurb = "Top, side, or constant speed"
        prompt = (
            "Centripetal acceleration always points toward the center of the circle. At the marked point, "
            "list which real forces have a radial component. Ask whether speed is constant: if the object "
            "is speeding up or slowing down there is also a tangential acceleration."
        )
        add(r"a_c", "a c", "the centripetal acceleration toward the center at the marked point")
        add(r"\sum F_r", "radial net force", "the combination of real forces along the radius, not a new 'centripetal force' from nowhere")
    elif ("friction" in t or "rough" in t) and not only_neg_friction:
        title = "Resting, about to slip, or sliding?"
        blurb = "Static vs kinetic"
        prompt = (
            "Static friction has a maximum; kinetic friction has a value once sliding has started. "
            "Read whether the object is at rest, at the threshold, or already moving, and which surfaces touch."
        )
        add(r"f_s", "f s", "static friction; at most mu s times the normal force, and only if needed")
        add("N", "N", "the normal force from the surface in the figure")
    elif third_law:
        title = "Which pair of forces?"
        blurb = "Same two objects, opposite directions"
        prompt = (
            "A third-law pair acts on two different objects. Same magnitude, opposite direction, same type. "
            "Weight and a normal force are not a third-law pair. Identify the two objects named in the stem."
        )
        add(r"\vec F_{12}", "F of 1 on 2", "the force object 1 exerts on object 2")
        add(r"\vec F_{21}", "F of 2 on 1", "the force object 2 exerts on object 1; this lives on a different free-body diagram")
    elif forces_on_named:
        title = "What can push on this object?"
        blurb = "Only contact or gravity"
        prompt = (
            "A force on the named object comes from something that touches it, or from Earth. "
            "If a new object is inserted, ask which contacts were lost and which remain. Gravity is still there."
        )
        add(r"\vec F_{\mathrm{on}}", "forces on the object", "only interactions that act on the object named in the question")
        add(r"\vec w", "weight", "Earth's gravitational force on that object; it does not require contact")
    elif "pulley" in t or (("hanging" in t or "suspended" in t) and "block" in t):
        title = "Which objects accelerate together?"
        blurb = "Two masses, one string"
        prompt = (
            "If two objects are tied by a string over a pulley, they usually share one magnitude of acceleration. "
            "Decide whether the pulley and string are massless, and whether friction is actually in play or called negligible."
        )
        add("T", "T", "the tension in the connecting string")
        add("a", "a", "the magnitude of acceleration the connected objects share, if the string does not stretch")
    else:
        if "incline" in t or "ramp" in t:
            add(r"\theta", "theta", "the incline angle; it sets how weight splits into parallel and perpendicular parts")
        if "tension" in t or "string" in t or "cord" in t or "rope" in t:
            add("T", "T", "the tension in the string, cord, or rope drawn in the figure")
        if "block" in t or "box" in t:
            add("m", "m", "the mass of the object whose motion or forces the question targets")
        if not vars_:
            add(r"\text{system}", "the system", "the object or objects the question is actually asking about")
        prompt = (
            "Lock in the setup from the exam cut before any algebra. Decide which object is the system, "
            "what is held constant, and what the question is comparing or finding. Do not pick a letter yet."
        )

    if not vars_:
        add(r"\text{system}", "the system", "the object or objects the question is actually asking about")

    explain = clip_sentence(
        f"{prompt} In words, the question is: {ask} Keep the exam cut in view; the figure often carries a length, "
        "angle, or contact that the sentence does not repeat.",
        720,
    )
    lead = clip_sentence(
        f"Look at Question {n} at the top. {prompt} Then read the question sentence again before you write a formula.",
        460,
    )
    return {
        "title": title,
        "blurb": blurb,
        "caption": f"{prompt.split('.')[0]}.",
        "lead": lead,
        "blocks": [{
            "vars": vars_,
            "explain": explain,
        }],
    }


def make_steps(n: int, stem: str, reason: str, answer: str) -> list[dict]:
    reason = usable_reason(reason)
    tex, say, meaning = governing_formula(stem, reason)
    chunks = unique_chunks(reason)
    others = [L for L in "ABCD" if L != answer]
    other_txt = ", ".join(others[:-1] + [f"and {others[-1]}"]) if len(others) > 1 else others[0]
    reason_clean = clean_speech(reason)
    if n == 3:
        read_step = {
            "title": "Read the four locations",
            "blurb": "Same three bars, four placements",
            "caption": "Each diagram is the same three-bar object on the xy-plane. Origin O is marked on every grid.",
            "lead": (
                "Look at the four location diagrams at the top. The three bars are identical and uniform. "
                "Only the placement on the xy-plane changes. Origin O is marked on each grid."
            ),
            "blocks": [{
                "vars": [
                    {"tex": "O", "say": "O",
                     "meaning": "the origin, marked on every location diagram"},
                    {"tex": r"\text{Location 1–4}", "say": "locations 1 through 4",
                     "meaning": "the same three-bar system set down in four different places"},
                ],
                "explain": (
                    "The question asks which placement puts the system's center of mass farthest from O. "
                    "The grids show the geometry; no extra lengths are written beside the figure."
                ),
            }],
        }
        goal_step = {
            "title": "Name what the question asks",
            "blurb": "Farthest center of mass from O",
            "caption": "The target is which location puts the center of mass farthest from the origin.",
            "lead": (
                "We are not asked for a numerical coordinate. Compare the four placements and pick the one "
                "whose center of mass is farthest from O."
            ),
            "blocks": [{
                "vars": [
                    {"tex": r"\vec r_{\mathrm{cm}}", "say": "r cm",
                     "meaning": "the position of the system's center of mass relative to origin O"},
                ],
                "explain": "Farthest from O means the largest distance from the origin to that center of mass.",
                "tex": r"d = \lvert \vec r_{\mathrm{cm}} \rvert",
                "speakFormula": "d is the distance from origin O to the center of mass.",
            }],
        }
    else:
        read_step = first_read_step(n, stem)
        goal_step = {
            "title": "Name what the question asks",
            "blurb": "Identify the target before formulas",
            "caption": "State the goal in words first. The formula in the next step is only a tool for that target.",
            "lead": "Next, name the quantity we must find or compare. Every later formula is only a tool for that target.",
            "blocks": [{
                "vars": [{"tex": r"\text{goal}", "say": "the goal",
                          "meaning": "what the multiple-choice question is asking you to decide"}],
                "explain": "Keep that goal in view so extra details in the figure do not pull you off the path.",
            }],
        }
    steps = ([read_step] if read_step else []) + [goal_step]
    steps.append({
            "title": "Use the governing idea",
            "blurb": "Name the symbols, then write the law",
            "caption": f"{say} is named first, then the law is written.",
            "lead": "Here is the law this problem needs. Each symbol is named before it appears in the formula.",
            "blocks": [{
                "vars": [{"tex": tex.split("=")[0].strip(), "say": say, "meaning": meaning}],
                "explain": "Write the law only after those symbols are named. Then apply it to the objects in the exam cut.",
                "tex": tex,
                "speakFormula": f"{say} means {meaning}. The law is written after those names.",
            }],
        })
    titles = ["Substitute the given values", "Carry the argument through"]
    blurbs = ["Plug the figure into the law", "Simplify to a result"]
    for i, chunk in enumerate(chunks[:2]):
        plugged = i == 0
        steps.append({
            "title": titles[i],
            "blurb": blurbs[i],
            "caption": chunk[:180],
            "lead": (
                "Copy every mass, length, and position from the exam cut into the law. "
                if plugged else
                "Stay with those substituted values and simplify until the result matches one choice."
            ),
            "blocks": [{
                "vars": [{"tex": tex.split("=")[0].strip(), "say": say, "meaning": meaning}],
                "explain": chunk,
            }],
        })
    leftover = chunks[2:]
    fail_explain = " ".join(leftover) if leftover else (
        f"Choices {other_txt} contradict the law or the figure: they use the wrong object, the wrong sign, or drop a mass that the cut includes."
    )
    steps.append({
        "title": "Why the other choices fail",
        "blurb": "Discard letters that break the law",
        "caption": f"Choices {other_txt} do not match the argument from the figure.",
        "lead": f"The remaining letters are {other_txt}. They fail because they disagree with the law or with a length, mass, or direction drawn in the exam cut.",
        "blocks": [{
            "vars": [{"tex": r"\text{not }"+answer, "say": f"not {answer}",
                      "meaning": f"choices {other_txt}, which do not match the solution"}],
            "explain": fail_explain[:500],
            "tex": rf"\text{{reject {other_txt}}}",
        }],
    })
    steps.append({
        "title": f"The answer is {answer}",
        "blurb": "Select the matching choice",
        "caption": f"Choice {answer} is the letter that matches the exam cut and the law.",
        "lead": f"The correct choice is {answer}. It is the only letter consistent with the figure and the argument above.",
        "blocks": [{
            "vars": [{"tex": rf"\text{{{answer}}}", "say": f"choice {answer}",
                      "meaning": "the letter that matches the solution"}],
            "explain": reason_clean[:450] if reason_clean else f"Choice {answer} is consistent with the walkthrough.",
            "tex": rf"\text{{answer {answer}}}",
            "speakFormula": f"The correct choice is {answer}.",
        }],
        "highlight": True,
    })
    return steps


def layout_parts():
    css = Q5[Q5.find("<style>") + len("<style>\n") : Q5.find("  </style>")]
    if Q5_ONLY not in css:
        raise SystemExit("Could not find Q5-only CSS to strip; refusing to slice layout")
    css = css.replace(Q5_ONLY, "")
    css = css.rstrip() + "\n" + PAGE_CSS
    js = Q5[Q5.find("    const $ = (id)") :]
    pre = js[: js.find("    function choiceRow")]
    mid = js[js.find("    function words(text)") : js.find("    function renderVisual")]
    rest = js[js.find("    function paintStep(i)") :]
    rest = rest.replace(
        '        return `<div class="eq-block">${meaning}${why}<p class="formula-label">Formula</p><div class="math-line${ok ? " ok" : ""}">${renderTex(block.tex, true)}</div></div>`;',
        '        const formula = block.tex\n'
        '          ? `<p class="formula-label">Formula</p><div class="math-line${ok ? " ok" : ""}">${renderTex(block.tex, true)}</div>`\n'
        '          : "";\n'
        '        return `<div class="eq-block">${meaning}${why}${formula}</div>`;',
    )
    assert_layout("<style>\n" + css + "\n</style>", "template")
    if "function paintStep" not in rest:
        raise SystemExit("player JS truncated")
    return css, pre, mid, rest


CSS, JS_PRE, JS_MID, JS_REST = layout_parts()


def build_html(n, total, stem, choices, answer, page, steps) -> str:
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
    fig = f"../figures/q{n:02d}.png"
    ans = f"../figures/a{n:02d}.png"
    css = CSS.replace("#choiceA", f"#choice{answer}")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Unit 2 Q{n} · Walkthrough</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.css" />
  <style>
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
    <section class="problem-bar exam" id="problemBar" aria-label="Problem statement">
      <div class="exam-frame">
        <img class="exam-cut" src="{fig}" alt="Question {n} exact exam item, including figure and choices" />
      </div>
      <div class="exam-meta">
        <div class="problem-tools">
        <h2><a href="{fig}" target="_blank" rel="noopener noreferrer">The problem</a><span class="dot"> · </span><a href="{ans}" target="_blank" rel="noopener noreferrer">The answer is</a></h2>
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
    const STEPS = {json.dumps(steps, ensure_ascii=False, indent=6)};
{JS_PRE}
    const ANSWER = {json.dumps(answer)};
    function choiceRow(winner) {{
      return ["A", "B", "C", "D"].map((letter) =>
        `<span class="choice${{winner && letter === ANSWER ? " win" : ""}}" id="choice${{letter}}">(${{letter}})</span>`
      ).join("");
    }}
{JS_MID}
    function renderVisual(step) {{
      /* Exam cut lives only in the sticky bar. Do not repeat it on the stage. */
    }}
{JS_REST}"""
    assert_layout(html, f"Q{n}")
    if f"Question {n}" not in html:
        raise SystemExit(f"Q{n} title missing")
    return html


def toc_row(n: int, stem: str) -> str:
    if n in CUSTOM_TOC:
        topic, blurb = CUSTOM_TOC[n]
        return f"""        <tr>
          <td class="num">Question {n}</td>
          <td>
            <div class="topic">{topic}</div>
            <p class="blurb">{blurb}</p>
          </td>
          <td><a class="open" href="q{n}/index.html">Open walkthrough</a></td>
        </tr>"""
    blurb = re.sub(r"\s+", " ", stem)
    if len(blurb) > 160:
        blurb = blurb[:157] + "..."
    topic = escape(blurb.split(".")[0][:80])
    return f"""        <tr>
          <td class="num">Question {n}</td>
          <td>
            <div class="topic">{topic}</div>
            <p class="blurb">{escape(blurb)}</p>
          </td>
          <td><a class="open" href="q{n}/index.html">Open walkthrough</a></td>
        </tr>"""


def write_toc(rows: list[str]) -> None:
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
      <p class="back"><a href="../index.html">All units</a></p>
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


def patch_nav(n: int, total: int) -> None:
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


def main() -> None:
    print("Extracting PDFs...")
    q_items = split_items(pdf_text(Q_PDF))
    s_items = split_items(pdf_text(S_PDF))
    pages = question_pages()
    total = max(q_items)
    print(f"{total} questions, pages mapped {len(pages)}")
    print("Cropping exact exam items...")
    crop_all(force=False)
    print("figures", len(list(FIG_DIR.glob("q[0-9][0-9].png"))))
    toc = []
    for n in range(1, total + 1):
        qbody = q_items.get(n, s_items.get(n, ""))
        stem, choices = parse_choices(qbody)
        if not stem:
            stem, choices = parse_choices(s_items.get(n, ""))
        answer, reason = parse_solution(s_items.get(n, qbody))
        page = pages.get(n, 1)
        toc.append(toc_row(n, stem or f"Question {n}"))
        if n in KEEP:
            continue
        dest = UNIT2 / f"q{n}"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "audio").mkdir(exist_ok=True)
        (dest / "generate-audio.mjs").write_text(AUDIO_GEN)
        steps = make_steps(n, stem, reason, answer)
        html = build_html(n, total, stem, choices, answer, page, steps)
        (dest / "index.html").write_text(html)
        if n % 10 == 0 or n == 3:
            print("built", n, "bytes", len(html))
    write_toc(toc)
    for n in range(1, total + 1):
        patch_nav(n, total)
        assert_layout((UNIT2 / f"q{n}" / "index.html").read_text(), f"final Q{n}")
    prompt = (ROOT / "tools" / "PROMPT.md").read_text()
    prompt = re.sub(r"currently `unit2-q\d+/`", "currently `unit2/q90/`", prompt)
    (ROOT / "tools" / "PROMPT.md").write_text(prompt)
    print("TOC rows", len(toc), "done")


def load_html_steps(html: str) -> tuple[list, int, int]:
    start = html.index("const STEPS = ")
    end = html.index("\n    const $ = (id)", start)
    raw = html[start + len("const STEPS = ") : end].strip().rstrip(";")
    return json.loads(raw), start, end


def is_empty_read_step(step: dict) -> bool:
    if not step:
        return True
    blocks = step.get("blocks") or []
    title = step.get("title", "")
    if title == "Read the problem" and not blocks:
        return True
    return not blocks


def patch_empty_first_steps(preview: bool = False) -> None:
    """Fill or drop empty first steps on generated pages. Does not rewrite KEEP or Q3."""
    q_items = split_items(pdf_text(Q_PDF))
    s_items = split_items(pdf_text(S_PDF))
    filled = dropped = skipped = 0
    samples = []
    for n in range(1, 91):
        if n in KEEP or n == 3:
            skipped += 1
            continue
        path = UNIT2 / f"q{n}" / "index.html"
        html = path.read_text()
        steps, start, end = load_html_steps(html)
        first = steps[0] if steps else {}
        if not is_empty_read_step(first):
            skipped += 1
            continue
        qbody = q_items.get(n, s_items.get(n, ""))
        stem, _choices = parse_choices(qbody)
        if not stem:
            stem, _choices = parse_choices(s_items.get(n, ""))
        read_step = first_read_step(n, stem)
        if read_step:
            steps[0] = read_step
            filled += 1
            action = "fill"
        else:
            steps = steps[1:]
            dropped += 1
            action = "drop"
        samples.append((n, action, (read_step or {}).get("title", "(removed)"), stem[:90].replace("\n", " ")))
        if preview:
            continue
        dumped = json.dumps(steps, ensure_ascii=False, indent=6)
        path.write_text(html[:start] + "const STEPS = " + dumped + ";" + html[end:])
        assert_layout(path.read_text(), f"first-step Q{n}")
    print(f"empty-first filled {filled} dropped {dropped} skipped {skipped}")
    for n, action, title, stem in samples:
        if n in {6, 8, 10, 12, 20, 25, 40, 50, 64, 73, 82, 89, 90} or action == "drop":
            print(f"  Q{n} {action}: {title}")
            print(f"      {stem}")


if __name__ == "__main__":
    import sys
    if "--patch-first" in sys.argv:
        patch_empty_first_steps(preview="--preview" in sys.argv)
    else:
        main()
