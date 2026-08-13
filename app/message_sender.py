from __future__ import annotations

from playwright.sync_api import (
    Locator,
    Page,
)


MAX_POPUP_RETRIES = 5


# =========================================================
# PROFILE MESSAGE ACTION
# =========================================================

def find_profile_message_action(
    page: Page,
) -> Locator:
    """
    Find Message action directly from the
    main LinkedIn profile header.
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

    if "Message" in parent.inner_text():
        return parent

    raise RuntimeError(
        "Profile Message action not found."
    )


# =========================================================
# SALES NAVIGATOR POPUP
# =========================================================

def close_sales_navigator_popup(
    page: Page,
) -> bool:
    """
    Close Sales Navigator promo if present.

    Returns True when a popup was found and closed.
    """

    popup_text = page.get_by_text(
        "Try Sales Navigator",
        exact=False,
    )

    visible_popup = None

    for index in range(
        popup_text.count()
    ):
        candidate = popup_text.nth(index)

        try:
            if candidate.is_visible():
                visible_popup = candidate
                break
        except Exception:
            continue

    if visible_popup is None:
        return False

    print("Sales Navigator popup detected.")

    # First try accessible Close buttons.
    close_candidates = page.locator(
        'button[aria-label*="close" i], '
        '[role="button"][aria-label*="close" i]'
    )

    for index in range(
        close_candidates.count()
    ):
        candidate = close_candidates.nth(index)

        try:
            if candidate.is_visible():
                candidate.click(
                    force=True
                )

                page.wait_for_timeout(
                    700
                )

                print(
                    "Sales Navigator popup closed."
                )

                return True

        except Exception:
            continue

    # Fallback: search upward from popup text
    # and find a visible X/close action.
    container = visible_popup

    for _ in range(8):
        container = container.locator(
            "xpath=.."
        )

        buttons = container.locator(
            'button, [role="button"]'
        )

        for index in range(
            buttons.count()
        ):
            button = buttons.nth(index)

            try:
                if not button.is_visible():
                    continue

                aria_label = (
                    button.get_attribute(
                        "aria-label"
                    )
                    or ""
                ).lower()

                text = (
                    button
                    .inner_text()
                    .strip()
                )

                if (
                    "close" in aria_label
                    or text in {
                        "X",
                        "×",
                        "✕",
                    }
                ):
                    button.click(
                        force=True
                    )

                    page.wait_for_timeout(
                        700
                    )

                    print(
                        "Sales Navigator popup closed."
                    )

                    return True

            except Exception:
                continue

    raise RuntimeError(
        "Sales Navigator popup appeared "
        "but close action was not found."
    )


# =========================================================
# OPEN MESSAGE COMPOSER
# =========================================================

def open_message_composer(
    page: Page,
) -> None:
    """
    Keep clicking Message until LinkedIn
    stops showing the Sales Navigator promo.
    """

    for attempt in range(
        1,
        MAX_POPUP_RETRIES + 1,
    ):
        print("")
        print(
            f"Opening Message - attempt {attempt}"
        )

        message_action = (
            find_profile_message_action(
                page
            )
        )

        message_action.click(
            force=True
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
            continue

        return

    raise RuntimeError(
        "Message composer could not be opened."
    )


# =========================================================
# FIND MESSAGE TEXTBOX
# =========================================================

def find_message_textbox(
    page: Page,
) -> Locator:
    """
    Find visible LinkedIn message composer textbox.
    """

    candidates = page.locator(
        '[contenteditable="true"][role="textbox"], '
        '[contenteditable="true"]'
    )

    for index in range(
        candidates.count()
    ):
        candidate = candidates.nth(index)

        try:
            if candidate.is_visible():
                return candidate

        except Exception:
            continue

    raise RuntimeError(
        "Message textbox not found."
    )


# =========================================================
# SEND BUTTON
# =========================================================

def find_send_button(
    page: Page,
    textbox: Locator,
) -> Locator:
    """
    Prefer Send button belonging to the same
    message composer as the textbox.
    """

    dialog = textbox.locator(
        'xpath=ancestor::*[@role="dialog"][1]'
    )

    if dialog.count() > 0:
        send_buttons = dialog.get_by_role(
            "button",
            name="Send",
            exact=True,
        )

        for index in range(
            send_buttons.count()
        ):
            button = send_buttons.nth(index)

            try:
                if button.is_visible():
                    return button
            except Exception:
                continue

    # Fallback when LinkedIn does not use role=dialog.
    send_buttons = page.get_by_role(
        "button",
        name="Send",
        exact=True,
    )

    for index in range(
        send_buttons.count()
    ):
        button = send_buttons.nth(index)

        try:
            if button.is_visible():
                return button
        except Exception:
            continue

    raise RuntimeError(
        "Send button not found."
    )


# =========================================================
# SEND MESSAGE
# =========================================================

def send_message(
    page: Page,
    message: str,
) -> None:
    cleaned_message = (
        message
        .strip()
    )

    if not cleaned_message:
        raise ValueError(
            "Message cannot be empty."
        )

    open_message_composer(
        page
    )

    page.wait_for_timeout(
        800
    )

    textbox = find_message_textbox(
        page
    )

    print("")
    print("==============================")
    print("MESSAGE TEXTBOX FOUND")
    print("==============================")

    textbox.click()

    textbox.fill(
        cleaned_message
    )

    page.wait_for_timeout(
        500
    )

    print("")
    print("Message filled:")
    print("------------------------------")
    print(cleaned_message)
    print("------------------------------")
    print("")

    send_button = find_send_button(
        page,
        textbox,
    )

    print(
        "Send button found."
    )

    send_button.click()

    page.wait_for_timeout(
        1_500
    )

    print("")
    print("==============================")
    print("MESSAGE SENT")
    print("==============================")
    print("")        )

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
