from __future__ import annotations

from playwright.sync_api import Locator, Page


MAX_SCROLL_ATTEMPTS = 8
SCROLL_DISTANCE = 600


def find_visible_nav_message_action(
    page: Page,
) -> Locator | None:
    """
    Tìm Message action trên sticky profile navigation.

    Chỉ trả về element nếu nó đang visible.
    """

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

    return None


def scroll_until_nav_message_visible(
    page: Page,
) -> Locator:
    """
    Scroll xuống từng đoạn cho tới khi
    sticky navigation bar xuất hiện.
    """

    print("")
    print("==============================")
    print("SCROLLING PROFILE")
    print("==============================")

    for attempt in range(
        1,
        MAX_SCROLL_ATTEMPTS + 1,
    ):
        message_action = (
            find_visible_nav_message_action(
                page
            )
        )

        if message_action is not None:
            print(
                f"Sticky Message found "
                f"after {attempt - 1} scroll(s)."
            )
            print("")

            return message_action

        print(
            f"Scroll attempt {attempt}..."
        )

        page.mouse.wheel(
            0,
            SCROLL_DISTANCE,
        )

        page.wait_for_timeout(
            700
        )

    message_action = (
        find_visible_nav_message_action(
            page
        )
    )

    if message_action is not None:
        return message_action

    raise RuntimeError(
        "Sticky Message action did not appear "
        "after scrolling down the profile."
    )


def open_message_composer(
    page: Page,
) -> None:
    """
    Scroll xuống profile cho đến khi sticky nav hiện,
    sau đó click Message trên sticky nav.
    """

    message_action = (
        scroll_until_nav_message_visible(
            page
        )
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

    print("==============================")
    print("NAV MESSAGE ACTION FOUND")
    print("==============================")
    print(f"Text: {text}")
    print(f"Href: {href}")
    print("")

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
