from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.browser import LinkedInBrowser
from app.message_sender import send_message
from app.message_template import build_message
from app.profile import get_profile_name


ProgressEvent = dict[str, Any]

ProgressCallback = Callable[
    [ProgressEvent],
    None,
]


# =========================================================
# URL NORMALIZATION
# =========================================================

def normalize_urls(
    urls: list[str],
) -> list[str]:
    """
    Clean URL input from the UI.

    - bỏ dòng trống
    - trim whitespace
    - bỏ duplicate
    - giữ nguyên thứ tự user nhập
    """

    cleaned_urls: list[str] = []
    seen: set[str] = set()

    for raw_url in urls:
        url = str(
            raw_url or ""
        ).strip()

        if not url:
            continue

        if url in seen:
            continue

        seen.add(
            url
        )

        cleaned_urls.append(
            url
        )

    return cleaned_urls


# =========================================================
# PROGRESS EVENT
# =========================================================

def emit_progress(
    callback: ProgressCallback | None,
    event: ProgressEvent,
) -> None:
    """
    Gửi trạng thái hiện tại về backend/UI.

    Nếu chưa có callback thì bỏ qua.
    """

    if callback is None:
        return

    callback(
        event.copy()
    )


# =========================================================
# SINGLE PROFILE
# =========================================================

def process_profile(
    browser: LinkedInBrowser,
    profile_url: str,
    template: str,
    index: int,
    total: int,
    progress_callback: ProgressCallback | None = None,
) -> ProgressEvent:
    """
    Xử lý một LinkedIn profile:

    URL
    -> mở profile
    -> lấy tên header
    -> lấy first_name
    -> build message
    -> gửi message
    -> trả result
    """

    result: ProgressEvent = {
        "index": index,
        "total": total,
        "url": profile_url,
        "full_name": "",
        "first_name": "",
        "message": "",
        "status": "processing",
        "step": "opening_profile",
        "error": "",
    }

    emit_progress(
        progress_callback,
        result,
    )

    try:
        # =================================================
        # STEP 1 — OPEN PROFILE
        # =================================================

        page = browser.open(
            profile_url
        )

        result["step"] = (
            "reading_profile"
        )

        emit_progress(
            progress_callback,
            result,
        )

        # =================================================
        # STEP 2 — READ HEADER NAME
        # =================================================

        profile = get_profile_name(
            page
        )

        full_name = str(
            profile.get(
                "full_name",
                "",
            )
        ).strip()

        first_name = str(
            profile.get(
                "first_name",
                "",
            )
        ).strip()

        if not full_name:
            raise RuntimeError(
                "LinkedIn profile name was empty."
            )

        if not first_name:
            raise RuntimeError(
                "LinkedIn first name was empty."
            )

        result["full_name"] = (
            full_name
        )

        result["first_name"] = (
            first_name
        )

        result["step"] = (
            "building_message"
        )

        emit_progress(
            progress_callback,
            result,
        )

        # =================================================
        # STEP 3 — BUILD PERSONALIZED MESSAGE
        # =================================================

        message = build_message(
            first_name,
            template,
        )

        result["message"] = (
            message
        )

        result["step"] = (
            "sending_message"
        )

        emit_progress(
            progress_callback,
            result,
        )

        # =================================================
        # STEP 4 — SEND
        # =================================================

        send_message(
            page,
            message,
        )

        # =================================================
        # COMPLETE
        # =================================================

        result["status"] = "sent"
        result["step"] = "completed"

        emit_progress(
            progress_callback,
            result,
        )

        return result

    except Exception as exc:
        result["status"] = "failed"
        result["step"] = "failed"
        result["error"] = str(
            exc
        )

        emit_progress(
            progress_callback,
            result,
        )

        return result


# =========================================================
# MASS MESSAGE
# =========================================================

def run_mass_message(
    urls: list[str],
    template: str,
    progress_callback: ProgressCallback | None = None,
) -> list[ProgressEvent]:
    """
    Main mass messaging flow.

    User input:
        URLs + template

    Flow:
        normalize URLs
        -> start browser once
        -> process profiles sequentially
        -> send progress to UI
        -> return all results

    Không có input() hoặc manual ENTER.
    """

    clean_urls = normalize_urls(
        urls
    )

    if not clean_urls:
        raise ValueError(
            "No LinkedIn URLs provided."
        )

    cleaned_template = str(
        template or ""
    ).strip()

    if not cleaned_template:
        raise ValueError(
            "Message template cannot be empty."
        )

    if (
        "{first_name}"
        not in cleaned_template
    ):
        raise ValueError(
            "Message template must contain "
            "{first_name}."
        )

    total = len(
        clean_urls
    )

    results: list[
        ProgressEvent
    ] = []

    browser = LinkedInBrowser()

    # =====================================================
    # JOB START
    # =====================================================

    emit_progress(
        progress_callback,
        {
            "index": 0,
            "total": total,
            "url": "",
            "full_name": "",
            "first_name": "",
            "message": "",
            "status": "running",
            "step": "starting_browser",
            "error": "",
        },
    )

    try:
        # =================================================
        # START BROWSER ONCE
        # =================================================

        browser.start()

        emit_progress(
            progress_callback,
            {
                "index": 0,
                "total": total,
                "url": "",
                "full_name": "",
                "first_name": "",
                "message": "",
                "status": "running",
                "step": "browser_ready",
                "error": "",
            },
        )

        # =================================================
        # PROCESS URL LIST
        # =================================================

        for index, profile_url in enumerate(
            clean_urls,
            start=1,
        ):
            result = process_profile(
                browser=browser,
                profile_url=profile_url,
                template=cleaned_template,
                index=index,
                total=total,
                progress_callback=progress_callback,
            )

            results.append(
                result
            )

        # =================================================
        # FINAL JOB EVENT
        # =================================================

        sent_count = sum(
            1
            for item in results
            if item.get(
                "status"
            ) == "sent"
        )

        failed_count = sum(
            1
            for item in results
            if item.get(
                "status"
            ) == "failed"
        )

        emit_progress(
            progress_callback,
            {
                "index": total,
                "total": total,
                "url": "",
                "full_name": "",
                "first_name": "",
                "message": "",
                "status": "completed",
                "step": "job_completed",
                "sent_count": sent_count,
                "failed_count": failed_count,
                "error": "",
            },
        )

        return results

    finally:
        # =================================================
        # ALWAYS CLOSE BROWSER
        # =================================================

        browser.stop()
