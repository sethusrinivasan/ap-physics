#!/usr/bin/env python3
"""Smoke test for Unit 4 walkthrough pages and navigation."""
from __future__ import annotations

import os
import re
import unittest
from urllib.parse import urljoin
from tests.test_live_site import BASE_URL, fetch, href_named, href_for_question


class Unit4SiteTest(unittest.TestCase):
    def test_home_opens_unit4_and_walkthrough(self) -> None:
        home = fetch(BASE_URL)
        unit4_link = None
        for text, href in home.links:
            if "unit4" in href:
                unit4_link = href
                break
        self.assertIsNotNone(unit4_link, "unit4 link found on home page")

        unit4 = fetch(urljoin(home.final_url, unit4_link))
        self.assertIn("Unit 4", unit4.title)
        self.assertTrue(any("Unit 4" in h for h in unit4.headings))

        # Check Q1
        q1_href = href_for_question(unit4, 1)
        q1 = fetch(urljoin(unit4.final_url, q1_href))
        self.assertIn("Unit 4 Question 1", q1.title)
        self.assertTrue(any(text == "The problem" for text, _ in q1.links))
        self.assertTrue(any(text == "The answer is" for text, _ in q1.links))
        self.assertTrue(any(text == "Contents" for text, _ in q1.links))
        self.assertTrue(any(text == "Next problem" for text, _ in q1.links))
        self.assertIn("problem-bar", q1.html)

        # Check Q2 via Next problem
        q2 = fetch(urljoin(q1.final_url, href_named(q1, "Next problem")))
        self.assertIn("Unit 4 Question 2", q2.title)

        # Check Q36
        q36_href = href_for_question(unit4, 36)
        q36 = fetch(urljoin(unit4.final_url, q36_href))
        self.assertIn("Unit 4 Question 36", q36.title)
        self.assertTrue(any(text == "Previous problem" for text, _ in q36.links))
        self.assertIn("Next problem", q36.html)


if __name__ == "__main__":
    unittest.main()
