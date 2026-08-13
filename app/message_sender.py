from __future__ import annotations

from playwright.sync_api import Locator, Page


# =========================================================
# FIND MESSAGE ACTION
# =========================================================

def find_profile_message_action(
    page: Page,
) -> Locator:
    """
    Find the clickable Message action
    in the LinkedIn profile header.
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


# =========================================================
# SALES NAVIGATOR POPUP
# =========================================================

def close_sales_navigator_popup(
    page: Page,
) -> bool:
    """
    Detect the Sales Navigator promo popup.

    Return:
        True  -> popup found and closed
        False -> popup not present
    """

    popup_text = page.get_by_text(
        "Try Sales Navigator",
        exact=False,
    )

    try:
        popup_text.first.wait_for(
            state="visible",
            timeout=2_500,
        )

    except Exception:
        return False

    print("")
    print("==============================")
    print("SALES NAVIGATOR POPUP FOUND")
    print("==============================")
    print("Closing popup...")
    print("")

    # ---------------------------------------------
    # Find the popup container first.
    # ---------------------------------------------

    popup_container = (
        popup_text
        .first
        .locator(
            "xpath=ancestor::div["
            ".//button or .//*[@role='button']"
            "][1]"
        )
    )

    close_button = None

    # ---------------------------------------------
    # Case 1 — accessible Close button
    # ---------------------------------------------

    possible_close = page.get_by_role(
        "button",
        name="Close",
        exact=False,
    )

    if possible_close.count() > 0:
        close_button = (
            possible_close
            .filter(
                visible=True
            )
            .first
        )

    # ---------------------------------------------
    # Case 2 — aria-label close
    # ---------------------------------------------

    if close_button is None:
        possible_close = page.locator(
            'button[aria-label*="close" i]'
        )

        if possible_close.count() > 0:
            close_button = possible_close.first

    # ---------------------------------------------
    # Case 3 — role button inside popup container
    # Use the top-right button.
    # ---------------------------------------------

    if close_button is None:
        popup_buttons = popup_container.locator(
            'button, [role="button"]'
        )

        if popup_buttons.count() > 0:
            close_button = popup_buttons.first

    if close_button is None:
        raise RuntimeError(
            "Sales Navigator popup appeared "
            "but close button was not found."
        )

    close_button.click(
        force=True,
    )

    page.wait_for_timeout(
        800
    )

    print("==============================")
    print("SALES NAVIGATOR POPUP CLOSED")
    print("==============================")
    print("")

    return True


# =========================================================
# OPEN MESSAGE COMPOSER
# =========================================================

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

    # =====================================================
    # FIRST CLICK
    # =====================================================

    print("Clicking Message...")

    message_action.click(
        force=True,
    )

    page.wait_for_timeout(
        1_000
    )

    # =====================================================
    # CHECK SALES NAVIGATOR PROMO
    # =====================================================

    popup_was_closed = (
        close_sales_navigator_popup(
            page
        )
    )

    # =====================================================
    # SECOND CLICK ONLY IF POPUP APPEARED
    # =====================================================

    if popup_was_closed:
        print(
            "Clicking Message again "
            "after closing popup..."
        )

        page.wait_for_timeout(
            500
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
            1_500
        )

    print("")
    print("==============================")
    print("MESSAGE ACTION COMPLETED")
    print("==============================")
    print("")
