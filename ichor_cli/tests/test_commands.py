"""Check CLI dispatch without configuration or a real scheduler."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from ichor.cli.commands import build_parser, main


class CommandTests(unittest.TestCase):
    def test_help_does_not_import_hpc(self):
        with patch.dict(sys.modules, {"ichor.hpc": None}):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    main(["submit_aimall", "--help"])
        self.assertEqual(result.exception.code, 0)

    def test_invalid_options(self):
        for flags in (["--ncores", "0"], ["--encomp", "9"], ["--unknown"]):
            with self.subTest(flags=flags), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    build_parser().parse_args(["submit_aimall"] + flags)
                self.assertEqual(result.exception.code, 2)

    def test_submission_dispatch(self):
        batch = ModuleType("ichor.hpc.batch_system")
        batch.JobID = lambda script, id: SimpleNamespace(script=script, id=id)
        aimall = ModuleType("ichor.hpc.main.aimall")
        submit = aimall.submit_points_directory_to_aimall = Mock()
        modules = {batch.__name__: batch, aimall.__name__: aimall}
        with tempfile.TemporaryDirectory() as tmp:
            points = Path(tmp) / "water.pointsdir"
            points.mkdir()
            for job in (None, SimpleNamespace(id="123")):
                submit.return_value = job
                output = io.StringIO()
                with patch.dict(sys.modules, modules), contextlib.redirect_stdout(output):
                    self.assertEqual(main([
                        "submit_aimall", str(points), "--ncores", "4", "--atoms",
                        "O1", "H2", "--hold", "42", "--force", "--no-iasprops",
                        "--atidsprops", "some",
                    ]), 0)
                kwargs = submit.call_args.kwargs
                self.assertEqual(kwargs["points_directory"], points.resolve())
                self.assertEqual(kwargs["ncores"], 4)
                self.assertEqual(kwargs["aimall_atoms"], ["O1", "H2"])
                self.assertEqual(kwargs["hold"].id, "42")
                self.assertEqual(kwargs["atidsprops"], 0.001)
                self.assertTrue(kwargs["force_calculate_ints"])
                self.assertFalse(kwargs["iasprops"])
                self.assertNotIn("script_name", kwargs)
                self.assertIn("no AIMAll jobs" if job is None else "123", output.getvalue())


if __name__ == "__main__":
    unittest.main()
