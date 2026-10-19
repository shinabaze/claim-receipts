"""Turn HTML into the text of its blocks, the way a browser's innerText would read them."""
import re
from html.parser import HTMLParser

BLOCK_TAGS = {"p", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
              "figcaption", "dd", "dt", "section", "article", "div", "span"}
SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
BREAK_TAGS = {"br", "p", "li", "div", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6"}


def norm(s):
    """Same text in, same text out, in Python and in the browser: no-break spaces become spaces,
    curly quotes become straight ones, runs of whitespace become one space."""
    s = (s or "").replace(" ", " ").replace("‘", "'").replace("’", "'")
    s = s.replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


class _Blocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.open, self.out, self.skip, self.title, self._in_title = [], [], 0, "", False

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        if tag == "title":
            self._in_title = True
        if tag in BREAK_TAGS:
            self._text(" ")
        if tag in BLOCK_TAGS and tag != "br":
            self.open.append([tag, []])

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip = max(0, self.skip - 1)
        if tag == "title":
            self._in_title = False
        if tag in BREAK_TAGS:
            self._text(" ")
        # close the innermost open block with this tag (tolerates a missing </p> inside it)
        for i in range(len(self.open) - 1, -1, -1):
            if self.open[i][0] == tag:
                for t, parts in self.open[i:][::-1]:
                    self.out.append((t, norm("".join(parts))))
                del self.open[i:]
                break

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self.skip:
            self._text(data)

    def _text(self, s):
        for _, parts in self.open:
            parts.append(s)


def read_html(html):
    """(title, [block text, ...]). Each block holds its own text and its children's, as innerText
    does, so the smallest block that proves a claim can be chosen later."""
    p = _Blocks()
    p.feed(html or "")
    p.close()
    return norm(p.title), [t for _, t in p.out if t]


def site_of(url):
    host = re.sub(r"^https?://", "", url or "").split("/")[0].lower()
    return host[4:] if host.startswith("www.") else host


def name_tokens(name):
    return [t for t in re.findall(r"[a-z0-9]+", (name or "").lower()) if len(t) > 2 and t not in ("the", "and", "inc", "com")]


def is_named_source(url, title, name):
    """Is this page the source the sentence names? Its host or its title carries the name."""
    host = site_of(url).replace("-", "").replace(".", "")
    toks = name_tokens(name)
    flat = re.sub(r"[^a-z0-9]", "", (name or "").lower().replace("&", "and"))
    return bool(toks) and ("".join(toks) in host
                           or any(t in host for t in toks if len(t) > 4)
                           or (len(flat) >= 4 and flat in host)
                           or name.lower() in (title or "").lower())
