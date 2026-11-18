import json
import tempfile
import unittest
from pathlib import Path

from streetviz import Markings, Network, write_html


class ReportTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.output = Path(tmp.name) / "report.html"
        self.network = Network([(1, 2), (3, 4)], [(2, 1)])

    def render(self, **options):
        write_html(self.network, self.output, **options)
        raw = self.output.read_text().split('id="data">')[1].split("</script>")[0]
        return json.loads(raw)

    def test_independent_reports(self):
        first = self.render(markings=Markings(edge_groups={(2, 1): 0}), basemap="none",
                            groups={0: {"label": "</script>", "color": "#123456"}})
        self.assertEqual(first["edgesMarked"], {"1,2": "0"})
        self.assertEqual(first["groups"]["0"]["label"], "</script>")
        self.assertEqual(first["basemap"], "none")
        second = self.render(markings=Markings(node_groups={2: 5}))
        self.assertEqual(second["edgesMarked"], {})
        self.assertEqual(second["nodesMarked"], {"2": "5"})

    def test_custom_tiles(self):
        url = "https://example.org/{z}/{x}/{y}.png"
        with self.assertRaises(ValueError):
            self.render(basemap="custom", tile_url=url)
        data = self.render(basemap="custom", tile_url=url, attribution="Cartography")
        self.assertEqual(data["tileUrl"], url)

    def test_invalid_markings_and_style(self):
        for options in ({"markings": Markings(node_groups={5: 0})},
                        {"markings": Markings(edge_groups={(1, 1): 2})},
                        {"groups": {1: {"color": "invalid"}}}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.render(**options)
