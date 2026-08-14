from __future__ import annotations

from playwright.sync_api import Locator, Page


MAX_POPUP_RETRIES = 5


# =========================================================
# PROFILE MESSAGE ACTION
# =========================================================

def find_profile_message_action(
    page: Page,
) -> Locator:
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
        "Profile Message action not found."
    )


# =========================================================
# SALES NAVIGATOR POPUP
# =========================================================

def close_sales_navigator_popup(
    page: Page,
) -> bool:
    popup_markers = page.get_by_text(
        "Try Sales Navigator",
        exact=False,
    )

    visible_popup = None

    for index in range(
        popup_markers.count()
    ):
        candidate = popup_markers.nth(index)

        try:
            if candidate.is_visible():
                visible_popup = candidate
                break

        except Exception:
            continue

    if visible_popup is None:
        return False

    print(
        "Sales Navigator popup detected."
    )

    close_candidates = page.locator(
        'button[aria-label*="close" i], '
        '[role="button"][aria-label*="close" i]'
    )

    for index in range(
        close_candidates.count()
    ):
        candidate = close_candidates.nth(
            index
        )

        try:
            if candidate.is_visible():
                candidate.click(
                    force=True,
                )

                page.wait_for_timeout(
                    700,
                )

                print(
                    "Sales Navigator popup closed."
                )

                return True

        except Exception:
            continue

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
            button = buttons.nth(
                index
            )

            try:
                if not button.is_visible():
                    continue

                aria_label = (
                    button
                    .get_attribute(
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
                        force=True,
                    )

                    page.wait_for_timeout(
                        700,
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
            force=True,
        )

        page.wait_for_timeout(
            1_000,
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
# MESSAGE TEXTBOX
# =========================================================

def find_message_textbox(
    page: Page,
) -> Locator:
    candidates = page.locator(
        '[contenteditable="true"][role="textbox"], '
        '[contenteditable="true"]'
    )

    for index in range(
        candidates.count()
    ):
        candidate = candidates.nth(
            index
        )

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
            button = send_buttons.nth(
                index
            )

            try:
                if button.is_visible():
                    return button

            except Exception:
                continue

    send_buttons = page.get_by_role(
        "button",
        name="Send",
        exact=True,
    )

    for index in range(
        send_buttons.count()
    ):
        button = send_buttons.nth(
            index
        )

        try:
            if button.is_visible():
                return button

        except Exception:
            continue

    raise RuntimeError(
        "Visible Send button not found."
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
        800,
    )

    textbox = find_message_textbox(
        page
    )

    textbox.click()

    textbox.fill(
        cleaned_message
    )

    page.wait_for_timeout(
        500,
    )

    print("")
    print("==============================")
    print("MESSAGE FILLED")
    print("==============================")
    print(cleaned_message)
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
        1_500,
    )

    print("")
    print("==============================")
    print("MESSAGE SENT")
    print("==============================")
    print("")
