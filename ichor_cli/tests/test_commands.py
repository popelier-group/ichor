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
    def test_datagen_dispatch(self):
        datagen = ModuleType("ichor.hpc.main.data_generation")
        submit = datagen.submit_data_generation_from_yaml = Mock(
            return_value=SimpleNamespace(
                points_directory=Path("water.pointsdir"),
                gaussian=SimpleNamespace(id="101"),
                aimall=SimpleNamespace(id="102"), database=None, csvs=None,
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "custom.yaml"
            config.write_text("input:\n  path: water.xyz\n")
            output = io.StringIO()
            with patch.dict(sys.modules, {datagen.__name__: datagen}), contextlib.redirect_stdout(output):
                self.assertEqual(main(["submit_datagen", str(config)]), 0)
            submit.assert_called_once_with(config.resolve())
            self.assertIn("Submitted gaussian job 101", output.getvalue())
            self.assertIn("Submitted aimall job 102", output.getvalue())
            self.assertNotIn("Submitted database", output.getvalue())

    def test_datagen_default_help_and_missing_file(self):
        self.assertEqual(
            build_parser().parse_args(["submit_datagen"]).config,
            Path("ichor_workflow.yaml"),
        )
        with patch.dict(sys.modules, {"ichor.hpc": None}), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                main(["submit_datagen", "--help"])
            self.assertEqual(result.exception.code, 0)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                main(["submit_datagen", str(Path(tmp) / "missing.yaml")])
            self.assertEqual(result.exception.code, 2)

    def test_gaussian_dispatch(self):
        batch = ModuleType("ichor.hpc.batch_system")
        batch.JobID = lambda script, id: SimpleNamespace(script=script, id=id)
        gaussian = ModuleType("ichor.hpc.main.gaussian")
        submit = gaussian.submit_points_directory_to_gaussian = Mock(return_value=SimpleNamespace(id="456"))
        with tempfile.TemporaryDirectory() as tmp:
            points = Path(tmp) / "water.pointsdir"
            points.mkdir()
            output = io.StringIO()
            with patch.dict(sys.modules, {batch.__name__: batch, gaussian.__name__: gaussian}), contextlib.redirect_stdout(output):
                self.assertEqual(main([
                    "submit_gaussian", str(points), "--method", "HF", "--basis-set",
                    "6-31+g(d,p)", "--ncores", "4", "--charge", "-1",
                    "--spin-multiplicity", "2", "--keywords", "opt", "nosymm",
                    "--overwrite-existing", "--force", "--hold", "42",
                ]), 0)
                kwargs = submit.call_args.kwargs
                self.assertEqual(kwargs["method"], "HF")
                self.assertEqual(kwargs["basis_set"], "6-31+g(d,p)")
                self.assertEqual(kwargs["charge"], -1)
                self.assertEqual(kwargs["spin_multiplicity"], 2)
                self.assertEqual(kwargs["keywords"], ["opt", "nosymm"])
                self.assertEqual(kwargs["ncores"], 4)
                self.assertEqual(kwargs["hold"].id, "42")
                self.assertTrue(kwargs["overwrite_existing"])
                self.assertTrue(kwargs["force_calculate_wfn"])
                self.assertIn("456", output.getvalue())
                submit.side_effect = ValueError("There are no jobs to submit in the submission script.")
                self.assertEqual(main(["submit_gaussian", str(points)]), 0)
                self.assertIn("no Gaussian jobs", output.getvalue())
                self.assertNotIn("method", submit.call_args.kwargs)
                submit.side_effect = ValueError("invalid input")
                with self.assertRaisesRegex(ValueError, "invalid input"):
                    main(["submit_gaussian", str(points)])

    def test_gaussian_help_and_validation(self):
        with patch.dict(sys.modules, {"ichor.hpc": None}), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                main(["submit_gaussian", "--help"])
            self.assertEqual(result.exception.code, 0)
        for flags in (["--ncores", "0"], ["--spin-multiplicity", "0"], ["--charge", "abc"]):
            with self.subTest(flags=flags), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    build_parser().parse_args(["submit_gaussian"] + flags)
                self.assertEqual(result.exception.code, 2)

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
