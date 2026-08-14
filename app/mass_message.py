from __future__ import annotations

from collections.abc import Callable

from app.browser import LinkedInBrowser
from app.message_sender import send_message
from app.message_template import build_message
from app.profile import get_profile_name


ProgressCallback = Callable[
    [dict],
    None,
]


def normalize_urls(
    urls: list[str],
) -> list[str]:
    cleaned_urls: list[str] = []
    seen: set[str] = set()

    for raw_url in urls:
        url = (
            str(raw_url or "")
            .strip()
        )

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)
        cleaned_urls.append(url)

    return cleaned_urls


def run_mass_message(
    urls: list[str],
    progress_callback: ProgressCallback | None = None,
) -> list[dict]:
    clean_urls = normalize_urls(
        urls
    )

    if not clean_urls:
        raise ValueError(
            "No LinkedIn URLs provided."
        )

    browser = LinkedInBrowser()

    results: list[dict] = []

    total = len(
        clean_urls
    )

    try:
        browser.start()

        for index, profile_url in enumerate(
            clean_urls,
            start=1,
        ):
            result = {
                "index": index,
                "total": total,
                "url": profile_url,
                "full_name": "",
                "first_name": "",
                "message": "",
                "status": "processing",
                "error": "",
            }

            if progress_callback is not None:
                progress_callback(
                    result.copy()
                )

            try:
                page = browser.open(
                    profile_url
                )

                profile = get_profile_name(
                    page
                )

                result["full_name"] = (
                    profile["full_name"]
                )

                result["first_name"] = (
                    profile["first_name"]
                )

                message = build_message(
                    profile["first_name"]
                )

                result["message"] = (
                    message
                )

                send_message(
                    page,
                    message,
                )

                result["status"] = "sent"

            except Exception as exc:
                result["status"] = "failed"
                result["error"] = str(
                    exc
                )

            results.append(
                result.copy()
            )

            if progress_callback is not None:
                progress_callback(
                    result.copy()
                )

        return results

    finally:
        browser.stop()
