import string
import asyncio
from datetime import datetime, timedelta
from patchright.async_api import async_playwright
from random_username.generate import generate_username

import random

TOR_SOCKS_PROXY = {"server": "socks5://127.0.0.1:9150"}  # current Tor connection
CHROMIUM_ARGS = [
    "--no-first-run",
    "--disable-blink-features=AutomationControlled",
    "--force-webrtc-ip-handling-policy",
]
email = "lozhkovilkin@gmail.com"
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


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=200,
            args=CHROMIUM_ARGS,
            ignore_default_args=["--enable-automation"],
        )
        context = await browser.new_context(
            proxy={"server": TOR_SOCKS_PROXY["server"]},
            ignore_https_errors=True,
            permissions=["geolocation"],
            locale="ru-RU",
        )

        page = await context.new_page()
        await page.goto("https://kick.com", timeout=1200000)
        login_button = page.get_by_test_id("login").first
        await login_button.click()

        registration_button = page.get_by_role("button", name="Регистрация")
        await registration_button.click()

        username = generate_username().pop()
        if not isinstance(username, str):
            raise Exception()

        global start_birthdate, end_birthdate, email
        birthdate = random_date(start_birthdate, end_birthdate).strftime("%m%d%Y")
        password = random_password()

        await page.locator('input[name="email"]').type(email)
        await page.locator('input[name="birthdate"]').type(birthdate)
        await page.locator('input[name="username"]').type(username)
        await page.locator('input[name="password"]').type(password)
        await page.locator('input[name="password"]').type(password)
        registration_button = page.get_by_role("button", name="Зарегистрироваться")
        await registration_button.click()
        code = input("Enter recieved code:")
        await page.locator('input[name="code"]').wait_for(
            state="visible", timeout=15000
        )
        await page.locator('input[name="code"]').type(code)
        await page.wait_for_timeout(60000)

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
