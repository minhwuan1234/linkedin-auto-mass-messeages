from __future__ import annotations


DEFAULT_MESSAGE_TEMPLATE = """Hi {first_name},

I wanted to reach out regarding...
"""


def build_message(
    first_name: str,
    template: str | None = None,
) -> str:
    cleaned_first_name = (
        first_name
        .strip()
    )

    if not cleaned_first_name:
        raise ValueError(
            "First name cannot be empty."
        )

    active_template = (
        template
        if template is not None
        else DEFAULT_MESSAGE_TEMPLATE
    )

    if not active_template.strip():
        raise ValueError(
            "Message template cannot be empty."
        )

    return active_template.format(
        first_name=cleaned_first_name
    )
