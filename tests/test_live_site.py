#!/usr/bin/env python3
"""Smoke-test the published GitHub Pages site by following home → unit → walkthrough."""
from __future__ import annotations

import os
import re
import unittest
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE_URL = os.environ.get(
    "BASE_URL", "https://sethusrinivasan.github.io/ap-physics/"
)


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.headings: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.html = ""
        self.final_url = ""
        self._in_title = False
        self._heading_tag: str | None = None
        self._heading_parts: list[str] = []
        self._link_href: str | None = None
        self._link_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag in {"h1", "h2", "h3"}:
            self._heading_tag = tag
            self._heading_parts = []
        elif tag == "a":
            self._link_href = attrs_d.get("href") or ""
            self._link_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == self._heading_tag:
            self.headings.append("".join(self._heading_parts).strip())
            self._heading_tag = None
        elif tag == "a" and self._link_href is not None:
            self.links.append(("".join(self._link_parts).strip(), self._link_href))
            self._link_href = None

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._heading_tag:
            self._heading_parts.append(data)
        if self._link_href is not None:
            self._link_parts.append(data)


def fetch(url: str) -> Page:
    req = Request(url, headers={"User-Agent": "ap-physics-live-site-test"})
    try:
        with urlopen(req, timeout=20) as resp:
            status = getattr(resp, "status", 200)
            html = resp.read().decode("utf-8", "replace")
            final_url = resp.geturl()
    except HTTPError as exc:
        raise AssertionError(f"{url} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise AssertionError(f"{url} failed: {exc.reason}") from exc
    if status >= 400:
        raise AssertionError(f"{url} returned HTTP {status}")
    page = Page()
    page.html = html
    page.final_url = final_url
    page.feed(html)
    return page


def href_named(page: Page, name: str) -> str:
    for text, href in page.links:
        if name.lower() in text.lower():
            return href
    raise AssertionError(f'no link containing "{name}" on {page.title!r}')


def href_for_question(page: Page, n: int) -> str:
    pat = re.compile(rf"(?:^|[^\d])q{n}(?:[^\d]|$)")
    for text, href in page.links:
        if "open walkthrough" in text.lower() and pat.search(href):
            return href
    raise AssertionError(f"no Question {n} walkthrough link on {page.title!r}")


def open_unit() -> Page:
    home = fetch(BASE_URL)
    return fetch(urljoin(home.final_url, href_named(home, "Open unit")))


class LiveSiteTest(unittest.TestCase):
    def test_home_opens_unit_and_walkthrough(self) -> None:
        home = fetch(BASE_URL)
        self.assertIn("AP Physics C", home.title)
        self.assertTrue(
            any("AP Physics C walkthroughs" in h for h in home.headings),
            home.headings,
        )

        unit = fetch(urljoin(home.final_url, href_named(home, "Open unit")))
        self.assertTrue(any("Unit 2" in h for h in unit.headings), unit.headings)

        walk = fetch(urljoin(unit.final_url, href_named(unit, "Open walkthrough")))
        self.assertTrue(
            any(text == "The problem" for text, _href in walk.links),
            walk.links[:8],
        )
        self.assertIn("problem-bar", walk.html)

    def test_home_opens_question_1(self) -> None:
        unit = open_unit()
        q1 = fetch(urljoin(unit.final_url, href_for_question(unit, 1)))
        self.assertRegex(q1.title, r"(?:\bQ1\b|Question 1)")
        self.assertTrue(any(text == "The problem" for text, _href in q1.links))
        self.assertTrue(any(text == "The answer is" for text, _href in q1.links))
        self.assertTrue(any(text == "Contents" for text, _href in q1.links))
        self.assertTrue(any(text == "Next problem" for text, _href in q1.links))
        self.assertIn("problem-bar", q1.html)
        self.assertIn('id="playBtn"', q1.html)
        self.assertIn('id="stage"', q1.html)

        q2 = fetch(urljoin(q1.final_url, href_named(q1, "Next problem")))
        self.assertRegex(q2.title, r"(?:\bQ2\b|Question 2)")

        toc = fetch(urljoin(q1.final_url, href_named(q1, "Contents")))
        self.assertTrue(any("Unit 2" in h for h in toc.headings), toc.headings)


if __name__ == "__main__":
    unittest.main()
