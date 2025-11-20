import asyncio
import email
import logging
import ssl
from datetime import datetime, timedelta
from email import policy
from email.message import EmailMessage
from types import TracebackType
from typing import Set
from email.utils import parseaddr

import aiohttp
from aioimaplib import (
    IMAP4,
    IMAP4_PORT,
    IMAP4_SSL,
    IMAP4_SSL_PORT,
    STOP_WAIT_SERVER_PUSH,
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
                await asyncio.wait_for(self.mail.logout(), timeout=10)
            except (TimeoutError, OSError, asyncio.CancelledError) as e:
                logging.warning(f"Failed to logout cleanly: {e}")
            finally:
                self.mail.protocol.connection_lost(None)  # type: ignore

    async def get_unseen_emails(self):
        res, data = await self.mail.search("UNSEEN")
        if res != "OK":
            return []
        return data[0].split()

    async def fetch_email(self, uid: str) -> EmailMessage | None:
        status, data = await self.mail.fetch(uid, "(RFC822)")
        if status != "OK":
            return None
        return email.message_from_bytes(data[1], policy=policy.default)

    async def wait_new_message_from(
        self, sender: str, timeout: float = 600
    ) -> EmailMessage:
        # check unseen
        existing_unseen = await self.get_unseen_emails()
        for uid in existing_unseen:
            msg = await self.fetch_email(uid)
            if msg:
                from_addr = parseaddr(msg.get("From"))[1]  # type: ignore
                if from_addr.lower() == sender.lower():
                    return msg

        deadline = datetime.now() + timedelta(seconds=timeout)
        while datetime.now() < deadline:
            idle_session_length = min(300, timeout)
            idle_future = await self.mail.idle_start(timeout=idle_session_length)
            try:
                while True:
                    remaining = (deadline - datetime.now()).total_seconds()

                    if remaining <= 0:
                        raise TimeoutError(
                            f"No message from {sender} in {timeout} seconds"
                        )

                    server_msg = await self.mail.wait_server_push(timeout=60)
                    if server_msg == STOP_WAIT_SERVER_PUSH:
                        break

                    if server_msg and b"EXISTS" in server_msg:
                        unseen = await self.get_unseen_emails()

                        for uid in unseen:
                            msg = await self.fetch_email(uid)
                            if msg:
                                from_addr = parseaddr(msg.get("From"))[1]  # type: ignore
                                if from_addr.lower() == sender.lower():
                                    self.mail.idle_done()
                                    await asyncio.wait_for(idle_future, timeout=2)
                                    return msg

            finally:
                if self.mail.has_pending_idle():
                    self.mail.idle_done()
                    try:
                        await asyncio.wait_for(idle_future, timeout=2)
                    except Exception:
                        pass
        raise TimeoutError(f"No message from {sender} in {timeout} seconds")


async def create_email_accounts(usernames: list[str]) -> Set[str]:
    async with aiohttp.client.ClientSession(
        f"http://{SETTINGS.DOMAIN}:{SETTINGS.EMAIL_API_PORT}"
    ) as client:
        response = await client.post(url="/create", json={"usernames": usernames})
        if response.status != 200:
            raise Exception(
                f"Error with API: {response.status} -- {await response.json()}"
            )
        body = await response.json()
        return {item["username"] for item in body if item["status"] == "created"}


async def create_and_print_code(username: str):
    username = (await create_email_accounts([username])).pop()
    email = f"{username}@{SETTINGS.DOMAIN}"
    logging.info(f"Account {email} has been created successfully")
    async with MailConnection(
        SETTINGS.DOMAIN, email, SETTINGS.DEFAULT_PASSWORD
    ) as connection:
        logging.info("Waiting for code letter...")
        message = await connection.wait_new_message_from(
            "noreply@email.kick.com", timeout=60000
        )
        subject = message.get("subject")
        if not subject:
            raise Exception("Subject is empty")
        code = subject[:6]
        logging.info(f"{username}'s login code is: {code}\n Congrats!!!")


if __name__ == "__main__":
    username = "lyingDove8"
    import core.log

    asyncio.run(create_and_print_code(username))
