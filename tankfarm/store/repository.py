"""Durable storage of the record stream, checkpoints and audit trail."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from tankfarm.errors import StoreError
from tankfarm.journal.checkpoint import JournalCheckpoint
from tankfarm.journal.record import Record
from tankfarm.store.layout import StoreLayout
from tankfarm.store.reader import JsonReader
from tankfarm.store.writer import AtomicWriter


class Repository:
    """The only component that touches the data directory."""

    def __init__(self, root: str | Path) -> None:
        self._layout = StoreLayout(root)
        self._layout.ensure()
        self._writer = AtomicWriter()
        self._reader = JsonReader()

    @property
    def layout(self) -> StoreLayout:
        return self._layout

    def append_record(self, record: Record) -> None:
        self._writer.append_line(self._layout.journal_file(), record.as_payload())

    def load_records(self) -> tuple[Record, ...]:
        """Reads the whole journal, validating sequence continuity.

        A gap means committed history is missing; resuming from that silently
        would present factory-seeded state as current, so this is a hard error.
        """

        items = self._reader.read_lines(self._layout.journal_file())
        records: list[Record] = []
        seen: set[int] = set()
        for index, item in enumerate(items, start=1):
            record = Record.from_payload(item)
            if record.seq != index:
                raise StoreError(
                    str(self._layout.journal_file()),
                    f"journal gap or reorder: expected seq {index}, found {record.seq}",
                )
            if record.seq in seen:
                raise StoreError(
                    str(self._layout.journal_file()),
                    f"duplicate journal seq {record.seq}",
                )
            seen.add(record.seq)
            records.append(record)
        return tuple(records)

    def save_checkpoint(self, checkpoint: JournalCheckpoint) -> None:
        """Persists the latest committed watermark and projected state."""

        self._writer.write_json(
            self._layout.checkpoint_file(),
            {
                "watermark": checkpoint.watermark,
                "head": checkpoint.head,
                "ts": checkpoint.ts,
                "state": dict(checkpoint.state),
            },
        )

    def load_checkpoint(self) -> JournalCheckpoint | None:
        payload = self._reader.read_json(self._layout.checkpoint_file())
        if payload is None:
            return None
        return JournalCheckpoint.from_payload(payload)

    def append_audit(self, payload: Mapping[str, Any]) -> None:
        self._writer.append_line(self._layout.audit_file(), payload)

    def load_audit(self) -> tuple[dict[str, Any], ...]:
        return self._reader.read_lines(self._layout.audit_file())
