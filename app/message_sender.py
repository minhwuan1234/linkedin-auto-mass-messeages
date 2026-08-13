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
    print("")            index
        )

        try:
            if candidate.is_visible():
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


# =========================================================
# FIND SALES NAVIGATOR POPUP
# =========================================================

def find_sales_navigator_popup(
    page: Page,
) -> Locator | None:
    """
    Return the visible Sales Navigator popup marker
    if the promo is currently shown.
    """

    popup_markers = page.get_by_text(
        "Try Sales Navigator",
        exact=False,
    )

    count = popup_markers.count()

    for index in range(count):
        candidate = popup_markers.nth(index)

        try:
            if candidate.is_visible():
                return candidate
        except Exception:
            continue

    return None


# =========================================================
# CLOSE SALES NAVIGATOR POPUP
# =========================================================

def close_sales_navigator_popup(
    page: Page,
) -> bool:
    """
    Close Sales Navigator promo if visible.

    Returns:
        True  = popup existed and was closed
        False = popup was not visible
    """

    popup_marker = find_sales_navigator_popup(
        page
    )

    if popup_marker is None:
        return False

    print("")
    print("==============================")
    print("SALES NAVIGATOR POPUP FOUND")
    print("==============================")

    close_button = None

    # -----------------------------------------------------
    # Case 1: normal Close button
    # -----------------------------------------------------

    close_candidates = page.get_by_role(
        "button",
        name="Close",
        exact=False,
    )

    for index in range(
        close_candidates.count()
    ):
        candidate = close_candidates.nth(
            index
        )

        try:
            if candidate.is_visible():
                close_button = candidate
                break
        except Exception:
            continue

    # -----------------------------------------------------
    # Case 2: aria-label close
    # -----------------------------------------------------

    if close_button is None:
        close_candidates = page.locator(
            '[aria-label*="close" i]'
        )

        for index in range(
            close_candidates.count()
        ):
            candidate = close_candidates.nth(
                index
            )

            try:
                if candidate.is_visible():
                    close_button = candidate
                    break
            except Exception:
                continue

    # -----------------------------------------------------
    # Case 3: button inside popup container
    # -----------------------------------------------------

    if close_button is None:
        popup_container = popup_marker.locator(
            "xpath=ancestor::div[1]"
        )

        for _ in range(6):
            buttons = popup_container.locator(
                'button, [role="button"]'
            )

            for index in range(
                buttons.count()
            ):
                candidate = buttons.nth(
                    index
                )

                try:
                    if candidate.is_visible():
                        text = (
                            candidate
                            .inner_text()
                            .strip()
                        )

                        aria_label = (
                            candidate
                            .get_attribute(
                                "aria-label"
                            )
                            or ""
                        )

                        if (
                            "close" in aria_label.lower()
                            or text in {"×", "✕", "X"}
                        ):
                            close_button = candidate
                            break

                except Exception:
                    continue

            if close_button is not None:
                break

            popup_container = (
                popup_container.locator(
                    "xpath=.."
                )
            )

    if close_button is None:
        raise RuntimeError(
            "Sales Navigator popup appeared "
            "but its close button was not found."
        )

    close_button.click(
        force=True,
    )

    page.wait_for_timeout(
        700
    )

    print("Sales Navigator popup closed.")
    print("")

    return True


# =========================================================
# OPEN MESSAGE COMPOSER
# =========================================================

def open_message_composer(
    page: Page,
) -> None:
    """
    Click Message until the real message composer opens.

    LinkedIn may show the Sales Navigator promo
    multiple times consecutively.

    We close it and retry Message until no promo appears.
    """

    for attempt in range(
        1,
        MAX_MESSAGE_ATTEMPTS + 1,
    ):
        print("")
        print("==============================")
        print(
            f"MESSAGE ATTEMPT {attempt}"
        )
        print("==============================")

        message_action = (
            find_profile_message_action(
                page
            )
        )

        message_action.scroll_into_view_if_needed()

        print("Clicking Message...")

        message_action.click(
            force=True,
        )

        page.wait_for_timeout(
            1_000
        )

        popup_closed = (
            close_sales_navigator_popup(
                page
            )
        )

        if popup_closed:
            print(
                "Promo interrupted Message."
            )
            print(
                "Retrying Message..."
            )

            page.wait_for_timeout(
                500
            )

            continue

        print("")
        print("==============================")
        print("MESSAGE COMPOSER SHOULD BE OPEN")
        print("==============================")
        print("")

        return

    raise RuntimeError(
        "Could not open Message composer "
        f"after {MAX_MESSAGE_ATTEMPTS} attempts."
    )
