import time
import unittest

from edryx import EdgeRuntime, TaskSpec, builtin_runtime


class EdgeRuntimeTests(unittest.TestCase):
    def test_registered_tasks_are_sorted(self):
        runtime = EdgeRuntime()
        runtime.register("b", lambda payload: payload)
        runtime.register("a", lambda payload: payload)
        self.assertEqual(runtime.registered(), ("a", "b"))

    def test_unregistered_task_is_rejected(self):
        with self.assertRaises(KeyError):
            builtin_runtime().execute(TaskSpec(name="missing", payload={}))

    def test_task_id_is_deterministic(self):
        runtime = builtin_runtime()
        spec = TaskSpec(name="echo", payload={"b": 2, "a": 1})
        a = runtime.execute(spec)
        b = runtime.execute(spec)
        self.assertEqual(a.task_id, b.task_id)

    def test_input_budget_is_enforced(self):
        runtime = builtin_runtime()
        result = runtime.execute(
            TaskSpec(name="echo", payload={"x": "a" * 100}, max_input_bytes=10)
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.error, "input_budget_exceeded")

    def test_task_failure_is_isolated(self):
        runtime = EdgeRuntime()
        runtime.register("boom", lambda payload: 1 / 0)
        result = runtime.execute(TaskSpec(name="boom", payload={}))
        self.assertEqual(result.status, "failed")
        self.assertIn("ZeroDivisionError", result.error)

    def test_deadline_is_reported(self):
        runtime = EdgeRuntime()
        runtime.register("slow", lambda payload: time.sleep(0.01) or "ok")
        result = runtime.execute(TaskSpec(name="slow", payload={}, timeout_ms=1))
        self.assertEqual(result.status, "deadline_exceeded")

    def test_builtin_sum_and_project(self):
        runtime = builtin_runtime()
        total = runtime.execute(
            TaskSpec(name="sum", payload={"values": [1, 2, 3.5]})
        )
        projected = runtime.execute(
            TaskSpec(
                name="project",
                payload={"data": {"a": 1, "b": 2}, "keys": ["b"]},
            )
        )
        self.assertEqual(total.output, 6.5)
        self.assertEqual(projected.output, {"b": 2})


if __name__ == "__main__":
    unittest.main()
