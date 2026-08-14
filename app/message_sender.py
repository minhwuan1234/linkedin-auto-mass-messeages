from __future__ import annotations

from playwright.sync_api import (
    Locator,
    Page,
)


# =========================================================
# SCROLL
# =========================================================

def scroll_to_bottom(
    page: Page,
) -> None:
    """
    Scroll xuống cuối LinkedIn profile.

    Mục đích:
    khi header profile gốc ra khỏi viewport,
    LinkedIn sẽ hiển thị sticky profile navigation
    ở phía trên màn hình.
    """

    print("")
    print("==============================")
    print("SCROLL TO BOTTOM")
    print("==============================")

    # Focus page trước để keyboard action tác động
    # vào document hiện tại.
    page.locator("body").click(
        position={
            "x": 10,
            "y": 10,
        },
        force=True,
    )

    page.keyboard.press(
        "End"
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


# =========================================================
# FIND STICKY MESSAGE
# =========================================================

def find_sticky_message_action(
    page: Page,
) -> Locator:
    """
    Sau khi scroll xuống cuối:

    - Message ở profile header gốc thường không còn visible.
    - Sticky profile nav xuất hiện phía trên.
    - Tìm các clickable element có text chính xác "Message".
    - Chọn element visible có y nhỏ nhất.
    """

    candidates = page.locator(
        'a, button, [role="button"]'
    )

    visible_message_actions: list[
        tuple[float, Locator]
    ] = []

    candidate_count = (
        candidates.count()
    )

    for index in range(
        candidate_count
    ):
        candidate = candidates.nth(
            index
        )

        try:
            if not candidate.is_visible():
                continue

            text = (
                candidate
                .inner_text()
                .strip()
            )

            # Chỉ match Message.
            # Không match Messaging.
            if text != "Message":
                continue

            box = candidate.bounding_box()

            if box is None:
                continue

            visible_message_actions.append(
                (
                    box["y"],
                    candidate,
                )
            )

        except Exception:
            continue

    if not visible_message_actions:
        raise RuntimeError(
            "No visible Message action found "
            "after scrolling to bottom."
        )

    # Sticky nav nằm phía trên viewport.
    # Vì vậy chọn Message có y nhỏ nhất.
    visible_message_actions.sort(
        key=lambda item: item[0]
    )

    print("==============================")
    print("VISIBLE MESSAGE ACTIONS")
    print("==============================")

    for y_position, _ in (
        visible_message_actions
    ):
        print(
            f"Message action y={y_position}"
        )

    print("")

    return (
        visible_message_actions[0][1]
    )


# =========================================================
# OPEN MESSAGE COMPOSER
# =========================================================

def open_message_composer(
    page: Page,
) -> None:
    """
    Scroll xuống cuối profile,
    tìm Message trên sticky profile nav
    và click.
    """

    scroll_to_bottom(
        page
    )

    message_action = (
        find_sticky_message_action(
            page
        )
    )

    box = (
        message_action
        .bounding_box()
    )

    print("==============================")
    print("STICKY MESSAGE FOUND")
    print("==============================")

    if box is not None:
        print(
            f"Position y: {box['y']}"
        )

    print(
        "Clicking sticky Message..."
    )
    print("")

    message_action.click(
        force=True,
    )

    page.wait_for_timeout(
        1_500
    )

    print("==============================")
    print("STICKY MESSAGE CLICKED")
    print("==============================")
    print("")


# =========================================================
# FIND MESSAGE TEXTBOX
# =========================================================

def find_message_textbox(
    page: Page,
) -> Locator:
    """
    Find visible textbox của LinkedIn
    message composer.
    """

    candidates = page.locator(
        '[contenteditable="true"][role="textbox"], '
        '[contenteditable="true"]'
    )

    candidate_count = (
        candidates.count()
    )

    for index in range(
        candidate_count
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
# FIND SEND BUTTON
# =========================================================

def find_send_button(
    page: Page,
    textbox: Locator,
) -> Locator:
    """
    Tìm Send button thuộc đúng message composer.

    Ưu tiên tìm trong dialog chứa textbox.
    Nếu LinkedIn không dùng role=dialog,
    fallback tìm Send visible toàn page.
    """

    dialog = textbox.locator(
        'xpath=ancestor::*[@role="dialog"][1]'
    )

    if dialog.count() > 0:
        send_candidates = (
            dialog.get_by_role(
                "button",
                name="Send",
                exact=True,
            )
        )

        for index in range(
            send_candidates.count()
        ):
            button = (
                send_candidates.nth(
                    index
                )
            )

            try:
                if button.is_visible():
                    return button

            except Exception:
                continue

    # Fallback
    send_candidates = (
        page.get_by_role(
            "button",
            name="Send",
            exact=True,
        )
    )

    for index in range(
        send_candidates.count()
    ):
        button = (
            send_candidates.nth(
                index
            )
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
    """
    Full message flow:

    1. Scroll xuống cuối profile.
    2. Tìm sticky Message.
    3. Mở composer.
    4. Tìm textbox.
    5. Fill template.
    6. Tìm Send.
    7. Click Send.
    """

    cleaned_message = (
        message
        .strip()
    )

    if not cleaned_message:
        raise ValueError(
            "Message cannot be empty."
        )

    # -----------------------------------------
    # Open composer
    # -----------------------------------------

    open_message_composer(
        page
    )

    page.wait_for_timeout(
        800
    )

    # -----------------------------------------
    # Find textbox
    # -----------------------------------------

    textbox = (
        find_message_textbox(
            page
        )
    )

    print("==============================")
    print("MESSAGE TEXTBOX FOUND")
    print("==============================")
    print("")

    # -----------------------------------------
    # Fill message
    # -----------------------------------------

    textbox.click()

    textbox.fill(
        cleaned_message
    )

    page.wait_for_timeout(
        500
    )

    print("==============================")
    print("MESSAGE FILLED")
    print("==============================")
    print(cleaned_message)
    print("")

    # -----------------------------------------
    # Find Send
    # -----------------------------------------

    send_button = (
        find_send_button(
            page,
            textbox,
        )
    )

    print("==============================")
    print("SEND BUTTON FOUND")
    print("==============================")
    print("")

    # -----------------------------------------
    # Send
    # -----------------------------------------

    send_button.click()

    page.wait_for_timeout(
        1_500
    )

    print("==============================")
    print("MESSAGE SENT")
    print("==============================")
    print("")
