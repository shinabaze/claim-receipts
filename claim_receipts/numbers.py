"""Find statistics in text, and match one number in every way it is commonly printed."""
import re

# A statistic a page can be quoted for: a percentage, money, a multiplier, or a count with a scale
# word. Bare years, list numbers ("5 steps") and durations are not.
STAT_RE = re.compile(
    r"(?<![\w.])(?:"
    r"\$\s?\d[\d,]*(?:\.\d+)?\s?(?:[kKmMbB]\b|thousand|million|billion|trillion)?"
    r"|\d[\d,]*(?:\.\d+)?\s?(?:%|percent\b|per cent\b)"
    r"|\d+(?:\.\d+)?\s?[x×](?![\w])"
    r"|\d[\d,]*(?:\.\d+)?\s(?:thousand|million|billion|trillion)\b"
    r")"
)

_SCALES = {
    "k": "(?:k|thousand)", "thousand": "(?:k|thousand)",
    "m": "(?:m|mn|million)", "million": "(?:m|mn|million)",
    "b": "(?:b|bn|billion)", "billion": "(?:b|bn|billion)",
    "t": "(?:t|tn|trillion)", "trillion": "(?:t|tn|trillion)",
}


def stat_pattern(stat):
    """A regex for `stat` in its common printed forms: 41% / 41 percent / 41.0%, 1,200 / 1200,
    $5.8B / $5.8 billion, 3x / 3 times. It never matches inside a bigger number (12% in 112%)."""
    s = stat.replace(",", "").replace(" ", "")
    m = re.match(r"\$?(\d+(?:\.\d+)?)", s)
    if not m:
        return re.escape(stat)
    whole, _, frac = m.group(1).partition(".")
    grouped = "{:,}".format(int(whole))
    num = "(?:%s|%s)" % (re.escape(whole), re.escape(grouped)) if grouped != whole else re.escape(whole)
    core = num + (r"\." + re.escape(frac) if frac else r"(?:\.0+)?")
    low = stat.lower()
    if "%" in stat or "percent" in low or "per cent" in low:
        return r"(?<![\d.])" + core + r"\s?(?:%|percent|per cent)"
    if re.search(r"[x×]$", stat.strip()):
        return r"(?<![\d.])" + core + r"\s?(?:x|×|times)(?![a-z])"
    money = r"\$\s?" if stat.strip().startswith("$") else r"\$?\s?"
    scale = re.search(r"(thousand|million|billion|trillion|[kKmMbBtT])\b", stat)
    if scale:
        return money + r"(?<![\d.])" + core + r"\s?" + _SCALES[scale.group(1).lower()] + r"(?![a-z])"
    return money + r"(?<![\d.])" + core + r"(?![\d])"


def distinctive(printed):
    """18.8%, 740 million or $5.8B could hardly be on a page by chance. 41%, 50% and $100 are on
    half the pages on the internet, so they need stronger evidence."""
    digits = re.sub(r"[^0-9.]", "", printed)
    return ("." in digits
            or bool(re.search(r"thousand|million|billion|trillion|\d\s?[kmb]\b", printed, re.I))
            or len(digits.rstrip("0").replace(".", "")) >= 3)
