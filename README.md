# claim-receipts

Put the source's own sentence next to every statistic you quote, or say you can't.

Give it an article. It finds every sentence that quotes a number and names a source ("According
to X, 91% of..."), then checks a source page: does that page really say this number about this
thing? If it does, an optional browser step screenshots the passage and returns where the number
sits, so you can mark it. If it doesn't, you get the reason, and the claim stays unverified.

About 350 lines of Python for the rules, standard library only, Python 3.10+. The screenshot step
(another 130 lines) needs Playwright.

I built the first version for the blog and the videos of my studio, where every figure we quote
has to show its source on screen. Its first versions "proved" three claims with pages that never said
them. This repo is that matcher rewritten, with those three pages kept as tests that must fail.

**Run it** (no network; the pages are saved in `examples/pages`):

```bash
python examples/demo.py
python -m unittest discover -s tests -t .
```

With Playwright installed (`pip install playwright && python -m playwright install chromium`):

```bash
python examples/demo.py --capture      # writes examples/out/receipts.html
```

**Use it:**

```python
from claim_receipts import find_claims, check

for claim in find_claims(article_html):
    result = check(claim, source_html, url=source_url)
    print(claim["sentence"], result["found"], result.get("reason"))
```

## How it works

```
article ─► find_claims ─► "According to X, 91% of households live within 400 m of a bus stop"
                               │ the number in all its printed forms: 91%, 91.0%, 91 percent
source page ─► blocks ─────────┤
                               ▼
              for each block holding the number (smallest first):
                 window = the number's own description, cut at the next statistic and the sentence
                 our words in the window, weighed ──► enough? ──► proof, or the reason it isn't
                               │
                     (optional) browser: crop the passage, return the number's boxes
```

The rules, with a claim worked through by hand: [docs/explained.md](docs/explained.md).

## A worked example

`python examples/demo.py` checks a four-claim article against two pages, a transport survey and an
unrelated blog post about bike-share:

```
According to Harbour City Transport, 91% of households live within 400 metres of a bus stop.
  source named: Harbour City Transport   numbers: 91%
  PROVED by https://harbourcitytransport.example/travel-survey-2026
    passage: 91% Households Within 400 m Of A Bus Stop
    words beside 91%: bus, household, stop

According to Harbour City Transport's 2026 survey, the network loses a 3.2% share of trips to late-running buses and missed connections.
  source named: Harbour City Transport   numbers: 3.2%
  PROVED by https://harbourcitytransport.example/travel-survey-2026
    passage: On-time running has held near 96.8% across the network. The remaining 3.2% of trips is lost to late-running buses, missed connections and closures.
    words beside 3.2%: bus, connection, late-running, missed, trip

According to Harbour City Transport, cyclists make roughly 41 percent of all school-run trips from just 5.3 percent of households.
  source named: Harbour City Transport   numbers: 41 percent, 5.3 percent
  not harbourcitytransport.example: the number is on the page, but not described by our words
  not bikeshare-notes.example: the number is not on the page
  -> no receipt. Shown as unverified, never as proved.

Harbour City Transport data shows that a working bike-share scheme needs 50%+ dock availability.
  source named: Harbour City Transport   numbers: 50%
  not harbourcitytransport.example: the number is not on the page
  not bikeshare-notes.example: the number is on the page, but not described by our words
  -> no receipt. Shown as unverified, never as proved.
```

The third claim is the interesting one. The survey page has a "41%" card and the words
"school-run trips", but the words belong to the 80% card next to it. An earlier version of this
code accepted exactly that.

With `--capture`, the two proofs become screenshots of the page with "91%" and "3.2%" marked.

## What I learned

- **"The number is on the page" proves nothing.** Pages on one topic repeat the same few round
  numbers and the same words. The first version checked for both in one block and accepted three
  pages that said something else.
- **Each number owns its own words.** Cutting the window at the neighbouring statistic and at the
  sentence end fixed all three. Writing this version I found a fourth case, the card before the
  number lending its words, so the smallest block that holds the number decides now.
- **A refusal needs a reason.** "Not described by our words" and "not on the page" lead to
  different fixes: the first means look for another page, the second often means the sentence
  misquotes its source.
- **Never paint on the evidence.** The highlight is CSS on top of an untouched screenshot, so the
  image is still a true copy of what the page showed.

## Limits

- It checks pages you give it. Finding candidate pages (a search API, the sources a writer used)
  is up to you.
- English only, and the stemming is crude: plurals are cut and that's it.
- Word overlap is not understanding. A page that uses our words to say the opposite ("41% of
  commuters do *not* cycle") passes. Read the receipt before you publish it.
- The offline reader ignores CSS, so it can't tell hidden text from visible text. The browser
  step can, and only judges what is on screen.
- Some sites block headless browsers or put the text behind a consent wall. Those come back as
  refusals, not receipts.

## Files

```
claim_receipts/  claims.py  numbers.py  match.py  page.py  capture.py (optional, Playwright)
tests/           unittest, including the pages that must be refused
examples/        demo.py, article.html, pages/
docs/            explained.md, decisions.md
```

MIT licence. Copyright 2026 Shinabaze Ajiya.
