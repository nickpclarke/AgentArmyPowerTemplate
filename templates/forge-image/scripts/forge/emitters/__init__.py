"""Output emitters — forge IR → source files on disk.

Each emitter exposes a single `emit(model, out_dir) -> list[str]` function
that returns the list of written file paths (relative to `out_dir`).

Determinism rules (load-bearing for the byte-identical doctor check):
  * No timestamps or hostnames in file headers.
  * Iteration order is the IR's declared `model.object_types` order
    (parsers are responsible for keeping that stable).
  * Sorted dict keys wherever a dict is serialized.
  * UTF-8 + LF line endings. Files end with a single trailing LF.
"""
from __future__ import annotations
