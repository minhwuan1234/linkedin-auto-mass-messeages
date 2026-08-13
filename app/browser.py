from __future__ import annotations

from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROFILE_DIR = (
    PROJECT_ROOT
    / "browser_profiles"
    / "linkedin_main"
)


class LinkedInBrowser:
    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError(
                "Browser has not been started."
            )

        return self._page

    def start(self) -> Page:
        PROFILE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._playwright = sync_playwright().start()

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
            )
        )

        if self._context.pages:
            self._page = self._context.pages[0]

        else:
            self._page = self._context.new_page()

        self._page.set_default_timeout(
            15_000
        )

        self._page.set_default_navigation_timeout(
            45_000
        )

        return self._page

    def open(
        self,
        url: str,
    ) -> Page:
        page = self.page

        page.goto(
            url,
            wait_until="domcontentloaded",
        )

        page.wait_for_timeout(
            1000
        )

        return page

    def stop(self) -> None:
        if self._context is not None:
            self._context.close()

        if self._playwright is not None:
            self._playwright.stop()

        self._page = None
        self._context = None
        self._playwright = None
