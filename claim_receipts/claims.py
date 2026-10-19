"""Find the attributed statistics in an article: a number, and who the sentence says it came from."""
import hashlib
import html
import re

from .numbers import STAT_RE
from .page import norm

_NAME = r"((?:[A-Z][\w&'.-]*|[A-Z]{2,})(?:\s+(?:[A-Z][\w&'.-]*|of|the|and|&))*)"
ATTRIBUTION = [
    re.compile(r"\b[Aa]ccording to (?:the |a |an |recent )*" + _NAME),
    re.compile(r"\b(?:[Pp]er|[Vv]ia|[Cc]iting) (?:the )?" + _NAME),
    re.compile(_NAME + r"(?:'s)? (?:\d{4} )?(?:report|reports|reported|found|finds|shows|showed|data|research|"
                       r"study|survey|benchmarks?|analysis|estimates?|notes|says|confirms?)\b"),
    re.compile(r"\((?:source: )?" + _NAME + r",? (?:\d{4}|report|study|data)\)"),
]
WEAK = 2   # "<Name> reports ..." also reads worked examples ("the shop reports 1 order for $100")

# Words that start a sentence or describe data, never a publisher.
_OPENERS = {"if", "while", "when", "as", "since", "although", "because", "and", "but", "once", "after", "before",
            "across", "among", "with", "for", "in", "on", "at", "by", "so", "yet", "even", "only", "this", "that",
            "these", "those", "it", "our", "we", "your", "a", "an", "most", "many", "some", "the"}
_GENERIC = {"recent", "data", "industry", "market", "research", "studies", "study", "survey", "benchmark",
            "benchmarks", "analysis", "early", "latest", "new", "current", "internal", "report", "reports",
            "global", "average", "median", "top", "leading", "independent", "public", "q1", "q2", "q3", "q4"}

# A worked example is not a claim about the world, whoever it names.
EXAMPLE_RE = re.compile(r"\b(?:illustrative|hypothetical|for example|for instance|scenario|imagine|suppose|"
                        r"let's say|say you)\b|\be\.g\.", re.I)
METRIC_RE = re.compile(r"\b(?:cost|costs|rate|rates|average|median|share|growth|revenue|spend|margin|price|"
                       r"prices|income|wage|wages|yield)\b", re.I)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"$])", text) if s.strip()]


def attribution(sentence):
    """(source name, weak) or ("", False)."""
    for k, rx in enumerate(ATTRIBUTION):
        for m in rx.finditer(sentence):
            name = re.sub(r"'s$", "", m.group(1).strip())
            name = re.sub(r"^(?:The|the)\s+", "", name)
            name = re.sub(r"\s+(of|the|and|&)$", "", name).rstrip(".,;:'")
            words = name.split()
            if not words or words[0].lower() in _OPENERS:
                continue
            if all(w.lower().strip("'") in _GENERIC for w in words):
                continue
            if STAT_RE.fullmatch(name):
                continue
            return name, k == WEAK
    return "", False


def paragraphs(article):
    """HTML (its p / li / blockquote / td blocks) or plain text (blank-line separated)."""
    if "<" in article and ">" in article:
        out = []
        for _, inner in re.findall(r"<(p|li|blockquote|td)\b[^>]*>(.*?)</\1>", article, re.S | re.I):
            text = norm(html.unescape(re.sub(r"<[^>]+>", " ", inner)))
            if text:
                out.append(text)
        return out
    return [norm(p) for p in re.split(r"\n\s*\n", article) if norm(p)]


def find_claims(article):
    """Every attributed statistic: [{id, sentence, stats, source, paragraph}]."""
    out = []
    for para in paragraphs(article):
        if EXAMPLE_RE.search(para):
            continue
        for s in sentences(para):
            stats = [m.group(0).strip() for m in STAT_RE.finditer(s)]
            if not stats:
                continue
            name, weak = attribution(s)
            if not name:
                continue
            # "<Name> reports $100" names a number, not a measurement, unless it is a rate, a
            # scale, or the sentence says what it measures
            if weak and not re.search(r"%|percent|[x×]$|thousand|million|billion|trillion", " ".join(stats)) \
                    and not METRIC_RE.search(s):
                continue
            cid = hashlib.sha1((s + "|" + stats[0]).encode("utf-8")).hexdigest()[:10]
            out.append({"id": cid, "sentence": s, "stats": stats, "source": name, "paragraph": para})
    return out
