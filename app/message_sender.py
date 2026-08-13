from __future__ import annotations

from playwright.sync_api import (
    Locator,
    Page,
)


def find_profile_message_button(
    page: Page,
) -> Locator:
    top_card = page.locator(
        'div[data-testid="lazy-column"]'
    ).first

    message_button = (
        top_card
        .get_by_role(
            "button",
            name="Message",
            exact=True,
        )
        .first
    )

    message_button.wait_for(
        state="visible",
        timeout=15_000,
    )

    return message_button


def open_message_composer(
    page: Page,
) -> None:
    message_button = (
        find_profile_message_button(
            page
        )
    )

    message_button.click()

    page.wait_for_timeout(
        1_000
    )

    print("")
    print("==============================")
    print("MESSAGE COMPOSER OPENED")
    print("==============================")
    print("")
