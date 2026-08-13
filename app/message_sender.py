from __future__ import annotations

from playwright.sync_api import Locator, Page


def find_nav_message_action(
    page: Page,
) -> Locator:
    """
    Find the Message action from LinkedIn's
    sticky profile navigation bar.
    """

    # Scroll xuống để sticky profile navigation xuất hiện.
    page.mouse.wheel(
        0,
        500,
    )

    page.wait_for_timeout(
        800
    )

    candidates = page.locator(
        'a[href*="recipient="][href*="interop=msgOverlay"]'
    )

    candidate_count = candidates.count()

    for index in range(candidate_count):
        candidate = candidates.nth(index)

        try:
            if candidate.is_visible():
                text = (
                    candidate
                    .inner_text()
                    .strip()
                )

                if "Message" in text:
                    return candidate

        except Exception:
            continue

    raise RuntimeError(
        "Could not find Message action "
        "in sticky profile navigation."
    )


def open_message_composer(
    page: Page,
) -> None:
    """
    Open LinkedIn Message composer using
    the Message action in the sticky profile nav.
    """

    message_action = find_nav_message_action(
        page
    )

    text = (
        message_action
        .inner_text()
        .strip()
    )

    href = (
        message_action
        .get_attribute(
            "href"
        )
        or ""
    )

    print("")
    print("==============================")
    print("NAV MESSAGE ACTION FOUND")
    print("==============================")
    print(f"Text: {text}")
    print(f"Href: {href}")
    print("")

    message_action.scroll_into_view_if_needed()

    print(
        "Clicking Message from sticky nav..."
    )

    message_action.click()

    page.wait_for_timeout(
        1_500
    )

    print("")
    print("==============================")
    print("NAV MESSAGE ACTION CLICKED")
    print("==============================")
    print("")
