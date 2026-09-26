"""Deterministic identifier factory."""

from __future__ import annotations

from typing import Mapping


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

    def restore(self, prefix: str, value: int) -> None:
        """Advances a prefix counter to at least ``value`` (never backwards)."""

        self._counters[prefix] = max(self._counters.get(prefix, 0), int(value))

    def restore_all(self, counters: Mapping[str, int]) -> None:
        for prefix, value in counters.items():
            self.restore(prefix, value)

