#!/usr/bin/env python3
"""Browser smoke test: click from the home page to Question 1 and check nav."""
from __future__ import annotations

import os
import re
import unittest

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:  # pragma: no cover
    expect = None
    sync_playwright = None

BASE_URL = os.environ.get(
    "BASE_URL", "https://sethusrinivasan.github.io/ap-physics/"
)
Q1_ROW = re.compile(r"^Question 1$")
Q1_TITLE = re.compile(r"Q1|Question 1")
Q2_TITLE = re.compile(r"Q2|Question 2")


@unittest.skipUnless(
    sync_playwright is not None,
    "Playwright is not installed. From the repo root run ./run-tests.sh",
)
class BrowserLiveSiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._pw = sync_playwright().start()
        cls.browser = cls._pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls._pw.stop()

    def test_browser_navigates_home_to_question_1(self) -> None:
        page = self.browser.new_page()
        page.set_default_timeout(15_000)
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded")
            expect(
                page.get_by_role("heading", name="AP Physics C walkthroughs")
            ).to_be_visible()

            page.get_by_role("link", name="Open unit").click()
            expect(page.get_by_role("heading", name=re.compile(r"Unit 2"))).to_be_visible()

            page.locator("tr").filter(
                has=page.locator("td.num", has_text=Q1_ROW)
            ).get_by_role("link", name="Open walkthrough").click()
            expect(page).to_have_title(Q1_TITLE)
            expect(page.get_by_role("link", name="The problem")).to_be_visible()
            expect(page.get_by_role("link", name="The answer is")).to_be_visible()
            expect(page.locator(".problem-bar")).to_be_visible()
            expect(page.locator("#playBtn")).to_be_visible()
            expect(page.get_by_role("link", name="Contents")).to_be_visible()

            page.get_by_role("link", name="Next problem").click()
            expect(page).to_have_title(Q2_TITLE)

            page.get_by_role("link", name="Contents").click()
            expect(page.get_by_role("heading", name=re.compile(r"Unit 2"))).to_be_visible()
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
