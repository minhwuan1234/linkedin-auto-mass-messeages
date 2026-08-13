from __future__ import annotations

from playwright.sync_api import Locator, Page


def scroll_to_profile_section(
    page: Page,
) -> None:
    targets = (
        "Experience",
        "Activity",
        "Education",
        "Highlights",
    )

    target = None
    target_name = None

    for name in targets:
        locator = page.get_by_text(
            name,
            exact=True,
        ).first

        try:
            if locator.count() > 0:
                target = locator
                target_name = name
                break
        except Exception:
            continue

    if target is None:
        raise RuntimeError(
            "Could not find a profile section "
            "to scroll to."
        )

    print("")
    print("==============================")
    print("SCROLL TARGET FOUND")
    print("==============================")
    print(f"Target: {target_name}")
    print("")

    target.evaluate(
        """
        element => {
            const rect = element.getBoundingClientRect();

            window.scrollTo({
                top: window.scrollY + rect.top - 150,
                behavior: "auto"
            });
        }
        """
    )

    page.wait_for_timeout(
        1_500
    )

    current_scroll = page.evaluate(
        "window.scrollY"
    )

    print(
        f"Current scrollY: {current_scroll}"
    )
    print("")


def find_nav_message_action(
    page: Page,
) -> Locator:
    """
    Find Message action in sticky profile nav.
    """

    scroll_to_profile_section(
        page
    )

    candidates = page.locator(
        'a[href*="recipient="][href*="interop=msgOverlay"]'
    )

    for index in range(
        candidates.count()
    ):
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
    message_action = (
        find_nav_message_action(
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
