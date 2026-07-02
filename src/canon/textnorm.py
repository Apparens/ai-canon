"""One canonical ascii-fold/normalize helper.

The pipeline compares "the same name spelled differently" in several places
(model slugs, title matching). This is the single spelling of that operation;
modules adopt it instead of growing private copies.
"""

from __future__ import annotations

import re
import unicodedata


def fold(s: str) -> str:
    """NFKD-normalize, drop non-ascii, lowercase, collapse non-alphanumeric runs
    to single spaces, and strip: 'GPT-4 Turbo' -> 'gpt 4 turbo'."""
    return re.sub(r"[^a-z0-9]+", " ",
                  unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()).strip()
