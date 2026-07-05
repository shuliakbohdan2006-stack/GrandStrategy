from __future__ import annotations

import zlib


def stable_hash(text: str) -> int:
    """Return a deterministic hash that is stable across Python runs."""
    return zlib.crc32(text.encode("utf-8")) & 0xFFFFFFFF
