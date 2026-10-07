"""Exercise the queue parser without optional scientific/HPC dependencies."""

import ast
import os
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


class SlurmQueueTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).parents[1] / "ichor/hpc/batch_system/slurm.py"
        tree = ast.parse(source.read_text())
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SLURM")
        method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "get_queued_jobs")
        method.decorator_list = []
        self.run_cmd = Mock()
        self.status = Mock(return_value=["squeue", "-u", "testuser"])
        self.namespace = {
            "os": os, "datetime": datetime, "List": list, "run_cmd": self.run_cmd,
            "JobStatus": lambda value: SimpleNamespace(name={"R": "Running", "PD": "Pending"}[value]),
            "Job": lambda id, priority, name, user, state, start, queue, slots, task_id: SimpleNamespace(
                id=id, priority=priority, name=name, user=user, state=state,
                start=start, queue=queue, slots=slots, task_id=task_id),
        }
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), self.namespace)

    def parse(self, text):
        self.run_cmd.return_value = (text, "")
        return self.namespace["get_queued_jobs"](SimpleNamespace(status=self.status))

    def test_explicit_fields_and_array_tasks(self):
        with patch.dict(os.environ, {}, clear=True):
            jobs = self.parse(
                "22196828_1|0.125|compute|Gaussian run|testuser|R|2026-10-07T10:00:00|4\n"
                "22196829_3|0.100|compute|AIMAll|testuser|PD|N/A|2\n\n"
            )
        self.assertEqual(len(jobs), 2)
        self.assertEqual((jobs[0].id, jobs[0].task_id, jobs[0].slots), ("22196828", "1", 4))
        self.assertEqual(jobs[0].name, "Gaussian run")
        self.assertEqual(jobs[0].state, "Running")
        self.assertEqual(jobs[0].start, datetime(2026, 10, 7, 10))
        self.assertEqual(jobs[1].state, "Pending")
        self.assertIsNone(jobs[1].start)
        command = self.run_cmd.call_args.args[0]
        self.assertIn("--noheader", command)
        self.assertIn("-r", command)
        self.assertIn("--format=%i|%p|%P|%j|%u|%t|%S|%C", command)
        self.assertNotIn("--array-unique", command)

    def test_custom_timestamp_and_single_job(self):
        with patch.dict(os.environ, {"SLURM_TIME_FORMAT": "%d/%m/%Y %H:%M:%S"}):
            jobs = self.parse("42|0.5|compute|job|user|R|07/10/2026 10:34:06|8\n")
        self.assertEqual(jobs[0].slots, 8)
        self.assertIsNone(jobs[0].task_id)
        self.assertEqual(jobs[0].start, datetime(2026, 10, 7, 10, 34, 6))

    def test_empty_queue(self):
        self.assertEqual(self.parse("\n"), [])

    def test_unexpected_output(self):
        with self.assertRaisesRegex(ValueError, "Unexpected squeue output"):
            self.parse("squeue: error: scheduler unavailable\n")


if __name__ == "__main__":
    unittest.main()
