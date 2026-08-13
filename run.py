from pathlib import Path

from app.browser import LinkedInBrowser
from app.profile import get_profile_name


PROJECT_ROOT = Path(
    __file__
).resolve().parent

INPUT_FILE = (
    PROJECT_ROOT
    / "input"
    / "urls.txt"
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

        profile = get_profile_name(
            page
        )

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

        input(
            "Press ENTER to close browser..."
        )

    finally:
        browser.stop()


if __name__ == "__main__":
    main()
