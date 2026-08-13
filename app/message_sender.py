from __future__ import annotations

from playwright.sync_api import (
    Locator,
    Page,
)


def find_profile_message_action(
    page: Page,
) -> Locator:
    """
    Find the Message action in the main LinkedIn profile header.

    LinkedIn hiện tại render Message action với SVG:
        id="send-privately-medium"
    """

    message_icon = page.locator(
        'svg#send-privately-medium'
    ).first

    message_icon.wait_for(
        state="visible",
        timeout=15_000,
    )

    return message_icon


def open_message_composer(
    page: Page,
) -> None:
    message_icon = (
        find_profile_message_action(
            page
        )
    )

    print("")
    print("==============================")
    print("MESSAGE ACTION FOUND")
    print("==============================")
    print("Clicking profile Message action...")
    print("")

    message_icon.click()

    page.wait_for_timeout(
        1_500
    )

    print("==============================")
    print("MESSAGE ACTION CLICKED")
    print("==============================")
    print("")
