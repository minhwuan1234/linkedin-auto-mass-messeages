from __future__ import annotations

from playwright.sync_api import Locator, Page


def find_profile_message_action(
    page: Page,
) -> Locator:
    """
    Find the clickable Message action
    from the main LinkedIn profile header.
    """

    message_icon = page.locator(
        'svg#send-privately-medium'
    ).first

    message_icon.wait_for(
        state="visible",
        timeout=15_000,
    )

    clickable_parent = message_icon.locator(
        'xpath=ancestor::*['
        '@role="button" '
        'or self::button '
        'or self::a'
        '][1]'
    )

    if clickable_parent.count() > 0:
        return clickable_parent.first

    parent = message_icon.locator(
        "xpath=.."
    )

    parent_text = (
        parent
        .inner_text()
        .strip()
    )

    if "Message" in parent_text:
        return parent

    raise RuntimeError(
        "Could not find clickable Message action."
    )


def open_message_composer(
    page: Page,
) -> None:
    message_action = find_profile_message_action(
        page
    )

    tag_name = message_action.evaluate(
        "(el) => el.tagName"
    )

    text = (
        message_action
        .inner_text()
        .strip()
    )

    print("")
    print("==============================")
    print("MESSAGE ACTION FOUND")
    print("==============================")
    print(f"Tag : {tag_name}")
    print(f"Text: {text}")
    print("")

    message_action.scroll_into_view_if_needed()

    message_action.click(
        force=True
    )

    page.wait_for_timeout(
        2_000
    )

    print("==============================")
    print("MESSAGE ACTION CLICKED")
    print("==============================")
    print("")
    parent_text = (
        parent
        .inner_text()
        .strip()
    )

    if "Message" in parent_text:
        return parent

    raise RuntimeError(
        "Could not find clickable Message action."
    )


def open_message_composer(
    page: Page,
) -> None:
    message_action = (
        find_profile_message_action(
            page
        )
    )

    print("")
    print("==============================")
    print("MESSAGE ACTION FOUND")
    print("==============================")
    print(
        "Tag:",
        message_action.evaluate(
            "(el) => el.tagName"
        ),
    )
    print(
        "Text:",
        message_action.inner_text(),
    )
    print("")

    message_action.scroll_into_view_if_needed()

    message_action.click(
        force=True,
    )

    page.wait_for_timeout(
        2_000
    )

    print("==============================")
    print("MESSAGE ACTION CLICKED")
    print("==============================")
    print("")        )
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
