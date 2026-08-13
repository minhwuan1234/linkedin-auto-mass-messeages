from __future__ import annotations

from playwright.sync_api import Page


def get_profile_name(
    page: Page,
) -> dict[str, str]:

    name_locator = page.locator(
        "main h1"
    ).first

    if name_locator.count() == 0:
        name_locator = page.locator(
            "h1"
        ).first

    name_locator.wait_for(
        state="visible",
        timeout=15_000,
    )

    full_name = (
        name_locator
        .inner_text()
        .strip()
    )

    if not full_name:
        raise RuntimeError(
            "Profile header name not found."
        )

    first_name = (
        full_name
        .split()[0]
        .strip()
    )

    return {
        "full_name": full_name,
        "first_name": first_name,
    }
