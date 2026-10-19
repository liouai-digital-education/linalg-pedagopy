"""Backward-compatible re-export of linalg_pedagopy.tutor.lock."""

from __future__ import annotations

from linalg_pedagopy.tutor.lock import (
    LockedMatrix,
    LockedNamespace,
    LockedVector,
    _get_namespace_raw_dict,
)

__all__ = [
    "LockedMatrix",
    "LockedNamespace",
    "LockedVector",
    "_get_namespace_raw_dict",
]
