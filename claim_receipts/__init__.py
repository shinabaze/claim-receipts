"""claim-receipts: put the source's own sentence next to every statistic you quote, or say you can't."""
from .claims import find_claims
from .match import prove
from .numbers import stat_pattern
from .page import is_named_source, read_html


def check(claim, html, url=""):
    """Does this page (its HTML and address) prove the claim? See match.prove for the result."""
    title, blocks = read_html(html)
    return prove(claim, blocks, named=is_named_source(url, title, claim["source"]))


__all__ = ["find_claims", "prove", "check", "stat_pattern", "read_html", "is_named_source"]
