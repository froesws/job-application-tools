"""The service is the single entry point: it validates input and builds the client."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from cvtailor.core.errors import CONFIGURATION_ERROR, INVALID_POSTING, TailorError
from cvtailor.llm.config import ChainEntry, LLMConfig
from cvtailor.service import TailorService
from cvtailor.storage.paths import Paths
from cvtailor.storage.profiles import save_master


def service(tmp_path: Path, master: dict[str, Any], config: LLMConfig | None = None) -> TailorService:
    layout = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    save_master(layout, "software-engineer", master)
    fake = LLMConfig(
        analyze=[ChainEntry("fake", "scripted")],
        tailor=[ChainEntry("fake", "scripted")],
    )
    return TailorService(paths=layout, config=config or fake)


def test_tailor_produces_a_one_page_run(tmp_path: Path, master: dict[str, Any]) -> None:
    result = service(tmp_path, master).tailor(
        posting="Backend Engineer. Python and PostgreSQL.",
        profile="software-engineer",
        language="pt-BR",
    )

    assert result.pages == 1
    assert (result.run_dir / "cv.pdf").is_file()


def test_an_empty_posting_is_refused(tmp_path: Path, master: dict[str, Any]) -> None:
    with pytest.raises(TailorError) as caught:
        service(tmp_path, master).tailor(posting="   ", profile="software-engineer", language="pt-BR")

    assert caught.value.code == INVALID_POSTING


def test_a_posting_above_the_cap_is_refused(tmp_path: Path, master: dict[str, Any]) -> None:
    with pytest.raises(TailorError) as caught:
        service(tmp_path, master).tailor(
            posting="x" * 100_001, profile="software-engineer", language="pt-BR"
        )

    assert caught.value.code == INVALID_POSTING


def test_a_real_provider_is_not_implemented_yet(tmp_path: Path, master: dict[str, Any]) -> None:
    config = LLMConfig(analyze=[ChainEntry("openai", "gpt")], tailor=[ChainEntry("openai", "gpt")])

    with pytest.raises(TailorError) as caught:
        service(tmp_path, master, config).tailor(
            posting="Backend Engineer.", profile="software-engineer", language="pt-BR"
        )

    assert caught.value.code == CONFIGURATION_ERROR
