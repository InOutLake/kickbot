import asyncio
import email
import logging
import ssl
from datetime import datetime, timedelta
from email.message import Message
from email.utils import parseaddr
from types import TracebackType
from typing import Set

import aiohttp
from aioimaplib import (
    IMAP4,
    IMAP4_PORT,
    IMAP4_SSL,
    IMAP4_SSL_PORT,
)

from core.settings import SETTINGS


class MailConnection:
    """
    Use as context manager
    """

    def __init__(self, host: str, email: str, password: str, secure: bool = True):
        self.host = host
        self.email = email
        self.password = password
        self.secure = secure

    async def __aenter__(self):
        if self.secure:
            # context setup to communicate with self signed ssl
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.mail = IMAP4_SSL(self.host, IMAP4_SSL_PORT, ssl_context=context)
        else:
            self.mail = IMAP4(self.host, IMAP4_PORT)
        await self.mail.wait_hello_from_server()
        await self.mail.login(self.email, self.password)
        await self.mail.select("INBOX")
        return self

    async def __aexit__(
        self,
        exc_type: BaseException | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if self.mail.get_state() not in ("LOGOUT", "NONAUTH"):
            try:
                await self.mail.logout()
            finally:
                self.mail.protocol.connection_lost(None)  # type: ignore

    async def get_unseen_emails(self) -> list[str]:
        res, data = await self.mail.search("UNSEEN")
        if res != "OK":
            raise Exception("Error fetching letters ids")
        return [uid.decode("utf-8") for uid in data[0].split()]

    async def fetch_email(self, uid: str) -> Message:
        status, data = await self.mail.fetch(uid, "(RFC822)")
        if status != "OK":
            raise Exception(f"Error fetching letter: {data[0].decode('utf-8')}")
        logging.debug(data)
        return email.message_from_bytes(data[1])

    async def wait_new_message_from(self, sender: str, timeout: float = 600) -> Message:
        deadline = datetime.now() + timedelta(seconds=timeout)
        logging.debug(
            f"{self.email} start listening process for incoming messasges from {sender}..."
        )
        # NOTE: originaly IDLE function was used, but it was blocking connection for other instances
        while datetime.now() < deadline:
            uids = await self.get_unseen_emails()
            logging.debug(uids)
            for uid in uids:
                msg = await self.fetch_email(uid)
                from_addr = parseaddr(msg.get("From"))[1]  # type: ignore
                if from_addr.lower() == sender.lower():
                    return msg
            await asyncio.sleep(2)
        raise TimeoutError("Timeout waiting for email")


async def create_email_accounts(usernames: list[str]) -> Set[str]:
    async with aiohttp.client.ClientSession(
        f"http://{SETTINGS.DOMAIN}:{SETTINGS.EMAIL_API_PORT}"
    ) as client:
        response = await client.post(
            url="/create",
            json={"usernames": usernames},
            headers={"Authorization": f"Bearer {SETTINGS.EMAIL_API_KEY}"},
        )
        if response.status != 200:
            raise Exception(
                f"Error with API: {response.status} -- {await response.text()}"
            )
        body = await response.json()
        logging.debug(body)
        return {item["username"] for item in body}


async def create_and_print_code(username: str):
    username = (await create_email_accounts([username])).pop()
    email = f"{username}@{SETTINGS.DOMAIN}"
    logging.info(f"Account {email} has been created successfully")
    async with MailConnection(
        SETTINGS.DOMAIN, email, SETTINGS.DEFAULT_PASSWORD
    ) as connection:
        logging.info("Waiting for code letter...")
        message = await connection.wait_new_message_from(
            "noreply@email.kick.com", timeout=60000000
        )
        subject = message.get("subject")
        logging.debug(subject)
        if not subject:
            raise Exception("Subject is empty")
        code = subject[:6]
        logging.info(f"{username}'s login code is: {code}\n Congrats!!!")


if __name__ == "__main__":
    username = "RealDeal2000"
    import core.log

    asyncio.run(create_and_print_code(username))
