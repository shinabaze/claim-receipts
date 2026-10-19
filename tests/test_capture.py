"""The browser capture, against the same six fixture pages served from 127.0.0.1.
Skipped when Playwright or its Chromium is not installed."""
import os
import struct
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from claim_receipts import find_claims
from tests.fixtures import CASES, page

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


class Pages(BaseHTTPRequestHandler):
    def do_GET(self):
        body = page(CASES[int(self.path.strip("/"))]).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@unittest.skipIf(sync_playwright is None, "Playwright is not installed")
class Capture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Pages)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch()
        except Exception as e:
            cls.pw.stop()
            cls.server.shutdown()
            raise unittest.SkipTest("Chromium is not installed: %s" % str(e).splitlines()[0])
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()

    def test_each_fixture_page(self):
        from claim_receipts.capture import capture_page, figure_html
        for i, case in enumerate(CASES):
            with self.subTest(case["name"]):
                p = self.browser.new_page(viewport={"width": 1280, "height": 900})
                p.goto("http://127.0.0.1:%d/%d" % (self.server.server_port, i))
                out = os.path.join(self.tmp, "%d.png" % i)
                r = capture_page(p, find_claims("<p>%s</p>" % case["sentence"])[0], out)
                p.close()
                self.assertEqual(r["ok"], case["proves"], r)
                if not r["ok"]:
                    self.assertFalse(os.path.exists(out), "a refusal must not leave an image")
                    continue
                with open(out, "rb") as f:
                    head = f.read(24)
                self.assertEqual(head[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", head[16:24])
                self.assertEqual((width, height), (r["width"], r["height"]))
                self.assertTrue(r["marks"])
                for k in r["marks"]:
                    self.assertTrue(0 <= k["x"] and k["x"] + k["w"] <= r["width"] + 4, k)
                    self.assertTrue(0 <= k["y"] and k["y"] + k["h"] <= r["height"] + 2, k)
                self.assertIn("receipt-mark", figure_html(r, "shot.png"))


if __name__ == "__main__":
    unittest.main()
