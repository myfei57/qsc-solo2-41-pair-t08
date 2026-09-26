"""Append-only and atomic file writers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from tankfarm.errors import StoreError


class AtomicWriter:
    """Writes either a whole JSON document or one appended JSON line.

    JSON documents are replaced atomically (temp file + fsync + rename) so a
    crash never leaves a half-written checkpoint. JSONL lines are appended in
    one O_APPEND write and flushed to disk before the call returns.
    """

    def write_json(self, path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        tmp_name = ""
        try:
            fd, tmp_name = tempfile.mkstemp(
                prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
            )
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp_name, path)
            finally:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
            self._fsync_dir(path.parent)
        except OSError as exc:  # pragma: no cover - depends on the file system
            raise StoreError(str(path), str(exc)) from exc

    def append_line(self, path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        try:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
            self._fsync_dir(path.parent)
        except OSError as exc:  # pragma: no cover - depends on the file system
            raise StoreError(str(path), str(exc)) from exc

    def _fsync_dir(self, directory: Path) -> None:
        try:
            dir_fd = os.open(directory, os.O_RDONLY)
        except OSError:  # pragma: no cover - depends on the file system
            return
        try:
            os.fsync(dir_fd)
        except OSError:  # pragma: no cover - depends on the file system
            pass
        finally:
            os.close(dir_fd)
