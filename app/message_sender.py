from __future__ import annotations

from playwright.sync_api import Locator, Page


def scroll_to_middle_of_profile(
    page: Page,
) -> None:
    """
    Scroll xuống giữa trang để LinkedIn
    hiện sticky profile navigation bar.
    """

    page.evaluate(
        """
        window.scrollTo({
            top: document.body.scrollHeight * 0.45,
            behavior: "instant"
        });
        """
    )

    page.wait_for_timeout(
        1_000
    )


def find_nav_message_action(
    page: Page,
) -> Locator:
    """
    Find the Message action from LinkedIn's
    sticky profile navigation bar.
    """

    scroll_to_middle_of_profile(
        page
    )

    candidates = page.locator(
        'a[href*="recipient="][href*="interop=msgOverlay"]'
    )

    candidate_count = candidates.count()

    for index in range(candidate_count):
        candidate = candidates.nth(index)

        try:
            if not candidate.is_visible():
                continue

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
    Scroll profile, find sticky-nav Message action,
    then open the LinkedIn message composer.
    """

    print("")
    print("==============================")
    print("SCROLLING PROFILE")
    print("==============================")
    print(
        "Scrolling to middle of profile "
        "to reveal sticky navigation..."
    )

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

    page.wait_for_timeout(
        300
    )

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
