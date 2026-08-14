from __future__ import annotations

from playwright.sync_api import (
    Locator,
    Page,
)


# =========================================================
# SCROLL REAL LINKEDIN CONTAINER
# =========================================================

def scroll_profile_to_bottom(
    page: Page,
) -> None:
    """
    LinkedIn hiện tại có thể không scroll bằng window.
    Function này tìm element thực sự có vertical scroll
    rồi ép nó xuống cuối.
    """

    print("")
    print("==============================")
    print("FINDING SCROLL CONTAINER")
    print("==============================")

    result = page.evaluate(
        """
        () => {
            const elements = Array.from(
                document.querySelectorAll("*")
            );

            const candidates = [];

            for (const element of elements) {
                const style = window.getComputedStyle(
                    element
                );

                const overflowY = style.overflowY;

                const scrollable =
                    (
                        overflowY === "auto" ||
                        overflowY === "scroll"
                    ) &&
                    element.scrollHeight >
                    element.clientHeight + 200;

                if (!scrollable) {
                    continue;
                }

                candidates.push({
                    element,
                    distance:
                        element.scrollHeight -
                        element.clientHeight
                });
            }

            candidates.sort(
                (a, b) =>
                    b.distance - a.distance
            );

            if (candidates.length > 0) {
                const target =
                    candidates[0].element;

                target.scrollTop =
                    target.scrollHeight;

                target.dispatchEvent(
                    new Event(
                        "scroll",
                        {
                            bubbles: true
                        }
                    )
                );

                return {
                    mode: "element",
                    tag: target.tagName,
                    className:
                        target.className || "",
                    scrollTop:
                        target.scrollTop,
                    scrollHeight:
                        target.scrollHeight,
                    clientHeight:
                        target.clientHeight
                };
            }

            const scrollingElement =
                document.scrollingElement;

            if (scrollingElement) {
                scrollingElement.scrollTop =
                    scrollingElement.scrollHeight;

                return {
                    mode: "document",
                    tag:
                        scrollingElement.tagName,
                    className:
                        scrollingElement.className
                        || "",
                    scrollTop:
                        scrollingElement.scrollTop,
                    scrollHeight:
                        scrollingElement.scrollHeight,
                    clientHeight:
                        scrollingElement.clientHeight
                };
            }

            return {
                mode: "not_found"
            };
        }
        """
    )

    print(
        f"Scroll mode   : "
        f"{result.get('mode')}"
    )

    print(
        f"Container tag : "
        f"{result.get('tag')}"
    )

    print(
        f"Scroll top    : "
        f"{result.get('scrollTop')}"
    )

    print(
        f"Scroll height : "
        f"{result.get('scrollHeight')}"
    )

    print(
        f"Client height : "
        f"{result.get('clientHeight')}"
    )

    print("")

    page.wait_for_timeout(
        1_500
    )


# =========================================================
# FIND STICKY NAV MESSAGE
# =========================================================

def find_sticky_message_action(
    page: Page,
) -> Locator:
    """
    Sticky profile Message của LinkedIn
    hiện tại là một <a> có href chứa:

        recipient=
        interop=msgOverlay

    Không dùng text Message chung nữa.
    """

    candidates = page.locator(
        'a[href*="recipient="]'
        '[href*="interop=msgOverlay"]'
    )

    visible_candidates: list[
        tuple[float, Locator]
    ] = []

    for index in range(
        candidates.count()
    ):
        candidate = candidates.nth(
            index
        )

        try:
            if not candidate.is_visible():
                continue

            box = candidate.bounding_box()

            if box is None:
                continue

            text = (
                candidate
                .inner_text()
                .strip()
            )

            href = (
                candidate
                .get_attribute(
                    "href"
                )
                or ""
            )

            if text != "Message":
                continue

            visible_candidates.append(
                (
                    box["y"],
                    candidate,
                )
            )

            print(
                "Sticky candidate | "
                f"y={box['y']} | "
                f"text={text!r} | "
                f"href={href}"
            )

        except Exception:
            continue

    if not visible_candidates:
        raise RuntimeError(
            "Sticky Message link with "
            "interop=msgOverlay was not found."
        )

    visible_candidates.sort(
        key=lambda item: item[0]
    )

    return visible_candidates[0][1]


# =========================================================
# OPEN MESSAGE COMPOSER
# =========================================================

def open_message_composer(
    page: Page,
) -> None:
    scroll_profile_to_bottom(
        page
    )

    message_action = (
        find_sticky_message_action(
            page
        )
    )

    box = message_action.bounding_box()

    href = (
        message_action
        .get_attribute(
            "href"
        )
        or ""
    )

    print("")
    print("==============================")
    print("STICKY MESSAGE FOUND")
    print("==============================")

    if box is not None:
        print(
            f"Position y: {box['y']}"
        )

    print(
        f"Href: {href}"
    )

    print("")
    print(
        "Clicking sticky Message..."
    )

    message_action.click(
        force=True,
    )

    page.wait_for_timeout(
        1_500
    )

    print("")
    print("==============================")
    print("STICKY MESSAGE CLICKED")
    print("==============================")
    print("")


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
        buttons = dialog.get_by_role(
            "button",
            name="Send",
            exact=True,
        )

        for index in range(
            buttons.count()
        ):
            button = buttons.nth(
                index
            )

            try:
                if button.is_visible():
                    return button

            except Exception:
                continue

    buttons = page.get_by_role(
        "button",
        name="Send",
        exact=True,
    )

    for index in range(
        buttons.count()
    ):
        button = buttons.nth(
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
        message.strip()
    )

    if not cleaned_message:
        raise ValueError(
            "Message cannot be empty."
        )

    # -----------------------------------------------------
    # 1. Open correct sticky Message
    # -----------------------------------------------------

    open_message_composer(
        page
    )

    page.wait_for_timeout(
        1_000
    )

    # -----------------------------------------------------
    # 2. Find textbox
    # -----------------------------------------------------

    textbox = find_message_textbox(
        page
    )

    print("")
    print("==============================")
    print("MESSAGE TEXTBOX FOUND")
    print("==============================")
    print("")

    # -----------------------------------------------------
    # 3. Fill message
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 4. Find Send
    # -----------------------------------------------------

    send_button = find_send_button(
        page,
        textbox,
    )

    print("==============================")
    print("SEND BUTTON FOUND")
    print("==============================")
    print("")

    # -----------------------------------------------------
    # 5. Send
    # -----------------------------------------------------

    send_button.click()

    page.wait_for_timeout(
        1_500
    )

    print("==============================")
    print("MESSAGE SENT")
    print("==============================")
    print("")
