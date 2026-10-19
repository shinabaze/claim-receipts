"""Six source pages and the sentence each is supposed to prove.

The first three `False` cases are the shapes of false receipts an earlier version of this code
accepted: the number was on the page, and so were our words, but the words described a different
number. The fourth is the same mistake one card earlier, found while writing this version.
"""

NAMED_TITLE = "Harbour City Transport - Travel Survey 2026"
OTHER_TITLE = "Notes on running a bike-share scheme"

CASES = [
    {
        "name": "refuses a stat card whose neighbour holds our words",
        "sentence": "According to Harbour City Transport, cyclists make roughly 41 percent of all school-run "
                    "trips from just 5.3 percent of households.",
        "title": NAMED_TITLE,
        "body": "<div class=cards><div class=s><b>26%</b> More Weekend Rides</div>"
                "<div class=s><b>41%</b> Higher Bus Ridership (Peak)</div>"
                "<div class=s><b>80%</b> Of School-Run Trips By Car</div></div>",
        "proves": False,
    },
    {
        "name": "refuses our words from the sentence before the number",
        "sentence": "According to Harbour City Transport, 41 percent of commuters cycle to work at least once a week.",
        "title": NAMED_TITLE,
        "body": "<p>People who cycle get 3x more weekly exercise than commuters who drive to work. "
                "Yet 41% of households own no bike at all.</p>",
        "proves": False,
    },
    {
        "name": "refuses a round number in an unrelated split",
        "sentence": "Harbour City Transport data shows that a working bike-share scheme needs 50%+ dock availability.",
        "title": OTHER_TITLE,
        "body": "<p>A bike-share scheme lives or dies on dock availability, and most cities track it by hand. "
                "Tools that handle this: none out of the box. You upload the ride logs and define your own "
                "rules for splitting credit between modes (e.g., 50% walking, 50% bus).</p>",
        "proves": False,
    },
    {
        "name": "refuses our words from the card before the number",
        "sentence": "According to Harbour City Transport, 41 percent of commuters cycle to work at least once a week.",
        "title": NAMED_TITLE,
        "body": "<div class=cards><div class=s><b>12%</b> Of Commuters Cycle To Work</div>"
                "<div class=s><b>41%</b> Higher Bus Ridership (Peak)</div></div>",
        "proves": False,
    },
    {
        "name": "accepts a stat card that says the same thing",
        "sentence": "According to Harbour City Transport, 91% of households live within 400 metres of a bus stop.",
        "title": NAMED_TITLE,
        "body": "<div class=cards><div class=s><b>91%</b> Households Within 400 m Of A Bus Stop</div>"
                "<div class=s><b>40%</b> Fewer Car Trips Since 2020</div></div>",
        "proves": True,
    },
    {
        "name": "accepts the same fact in different prose",
        "sentence": "According to Harbour City Transport's 2026 survey, the network loses a 3.2% share of trips to "
                    "late-running buses and missed connections.",
        "title": NAMED_TITLE,
        "body": "<p>On-time running has held near 96.8% across the network. The remaining 3.2% of trips is lost "
                "to late-running buses, missed connections and closures.</p>",
        "proves": True,
    },
]


def page(case):
    return ("<html><head><title>%s</title><style>.s{display:inline-block;width:30%%;margin:8px;"
            "font:16px sans-serif}b{display:block;font-size:32px}</style></head>"
            "<body style='font:16px/1.5 sans-serif;max-width:720px;margin:40px auto'>%s</body></html>"
            % (case["title"], case["body"]))
