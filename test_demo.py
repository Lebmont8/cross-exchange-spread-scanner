import json
from threading import Thread
from unittest import TestCase
from urllib.error import HTTPError
from urllib.request import urlopen

from serve import FIXTURE, Handler, ThreadingHTTPServer, run


class HttpTest(TestCase):
    def test_routes_and_validation(self):
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(base, timeout=3) as response:
                    self.assertIn(b'name="viewport"', response.read())
                with urlopen(base + "/api/replay", timeout=3) as response:
                    self.assertEqual(json.load(response), run(FIXTURE, {}))
                for query in ("unknown=1", "size=NaN", "test=1&test=2"):
                    with self.assertRaises(HTTPError) as failure:
                        urlopen(base + "/api/replay?" + query, timeout=3)
                    with failure.exception as response:
                        self.assertEqual(response.code, 400)
                with self.assertRaises(HTTPError) as failure:
                    urlopen(base + "/not-a-route", timeout=3)
                failure.exception.close()
                self.assertEqual(failure.exception.code, 404)
            finally:
                server.shutdown()
                thread.join(timeout=3)

class SpreadTest(TestCase):
    def test_edges_include_depth_and_both_fees(self):
        result = run(FIXTURE, {})
        self.assertEqual(result["rows"][0][4:6], ["51.42", "20.6"])
        self.assertEqual(result["rows"][4][2:6], ["7.0", "500", "-17.51", "-7.0"])

    def test_thin_leg_blocks_paired_execution(self):
        self.assertIn("0.110000 BTC", run(FIXTURE, {})["rows"][2][-1])
        self.assertEqual(run(FIXTURE, {"size": "0.10"})["rows"][2][-1], "Would simulate both legs")

    def test_stale_quotes_do_not_generate_net_values(self):
        row = run(FIXTURE, {})["rows"][6]
        self.assertEqual(row[4:], ["—", "—", "Skip: stale quote"])
        self.assertEqual(run(FIXTURE, {"age": "3000"})["rows"][6][-1], "Would simulate both legs")

    def test_minimum_edge_affects_decision(self):
        row = run(FIXTURE, {"minimum": "21"})["rows"][0]
        self.assertEqual(row[-1], "Skip: below minimum net edge")
        self.assertEqual(row[4:6], ["51.42", "20.6"])
