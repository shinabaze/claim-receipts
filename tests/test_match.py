import unittest

from claim_receipts import check, find_claims
from claim_receipts.match import window
from claim_receipts.page import is_named_source, read_html

from tests.fixtures import CASES, page


def claim_for(sentence):
    found = find_claims("<p>%s</p>" % sentence)
    assert found, "not read as a claim: " + sentence
    return found[0]


class Proof(unittest.TestCase):
    def test_every_fixture(self):
        for case in CASES:
            with self.subTest(case["name"]):
                r = check(claim_for(case["sentence"]), page(case))
                self.assertEqual(r["found"], case["proves"], r)

    def test_a_refusal_says_why(self):
        r = check(claim_for(CASES[0]["sentence"]), page(CASES[0]))
        self.assertEqual(r["reason"], "the number is on the page, but not described by our words")
        absent = check(claim_for(CASES[0]["sentence"]), "<p>Nothing to see in this paragraph at all.</p>")
        self.assertEqual(absent["reason"], "the number is not on the page")

    def test_a_proof_points_at_the_number(self):
        case = CASES[5]
        r = check(claim_for(case["sentence"]), page(case))
        self.assertEqual(r["passage"][r["start"]:r["end"]], "3.2%")
        self.assertIn("connection", r["words"])

    def test_the_smallest_block_wins(self):
        case = CASES[4]
        r = check(claim_for(case["sentence"]), page(case))
        self.assertTrue(r["passage"].startswith("91%"))
        self.assertNotIn("Fewer Car Trips", r["passage"])

    def test_an_unnamed_page_needs_more_evidence(self):
        # one specific word is enough on the source's own page, not on a stranger's
        sentence = "According to Harbour City Transport, 41 percent of commuters cycle to work."
        body = "<p>Across the region 41% of commuters now travel by train on weekdays.</p>"
        named = check(claim_for(sentence), "<title>Harbour City Transport</title>" + body)
        other = check(claim_for(sentence), "<title>A blog</title>" + body)
        self.assertTrue(named["found"])
        self.assertFalse(other["found"])


class Window(unittest.TestCase):
    def test_the_next_statistic_owns_what_follows_it(self):
        text = "41% Higher Bus Ridership 80% Of School-Run Trips"
        self.assertEqual(window(text, 0, 3).split(), ["higher", "bus", "ridership"])

    def test_the_window_stops_at_the_sentence(self):
        text = "Commuters who drive to work. Yet 41% of households own no bike."
        start = text.index("41%")
        self.assertNotIn("work", window(text, start, start + 3))


class Page(unittest.TestCase):
    def test_blocks_hold_their_children(self):
        title, blocks = read_html("<title>T</title><div><p>One <b>two</b></p><p>three</p></div><script>x</script>")
        self.assertEqual(title, "T")
        self.assertIn("One two", blocks)
        self.assertIn("One two three", blocks)
        self.assertFalse(any("x" == b for b in blocks))

    def test_named_source(self):
        self.assertTrue(is_named_source("https://www.harbourcitytransport.example/survey", "", "Harbour City Transport"))
        self.assertTrue(is_named_source("https://news.example/a", "Harbour City Transport survey", "Harbour City Transport"))
        self.assertFalse(is_named_source("https://news.example/a", "City news", "Harbour City Transport"))


if __name__ == "__main__":
    unittest.main()
