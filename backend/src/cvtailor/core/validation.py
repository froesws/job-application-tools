"""Selection validation.

The renderer is the authority on what a selection may contain, because it is the
component that would fail. This module calls it with the renderer's vocabulary and
converts its messages into typed problems the API and the CLI can serialize.
"""

from __future__ import annotations

from typing import Any

from cvtailor.core.errors import INVALID_SELECTION, Problem
from cvtailor.core.render_pdf import validate_selection as renderer_validate
from cvtailor.core.selection import Selection, to_renderer


def validate_selection(master: dict[str, Any], selection: Selection) -> list[Problem]:
    """Return the problems that block a render, empty when the selection is valid."""
    return [_to_problem(message) for message in renderer_validate(master, to_renderer(selection))]


def _to_problem(message: str) -> Problem:
    return Problem(code=INVALID_SELECTION, message=message, item_id=_item_id(message))


def _item_id(message: str) -> str | None:
    """Extract the offending id from the renderer's message, when it names one.

    The renderer ends its item-level messages with the id after a colon; count
    messages do not, and return no id.
    """
    if ": " not in message:
        return None
    return message.rsplit(": ", 1)[-1]
