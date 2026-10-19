"""Check every attributed statistic in examples/article.html against two saved source pages.

    python examples/demo.py             # the rules only, no browser
    python examples/demo.py --capture   # also screenshot each proof (needs Playwright)
"""
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from claim_receipts import check, find_claims  # noqa: E402

PAGES = {  # where each page "lives", for the named-source rule
    "https://harbourcitytransport.example/travel-survey-2026": HERE / "pages" / "travel-survey.html",
    "https://bikeshare-notes.example/running-a-scheme": HERE / "pages" / "bike-share-notes.html",
}


def main():
    capture = "--capture" in sys.argv
    article = (HERE / "article.html").read_text(encoding="utf-8")
    figures = []
    for c in find_claims(article):
        print("\n" + c["sentence"])
        print("  source named: %s   numbers: %s" % (c["source"], ", ".join(c["stats"])))
        for url, path in PAGES.items():
            r = check(c, path.read_text(encoding="utf-8"), url)
            if r["found"]:
                print("  PROVED by %s" % url)
                print("    passage: %s" % r["passage"])
                print("    words beside %s: %s" % (r["matched"], ", ".join(r["words"])))
                if capture:
                    figures.append(shoot(c, path))
                break
            print("  not %s: %s" % (url.split("/")[2], r["reason"]))
        else:
            print("  -> no receipt. Shown as unverified, never as proved.")
    if capture:
        out = HERE / "out"
        (out / "receipts.html").write_text(page(figures), encoding="utf-8")
        print("\nwrote %s" % (out / "receipts.html"))


def shoot(claim, path):
    from claim_receipts.capture import capture
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    shot = out / ("%s.png" % claim["id"])
    r = capture(path.as_uri(), claim, str(shot))
    return r if r["ok"] else None


def page(results):
    from claim_receipts.capture import RECEIPT_CSS, figure_html
    figs = "".join(figure_html(r, os.path.basename(r["image"])) for r in results if r)
    return ("<!doctype html><meta charset=utf-8><title>Receipts</title><style>body{font:16px sans-serif;"
            "max-width:760px;margin:40px auto}figure{margin:0 0 32px}img{display:block}%s</style>%s" % (RECEIPT_CSS, figs))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
