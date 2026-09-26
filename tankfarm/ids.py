"""Deterministic identifier factory."""

from __future__ import annotations


class IdFactory:
    """Hands out increasing identifiers per prefix, so runs stay reproducible."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}

    def new(self, prefix: str) -> str:
        count = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = count
        return f"{prefix}-{count:06d}"

    def counters(self) -> dict[str, int]:
        return dict(self._counters)

    def restore(self, prefix: str, count: int) -> None:
        """Ensure the next id for ``prefix`` never repeats a durable one."""

        self._counters[prefix] = max(self._counters.get(prefix, 0), int(count))

