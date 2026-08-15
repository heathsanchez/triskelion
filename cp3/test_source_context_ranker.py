from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import source_context_ranker as ranker


class SourceContextRankerTests(unittest.TestCase):
    def test_excludes_generated_env_and_ranks_named_definition(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "env/lib/python3.7/site-packages/_pytest").mkdir(parents=True)
            (root / "env/lib/python3.7/site-packages/_pytest/core.py").write_text("def parse_items():\n    pass\n")
            (root / "pkg").mkdir()
            (root / "pkg/cli.py").write_text("def parse_items(items):\n    return items\n")
            (root / "pkg/other.py").write_text("def unrelated():\n    return 1\n")
            failure = "FAILED test_escape_longsep: parse_items produced incorrect escaped separator"
            _, files = ranker.collect_context(root, failure)
            self.assertIn("pkg/cli.py", files)
            self.assertFalse(any(f.startswith("env/") for f in files))
            self.assertLess(files.index("pkg/cli.py"), len(files))

    def test_traceback_project_frame_beats_unrelated_file(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "youtube_dl").mkdir()
            target = root / "youtube_dl/utils.py"
            target.write_text("def strip_jsonp(value):\n    return value\n")
            (root / "aaa.py").write_text("def unrelated():\n    pass\n")
            failure = f'File "{target}", line 2, in strip_jsonp\nJSONDecodeError: Expecting value'
            _, files = ranker.collect_context(root, failure)
            self.assertEqual(files[0], "youtube_dl/utils.py")

    def test_devscripts_are_not_fallback_context(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "devscripts").mkdir()
            (root / "devscripts/a.py").write_text("def strip_jsonp(v):\n    return v\n")
            (root / "youtube_dl").mkdir()
            (root / "youtube_dl/utils.py").write_text("def strip_jsonp(v):\n    return v\n")
            _, files = ranker.collect_context(root, "test_strip_jsonp failed in strip_jsonp")
            self.assertIn("youtube_dl/utils.py", files)
            self.assertFalse(any(f.startswith("devscripts/") for f in files))


if __name__ == "__main__":
    unittest.main()
