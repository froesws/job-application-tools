"""Where profiles, runs, and the corpus live.

The environment wins; the defaults point at the repository root, which is where a
developer runs the tool.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    profile_root: Path
    data_root: Path

    @property
    def runs_root(self) -> Path:
        return self.data_root / "runs"

    @property
    def corpus_path(self) -> Path:
        return self.data_root / "corpus.jsonl"

    @property
    def ingestions_root(self) -> Path:
        return self.data_root / "ingestions"

    @property
    def eval_root(self) -> Path:
        return self.data_root / "eval"


def from_env() -> Paths:
    return Paths(
        profile_root=Path(os.environ.get("CVTAILOR_PROFILE_ROOT", "profile")),
        data_root=Path(os.environ.get("CVTAILOR_DATA_ROOT", "data")),
    )
