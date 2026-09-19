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
[![Made with Cursor](https://img.shields.io/badge/Made_with-Cursor-000000?logo=cursor&logoColor=white)](https://cursor.com)

Step-by-step interactive solutions for AP Physics C topic questions. Each problem keeps the exam item on screen, names every symbol before the formula, and plays English audio through the derivation to the answer choice.

Unit 2 is 90 problems covering center of mass, Newton’s laws, gravity, friction, springs, drag, and circular motion.

This site was created with [Cursor](https://cursor.com). Questions and official solution images come from AP Physics C problem sets shared by a school teacher. They remain the property of the College Board. This project is an independent study aid and is not affiliated with or endorsed by the College Board.

- [`index.html`](index.html) — unit list (GitHub Pages home)
- [`unit2/`](unit2/) — Unit 2 TOC, problems `q1`–`q90`, and exam/solution crops
- [`tools/`](tools/) — build scripts and authoring prompt
- [`tests/`](tests/) — HTTP and Playwright smoke tests
- [`LICENSE`](LICENSE) — MIT

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

HTTP-only checks (no Chromium): `python3 -m unittest tests.test_live_site -v`

On Debian/Ubuntu, a full venv needs the `python3-venv` package. `./run-tests.sh` still works without it: it bootstraps pip in `.venv` or falls back to `pip --user`. GitHub Actions runs `./run-tests.sh` as well as CodeQL, OpenSSF Scorecard, and dependency review.
