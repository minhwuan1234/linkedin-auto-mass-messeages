from app.browser import LinkedInBrowser


def main() -> None:
    browser = LinkedInBrowser()

    try:
        page = browser.start()

        page.goto(
            "https://www.linkedin.com/",
            wait_until="domcontentloaded",
        )

        print("")
        print("==============================")
        print("LINKEDIN PROFILE SETUP")
        print("==============================")
        print("")
        print("1. Login LinkedIn manually.")
        print("2. Complete any verification if needed.")
        print("3. Make sure LinkedIn home/feed is visible.")
        print("")
        input(
            "When login is complete, "
            "press ENTER here to close the browser..."
        )

    finally:
        browser.stop()


if __name__ == "__main__":
    main()
