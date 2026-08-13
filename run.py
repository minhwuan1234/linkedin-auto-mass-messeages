from pathlib import Path

from app.browser import LinkedInBrowser
from app.message_template import build_message
from app.profile import get_profile_name
from app.message_sender import open_message_composer

PROJECT_ROOT = Path(
    __file__
).resolve().parent

INPUT_FILE = (
    PROJECT_ROOT
    / "input"
    / "urls.txt"
)

LINKEDIN_LOGIN_URL_PARTS = (
    "/login",
    "/checkpoint",
    "/challenge",
    "/authwall",
    "/uas/login",
)


def load_urls() -> list[str]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    raw_lines = INPUT_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    urls: list[str] = []
    seen: set[str] = set()

    for raw_line in raw_lines:
        url = raw_line.strip()

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)
        urls.append(url)

    return urls


def requires_login(
    current_url: str,
) -> bool:
    url = (
        current_url
        or ""
    ).lower()

    return any(
        part in url
        for part in LINKEDIN_LOGIN_URL_PARTS
    )


def wait_for_manual_login(
    browser: LinkedInBrowser,
    target_url: str,
) -> None:
    print("")
    print("==============================")
    print("LINKEDIN LOGIN REQUIRED")
    print("==============================")
    print("")
    print("Login manually in the browser.")
    print("Complete verification if needed.")
    print("Wait until the LinkedIn feed is visible.")
    print("")

    input(
        "When login is finished, press ENTER here..."
    )

    print("")
    print("Opening target profile again...")
    print("")

    browser.open(
        target_url
    )


def main() -> None:
    urls = load_urls()

    if not urls:
        raise RuntimeError(
            "No LinkedIn URLs found."
        )

    test_url = urls[0]

    print("")
    print("==============================")
    print("PROFILE NAME TEST")
    print("==============================")
    print(f"URL: {test_url}")
    print("")

    browser = LinkedInBrowser()

    try:
        browser.start()

        page = browser.open(
            test_url
        )

        if requires_login(
            page.url
        ):
            wait_for_manual_login(
                browser,
                test_url,
            )

            page = browser.page

        profile = get_profile_name(
            page
        )

        print("")
        print("==============================")
        print("PROFILE FOUND")
        print("==============================")
        print(
            f"Full name : {profile['full_name']}"
        )
        print(
            f"First name: {profile['first_name']}"
        )
        print("")

        message = build_message(
            profile["first_name"]
        )

        print("==============================")
        print("MESSAGE PREVIEW")
        print("==============================")
        print(message)
        print("")

        input(
            "Press ENTER to close browser..."
        )
        open_message_composer(
        page
        )

        input(
            "Check that the correct Message composer is open. "
            "Press ENTER to close browser..."
        )

    finally:
        browser.stop()


if __name__ == "__main__":
    main()
