import bz2
import json
import tempfile
import unittest
from pathlib import Path

from streetviz import load_graph, write_html


class GraphTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.graph = self.root / "test.graph.bz2"
        self.graph.write_bytes(bz2.compress(b"% test\n3 1\n2\n1\n\n"))
        self.xyz = self.root / "test.xyz"
        self.xyz.write_text("604893 5063036 0\n604946 5063032 0\n605003 5063030 0\n")
        self.marks = self.root / "marks.txt"

    def test_embedded_graph(self):
        self.marks.write_text("1 0 0\n0 1 0\n")
        graph = load_graph(self.graph, self.xyz, coord_format="dimacs10-osm", edge_marks=self.marks, mark_id_base=0)
        output = self.root / "result.html"
        write_html(graph, output)
        data = json.loads(output.read_text().split('id="data">')[1].split("</script>")[0])
        self.assertEqual(data["positions"][0], [6.04893, 49.63036])
        self.assertEqual(data["edges"], [[1, 2]])
        self.assertEqual(data["edgesMarked"], {"1,2": "0"})

    def test_invalid_marks(self):
        for content in ["1 2 7\n2 1 3", "1 3 1", "0 1 7", "1 2 -1"]:
            with self.subTest(content=content):
                self.marks.write_text(content)
                with self.assertRaisesRegex(ValueError, "marks.txt:"):
                    load_graph(self.graph, self.xyz, coord_format="dimacs10-osm", edge_marks=self.marks)

    def test_missing_reverse(self):
        self.graph.write_bytes(bz2.compress(b"3 1\n2\n\n\n"))
        with self.assertRaises(ValueError):
            load_graph(self.graph, self.xyz, coord_format="dimacs10-osm")
