from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import time
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class TaskSpec:
    name: str
    payload: Dict[str, Any]
    timeout_ms: int = 1000
    max_input_bytes: int = 65536


@dataclass(frozen=True)
class Receipt:
    task_id: str
    name: str
    status: str
    elapsed_ms: int
    output: Any = None
    error: Optional[str] = None


class EdgeRuntime:
    """Allowlisted, dependency-free edge task runtime.

    Edryx deliberately does not execute arbitrary shell commands or paths.
    Callers register explicit Python callables and may invoke only those names.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register(self, name: str, fn: Callable[[Dict[str, Any]], Any]) -> None:
        name = name.strip()
        if not name:
            raise ValueError("task name is required")
        if not callable(fn):
            raise TypeError("fn must be callable")
        self._tasks[name] = fn

    def registered(self) -> tuple[str, ...]:
        return tuple(sorted(self._tasks))

    @staticmethod
    def _task_id(spec: TaskSpec) -> str:
        canonical = json.dumps(
            asdict(spec),
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(canonical.encode("utf-8")).hexdigest()[:24]

    def execute(self, spec: TaskSpec) -> Receipt:
        if spec.timeout_ms < 1:
            raise ValueError("timeout_ms must be >= 1")
        if spec.max_input_bytes < 1:
            raise ValueError("max_input_bytes must be >= 1")
        if spec.name not in self._tasks:
            raise KeyError(f"unregistered task: {spec.name}")

        encoded = json.dumps(spec.payload, sort_keys=True).encode("utf-8")
        if len(encoded) > spec.max_input_bytes:
            return Receipt(
                task_id=self._task_id(spec),
                name=spec.name,
                status="rejected",
                elapsed_ms=0,
                error="input_budget_exceeded",
            )

        start = time.monotonic_ns()
        try:
            output = self._tasks[spec.name](dict(spec.payload))
            error = None
            status = "completed"
        except Exception as exc:  # isolate task failure at runtime boundary
            output = None
            error = f"{type(exc).__name__}: {exc}"
            status = "failed"

        elapsed_ms = max(0, (time.monotonic_ns() - start) // 1_000_000)
        if elapsed_ms > spec.timeout_ms and status == "completed":
            return Receipt(
                task_id=self._task_id(spec),
                name=spec.name,
                status="deadline_exceeded",
                elapsed_ms=elapsed_ms,
                error="task exceeded deadline",
            )

        return Receipt(
            task_id=self._task_id(spec),
            name=spec.name,
            status=status,
            elapsed_ms=elapsed_ms,
            output=output,
            error=error,
        )


def builtin_runtime() -> EdgeRuntime:
    runtime = EdgeRuntime()
    runtime.register("echo", lambda payload: payload)
    runtime.register(
        "sum",
        lambda payload: sum(float(x) for x in payload.get("values", [])),
    )
    runtime.register(
        "project",
        lambda payload: {
            key: payload.get("data", {}).get(key)
            for key in payload.get("keys", [])
        },
    )
    return runtime
