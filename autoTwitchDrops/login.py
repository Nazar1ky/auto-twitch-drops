import asyncio
import json
import logging
import os
import time
import aiohttp

from .constants import CLIENT_ID


class TwitchLogin:
    logger = logging.getLogger(__name__)

    def __init__(self, cookie_filename="cookies.json"):
        self.nickname = None
        self.user_id = None
        self.access_token = None
        self.cookie_filename = cookie_filename

    async def login(self):
        """
        This is function which called to login. Saved cookies will be in cookies.json.
        https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow
        """
        async with aiohttp.ClientSession() as session:
            try:
                self._load_cookies()
            except (FileNotFoundError, KeyError, json.decoder.JSONDecodeError):
                device_code = await self._get_device_code(session)
                start_time = time.time()

                self.logger.info(
                    f"Please login in: {device_code['verification_uri']} | Expires in {device_code['expires_in'] / 60} minutes!",
                )

                while True:
                    if time.time() - start_time > device_code["expires_in"]:
                        self.logger.info("Time for login expired. Restart program.")
                        raise RuntimeError("Time runned out.")

                    try:
                        self.token = await self._get_token(session, device_code["device_code"])
                        break
                    except aiohttp.client_exceptions.ClientResponseError:
                        await asyncio.sleep(device_code["interval"])

            try:
                self.nickname, self.user_id = await self._validate(session)
            except aiohttp.client_exceptions.ClientResponseError as ex:
                self._remove_cookies()
                raise RuntimeError from ex

            self._save_cookies()

    async def _get_device_code(self, session):
        """This function used to get URL for auth to user to account. And device code which used in get_token() to get access_token."""
        payload = {
            "client_id": CLIENT_ID,
            "scopes": "channel_read chat:read user_blocks_edit user_blocks_read user_follows_edit user_read",
        }

        async with session.post("https://id.twitch.tv/oauth2/device", data=payload, raise_for_status=True) as response:
            return await response.json()

    async def _get_token(self, session, device_code):
        """This function used to get access_token with device_code. If user authorized account then return True else False"""
        payload = {
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        async with session.post("https://id.twitch.tv/oauth2/token", data=payload, raise_for_status=True) as response:
            data = await response.json()

        return data["access_token"]

    async def _validate(self, session):
        """In this function we validating account if access_token not expired and valid. Plus we get user_id which used in some requests and nickname (login)."""
        headers = {
                "Authorization": f"OAuth {self.access_token}",
        }

        async with session.get("https://id.twitch.tv/oauth2/validate", headers=headers, raise_for_status=True) as response:
            data = await response.json()


        return data["login"].lower(), data["user_id"]

    def _save_cookies(self):
        cookies = {
            "access_token": self.access_token,
            "nickname": self.nickname,
            "user_id": self.user_id,
        }

        with open(self.cookie_filename, "w", encoding="utf-8") as file:
            json.dump(cookies, file, ensure_ascii=False, indent=4)

    def _load_cookies(self):
        with open(self.cookie_filename, encoding="utf-8") as file:
            cookies = json.load(file)

        self.access_token = cookies["access_token"]
        self.nickname = cookies["nickname"]
        self.user_id = cookies["user_id"]

    def _remove_cookies(self):
        if os.path.exists(self.cookie_filename):
            os.remove(self.cookie_filename)
