from __future__ import annotations


MESSAGE_TEMPLATE = """Hi {first_name},

I wanted to reach out regarding...
"""


def build_message(
    first_name: str,
) -> str:
    cleaned_first_name = (
        first_name
        .strip()
    )

    if not cleaned_first_name:
        raise ValueError(
            "First name cannot be empty."
        )

    return MESSAGE_TEMPLATE.format(
        first_name=cleaned_first_name
    )
