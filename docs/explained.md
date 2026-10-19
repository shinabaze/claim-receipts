# Receipts, explained from scratch

## The idea

When an article says "According to X, 91% of households live near a bus stop", a reader has to
trust that X really said it. A receipt removes the trust: a screenshot of X's own page, with the
number marked, right under the sentence. If no page says it, the claim gets no receipt and is
listed as unverified. Nothing is shown as proved that isn't.

The hard part is not the screenshot. It is deciding whether a page really says what the sentence
says.

## Step 1: find the claims

A claim is a sentence with a statistic and a named source. Statistics are percentages, money,
multipliers ("3x") and counts with a scale word ("470 million"). Years, list numbers and durations
are not statistics. The source is read from shapes like "According to X", "per X", "X found" or
"(X, 2026)".

Two kinds of sentence look like claims and are not:

- A worked example ("for example", "illustrative", "imagine"). It describes a case, not the world.
- "X reports 1 order for $100". "Reports" here is a step in a process, not a finding, so this
  shape only counts when the number is a rate or a scale, or the sentence names a metric.

## Step 2: find the number on the page

`41 percent` has to match `41%`, `41.0%` and `41 per cent`, but not `141%`. `$5.8 billion` has to
match `$5.8B` and `5.8bn`. `stat_pattern` builds one regex per number for that.

## Step 3: check that our words describe that same number

This is where the first version went wrong. It accepted a page when the number and two of our words
were in the same block. Three pages fooled it. Here they are in the same shape, with the topic
changed:

| Our sentence | The page | Why it is not proof |
|---|---|---|
| 41 percent of school-run trips | stat cards: "41% Higher Bus Ridership", "80% Of School-Run Trips By Car" | "school-run trips" describes the 80% |
| 41 percent of commuters cycle to work | "...than commuters who drive to work. Yet 41% of households own no bike" | the words are in the sentence before |
| 50% dock availability | "...bike-share lives or dies on dock availability... (e.g., 50% walking, 50% bus)" | a split of credit, not availability |

So now each number gets a window: back to the previous statistic or the start of its sentence,
forward to the next statistic or the end of its sentence. Only words inside the window count. In a
row of stat cards, each card is judged on its own, because the row's text runs one card into the
next.

## Step 4: how much evidence is enough

- Words from our sentence count 1. Words from the rest of our paragraph count 0.5. Words that sit
  next to almost any number ("rate", "total", "year") count half of that.
- On the named source's own page (its address or title carries the name) a score of 1 is enough.
  Anywhere else it takes 2.
- A round number (41%, 50%, $100) is on half the pages on the internet, so it also needs at least
  one specific word of our sentence. A distinctive one (3.2%, 740 million) needs less.

## Worked by hand

Our sentence: "the network loses a 3.2% share of trips to late-running buses and missed
connections". The page: "On-time running has held near 96.8% across the network. The remaining
3.2% of trips is lost to late-running buses, missed connections and closures."

1. `3.2%` is on the page.
2. Window: back to the sentence start ("The remaining"), forward to the end ("...and closures").
   The 96.8% and its sentence are outside.
3. Our words inside it: trip, late-running, bus, missed, connection. Score 5.
4. 3.2% is distinctive and the page is the named source, so it needs 0.5. Proved.

## Step 5: the crop

`capture.py` opens the page in a real browser, runs the same rules on what is actually visible,
hides anything fixed or sticky that could cover the passage, and screenshots it. The number's
position comes back as boxes, and the highlight is drawn over the image with CSS. The screenshot
itself is never edited.
