from pathlib import Path


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

    print("")
    print("==============================")
    print("LINKEDIN MASS MESSAGE")
    print("==============================")
    print(f"Loaded URLs: {len(urls)}")
    print("")

    for index, url in enumerate(
        urls,
        start=1,
    ):
        print(
            f"{index}. {url}"
        )


if __name__ == "__main__":
    main()
