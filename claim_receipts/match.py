"""Does this page prove that sentence? The rules.

A page proves a claim only when the SAME number is described by OUR words. Being on the page is
not enough: a page about one topic is full of numbers, and the one you want is often there
describing something else. So the words are counted only in the number's own window: back to the
previous statistic or the start of its sentence, forward to the next statistic or the end of its
sentence. Each statistic owns its own description.
"""
import re

from .numbers import STAT_RE, distinctive, stat_pattern
from .page import name_tokens

STOP = set((
    "the and for with your you are how why what when this that from our its into can will not but all new use "
    "using about than more most they their them have has was were did does just now here there who which out get "
    "got also over only per each such been being very some any may might could would should while where after "
    "before across between through during within without based according reports report found shows study data "
    "survey research percent roughly nearly almost around about least").split())

# Words that sit next to almost any number. They count half.
GENERIC = {"rate", "total", "average", "year", "month", "week", "people", "user", "customer", "business",
           "share", "growth", "time", "number", "level", "result", "group", "company", "market"}

MIN_BLOCK, MAX_BLOCK = 20, 900   # shorter is a label, longer is a whole page section


def content_words(text, drop=()):
    """Lower-case words of 3+ letters, minus stop words, with a crude plural cut."""
    drop = {w.lower() for w in drop}
    out = set()
    for w in re.findall(r"[a-z][a-z0-9-]{2,}", (text or "").lower()):
        if w in STOP or w in drop:
            continue
        if re.search(r"(?:s|x|ch|sh)es$", w):
            w = w[:-2]                     # buses -> bus
        elif len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]                     # trips -> trip
        out.add(w)
    return out


def window(text, start, end):
    """The text that describes the number at text[start:end], and nothing that describes another."""
    spans = [(m.start(), m.end()) for m in STAT_RE.finditer(text)]
    prev = max([e for s, e in spans if e <= start], default=0)
    nxt = min([s for s, e in spans if s >= end], default=len(text))
    before = text[max(prev, start - 90):start]
    cut = max(before.rfind(". "), before.rfind("! "), before.rfind("? "))
    if cut >= 0:
        before = before[cut + 2:]
    after = text[end:min(nxt, end + 110)]
    stop = re.search(r"[.!?](\s|$)", after)
    if stop:
        after = after[:stop.start()]
    return (before + " " + after).lower()


def _weigh(words, base):
    return sum(base / 2 if w in GENERIC else base for w in words)


def described(text, claim, named):
    """Where in `text` one of the claim's numbers is described by our words, or None.

    Our sentence's words count 1, the rest of our paragraph 0.5, generic words half that. A page
    that is the named source needs a score of 1, any other page 2. A round number also needs at
    least one specific (non-generic) word of our sentence beside it."""
    s_words = content_words(claim["sentence"], drop=name_tokens(claim["source"]))
    p_words = content_words(claim.get("paragraph", ""), drop=name_tokens(claim["source"])) - s_words
    need = 1 if named else 2
    for stat in claim["stats"]:
        for m in re.finditer(stat_pattern(stat), text, re.I):
            win = content_words(window(text, m.start(), m.end()))
            s_hit = sorted(s_words & win)
            p_hit = sorted(p_words & win)
            score = _weigh(s_hit, 1) + _weigh(p_hit, 0.5)
            if distinctive(m.group(0)):
                ok = len(s_hit) >= 1 and score >= need / 2
            else:
                ok = any(w not in GENERIC for w in s_hit) and score >= need
            if ok:
                return {"start": m.start(), "end": m.end(), "matched": m.group(0), "words": s_hit + p_hit}
    return None


def prove(claim, blocks, named=False):
    """Pick the smallest block of the page that proves the claim.

    blocks: the page's block texts (see page.read_html). Returns {found: True, block, start, end,
    matched, words} or {found: False, reason}."""
    pats = [re.compile(stat_pattern(s), re.I) for s in claim["stats"]]
    holders = [i for i, t in enumerate(blocks) if any(p.search(t) for p in pats)]
    usable = [i for i in holders if MIN_BLOCK <= len(blocks[i]) <= MAX_BLOCK]
    best = None
    for i in usable:
        text = blocks[i]
        # Judge a number in the smallest block that holds it. In a row of stat cards the row's
        # text runs one card into the next, and the card before would lend its words.
        if any(j != i and len(blocks[j]) < len(text) and blocks[j] in text for j in usable):
            continue
        d = described(text, claim, named)
        if d and (best is None or len(text) < len(blocks[best["block"]])):
            best = dict(d, block=i)
    if best:
        return dict(best, found=True, passage=blocks[best["block"]])
    return {"found": False,
            "reason": "the number is on the page, but not described by our words" if holders
            else "the number is not on the page"}
