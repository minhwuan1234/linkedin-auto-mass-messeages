from __future__ import annotations

from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)


# =========================================================
# BROWSER PROFILE
# =========================================================

PROFILE_ROOT = (
    Path.home()
    / ".linkedin-auto-mass-messeages"
    / "browser_profiles"
)

PROFILE_DIR = (
    PROFILE_ROOT
    / "linkedin_main"
)


# =========================================================
# BROWSER
# =========================================================

class LinkedInBrowser:
    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError(
                "LinkedIn browser has not been started."
            )

        return self._page

    def start(self) -> Page:
        if self._context is not None:
            return self.page

        PROFILE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(
            f"Browser profile: {PROFILE_DIR}"
        )

        self._playwright = (
            sync_playwright().start()
        )

        try:
            self._context = (
                self._playwright
                .chromium
                .launch_persistent_context(
                    user_data_dir=str(PROFILE_DIR),
                    headless=False,
                    viewport={
                        "width": 1440,
                        "height": 1000,
                    },
                    locale="en-US",
                    args=[
                        "--disable-dev-shm-usage",
                        "--no-default-browser-check",
                        "--disable-popup-blocking",
                    ],
                )
            )

        except Exception:
            self._playwright.stop()
            self._playwright = None
            raise

        self._context.set_default_timeout(
            15_000
        )

        self._context.set_default_navigation_timeout(
            45_000
        )

        existing_pages = (
            self._context.pages
        )

        if existing_pages:
            self._page = existing_pages[0]

        else:
            self._page = (
                self._context.new_page()
            )

        return self._page

    def open(
        self,
        url: str,
    ) -> Page:
        cleaned_url = str(
            url or ""
        ).strip()

        if not cleaned_url:
            raise ValueError(
                "LinkedIn URL cannot be empty."
            )

        page = self.page

        page.goto(
            cleaned_url,
            wait_until="domcontentloaded",
            timeout=45_000,
        )

        page.wait_for_timeout(
            1_500
        )

        return page

    def stop(self) -> None:
        if self._context is not None:
            try:
                self._context.close()
            finally:
                self._context = None
                self._page = None

        if self._playwright is not None:
            try:
                self._playwright.stop()
            finally:
                self._playwright = None
