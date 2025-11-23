import logging
import string
import asyncio
from auth_manager.mail import MailConnection, create_email_accounts
from datetime import datetime, timedelta
from patchright.async_api import Response, async_playwright

from random_username.generate import generate_username
from core.settings import SETTINGS
import random

CHROMIUM_ARGS = [
    "--no-first-run",
    "--disable-blink-features=AutomationControlled",
    "--force-webrtc-ip-handling-policy",
]

start_birthdate = datetime.fromisocalendar(1995, 1, 1)
end_birthdate = datetime.fromisocalendar(2005, 1, 1)


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def random_password(length: int | None = None) -> str:
    if length is None:
        length = random.randint(16, 25)
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*"
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*"),
    ]
    for _ in range(length - len(password)):
        password.append(random.choice(chars))
    random.shuffle(password)
    return "".join(password)


async def register_user():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=200,
        )
        context = await browser.new_context(
            # proxy={"server": SETTINGS.TOR_SOCKS_PROXY["server"]},
            ignore_https_errors=True,
            permissions=["geolocation"],
            locale="en-US",
        )

        page = await context.new_page()
        await page.goto("https://kick.com", timeout=1200000)
        await page.wait_for_timeout(6000000)
        login_button = page.get_by_test_id("login").first
        await login_button.click()
        login_button = page.get_by_test_id("login").first
        await login_button.click()

        registration_button = page.get_by_role("button", name="Sign Up")
        await registration_button.click()

        username_fits = False

        def handle_response(response: Response):
            nonlocal username_fits
            if (
                "/api/v1/signup/verify/username" in response.url
                and response.status == 204
            ):
                username_fits = True

        page.on("response", handle_response)

        username = ""
        while not username_fits:
            username = generate_username().pop()
            if not isinstance(username, str):
                raise Exception()
            await page.locator('input[name="username"]').type(username)
            await asyncio.sleep(5)

        global start_birthdate, end_birthdate
        username = (await create_email_accounts([username])).pop()
        email = f"{username}@{SETTINGS.DOMAIN}"
        birthdate = random_date(start_birthdate, end_birthdate).strftime("%m%d%Y")
        password = random_password()

        await page.locator('input[name="email"]').type(email)
        await page.locator('input[name="birthdate"]').type(birthdate)
        await page.locator('input[name="password"]').type(password)
        registration_button = page.get_by_test_id("sign-up-submit")
        logging.debug(f"EMAIL: {email}")
        await registration_button.click()

        code = ""
        async with MailConnection(
            SETTINGS.DOMAIN,
            email,
            SETTINGS.DEFAULT_PASSWORD,
        ) as connection:
            logging.info("Listening for code message...")
            message = await connection.wait_new_message_from("noreply@email.kick.com")
            subject = message.get("subject")
            if not subject:
                raise Exception("Subject is empty")
            code = subject[:6]
            logging.info(f"Received, code is {code}")

        await page.locator('input[name="code"]').type(code)
        await page.wait_for_timeout(6000000)
        to_scroll = page.locator("div[class=markdown-policy-page]")

        button = page.locator("button[name=I accept]")  # or content
        button = page.get_by_text("I accept")

        # scroll untill active
        # press the button

        # await context.close()
        # await browser.close()


async def check_tor_proxy():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=200,
            args=CHROMIUM_ARGS,
            ignore_default_args=["--enable-automation"],
        )
        context = await browser.new_context(
            proxy={"server": SETTINGS.TOR_SOCKS_PROXY["server"]},
            ignore_https_errors=True,
            permissions=["geolocation"],
            locale="en-US",
        )

        page = await context.new_page()
        await page.goto("https://check.torproject.org/api/ip", timeout=1200000)
        await page.wait_for_timeout(12000)


async def main():
    await register_user()


if __name__ == "__main__":
    import core.log

    asyncio.run(main())
