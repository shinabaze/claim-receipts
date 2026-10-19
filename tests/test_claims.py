import re
import unittest

from claim_receipts.claims import find_claims
from claim_receipts.numbers import stat_pattern


class Claims(unittest.TestCase):
    def count(self, text):
        return len(find_claims("<p>%s</p>" % text))

    def test_an_attributed_rate_is_a_claim(self):
        self.assertEqual(self.count("According to Harbour City Transport, 52% of trips are under five kilometres."), 1)

    def test_a_worked_example_naming_a_shop_is_not(self):
        self.assertEqual(self.count("Shopwise reports 1 actual order for $100."), 0)

    def test_an_illustrative_paragraph_is_skipped(self):
        self.assertEqual(self.count("Running costs settle at an illustrative $47 via Pedalco."), 0)

    def test_recent_data_is_not_a_source(self):
        self.assertEqual(self.count("Recent data shows a 40% lift."), 0)

    def test_a_named_price_is_a_claim(self):
        self.assertEqual(self.count("Velodata reports that a city bike now costs anywhere from $450 to $900."), 1)

    def test_the_source_loses_its_possessive(self):
        c = find_claims("<p>According to Pedalco's 2026 benchmarks, repair prices have risen by 40% this year.</p>")
        self.assertEqual(c[0]["source"], "Pedalco")
        self.assertEqual(c[0]["stats"], ["40%"])

    def test_plain_text_articles_work_too(self):
        text = "First paragraph.\n\nAccording to Harbour City Transport, 52% of trips are short.\n"
        self.assertEqual(len(find_claims(text)), 1)

    def test_html_entities_are_decoded(self):
        c = find_claims("<p>According to Smith &amp; Rowe, rents rose 7.5% in a year.</p>")
        self.assertEqual(c[0]["source"], "Smith & Rowe")


class StatPatterns(unittest.TestCase):
    def check(self, stat, text, want):
        self.assertEqual(bool(re.search(stat_pattern(stat), text, re.I)), want, (stat, text))

    def test_printed_forms(self):
        self.check("41 percent", "drove 41% of trips", True)
        self.check("$5.8 billion", "hit $5.8B in Q1", True)
        self.check("470 million", "470 million rides", True)
        self.check("3.2%", "the remaining 3.2 % loss", True)
        self.check("$1,200", "costs $1200 a year", True)
        self.check("3x", "three times? no, 3 times more", True)

    def test_never_inside_a_bigger_number(self):
        self.check("12%", "112% growth", False)
        self.check("$100", "$1000 spend", False)
        self.check("3.2%", "13.2% loss", False)


if __name__ == "__main__":
    unittest.main()
