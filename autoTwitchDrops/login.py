import asyncio
import json
import logging
import os

import aiohttp

from .constants import CLIENT_ID


class TwitchLogin:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.nickname = None
        self.user_id = None
        self.access_token = None

    async def login(self):
        """
        This is function which called to login. Saved cookies will be in cookies.json.
        https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow
        """
        self.session = aiohttp.ClientSession()
        save_cookies = False

        if not self.load_cookies():
            device_code = await self.get_device_code()

            self.logger.info(
                f"Please login in: {device_code['verification_uri']} | Expires in {device_code['expires_in'] / 60} minutes!",
            )

            while True:
                if not self.get_token(device_code["device_code"]): # I can do here loop but https://docs.astral.sh/ruff/rules/try-except-in-loop/
                    asyncio.sleep(device_code["interval"])
                break

            save_cookies = True

        if not await self.validate():
            self.remove_cookies()
            return False

        if save_cookies:
            self.save_cookies()

        await self.session.close()
        return True

    async def get_device_code(self):
        """This function used to get URL for auth to user to account. And device code which used in get_token() to get access_token."""
        payload = {
            "client_id": CLIENT_ID,
            "scopes": "channel_read chat:read user_blocks_edit user_blocks_read user_follows_edit user_read",
        }

        async with self.session.post("https://id.twitch.tv/oauth2/device", data=payload) as response:
            return await response.json()

    async def get_token(self, device_code):
        """This function used to get access_token with device_code. If user authorized account then return True else False"""
        payload = {
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }
        async with self.session.post("https://id.twitch.tv/oauth2/token", payload) as response:

            if response.status != 200:
                return False

            data = await response.json()

        self.access_token = data["access_token"]
        return True

    async def validate(self):
        """In this function we validating account if access_token not expired and valid. Plus we get user_id which used in some requests and nickname (login)."""
        headers = {
                "Authorization": f"OAuth {self.access_token}",
        }

        async with self.session.get("https://id.twitch.tv/oauth2/validate", headers=headers) as response:

            if response.status != 200:
                return False

            data = await response.json()

        self.nickname = data["login"].lower()
        self.user_id = data["user_id"]

        return True

    def save_cookies(self):
        cookies = {
            "access_token": self.access_token,
            "nickname": self.nickname,
            "user_id": self.user_id,
        }

        with open("cookies.json", "w", encoding="utf-8") as file:
            json.dump(cookies, file, ensure_ascii=False, indent=4)

    def load_cookies(self):
        try:
            with open("cookies.json", encoding="utf-8") as file:
                cookies = json.load(file)

            self.access_token = cookies["access_token"]
            self.nickname = cookies["nickname"]
            self.user_id = cookies["user_id"]

        except FileNotFoundError:
            return False
        else:
            return True

    def remove_cookies(self):
        if os.path.exists("cookies.json"):
            os.remove("cookies.json")
