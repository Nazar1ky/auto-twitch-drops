import asyncio
import json
import logging
import os
import time

import aiohttp

from .constants import CLIENT_ID


class TwitchLogin:
    logger = logging.getLogger(__name__)

    def __init__(self, session, cookie_filename="cookies.json"):
        self._sess = session
        self.nickname = None
        self.user_id = None
        self.access_token = None
        self.cookie_filename = cookie_filename

    async def login(self):
        """
        Login to Twitch.
        Loads cookies file if exists.
        https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow
        """
        try:
            self._load_cookies()
        except (FileNotFoundError, KeyError, json.decoder.JSONDecodeError):
            device_code = await self._authorize_device()
            start_time = time.time()

            self.logger.info(
                f"Please login in: {device_code['verification_uri']} | Expires in {device_code['expires_in'] / 60} minutes!",
            )

            while True:
                if time.time() - start_time > device_code["expires_in"]:
                    self.logger.info("Time for login expired. Restart program.")
                    raise RuntimeError("Time ran out") from None

                try:
                    self.access_token = await self._request_token(device_code["device_code"])
                    break
                except (aiohttp.client_exceptions.ClientResponseError, json.decoder.JSONDecodeError, KeyError):
                    await asyncio.sleep(device_code["interval"])

        try:
            self.nickname, self.user_id = await self._validate()
        except aiohttp.client_exceptions.ClientConnectorError:
            self.logger.critical("No internet connection")
            raise
        except Exception:
            self._remove_cookies()
            raise

        self._save_cookies()

    async def _authorize_device(self):
        """
        Start device authorization flow.
        Scopes needed: https://dev.twitch.tv/docs/authentication/scopes/
        """
        payload = {
            "client_id": CLIENT_ID,
            "scopes": "channel_read chat:read user_blocks_edit user_blocks_read user_follows_edit user_read",
        }

        async with self._sess.post("https://id.twitch.tv/oauth2/device", data=payload, raise_for_status=True) as response:
            return await response.json()

    async def _request_token(self, device_code):
        """
        Request tokens from device code
        """
        payload = {
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        async with self._sess.post("https://id.twitch.tv/oauth2/token", data=payload, raise_for_status=True) as response:
            data = await response.json()

        return data["access_token"]

    async def _validate(self):
        """
        Validate token is not expired.
        We also get user_id/username information.
        https://dev.twitch.tv/docs/authentication/validate-tokens/
        """
        headers = {
                "Authorization": f"OAuth {self.access_token}",
        }

        async with self._sess.get("https://id.twitch.tv/oauth2/validate", headers=headers, raise_for_status=True) as response:
            data = await response.json()


        return data["login"].lower(), data["user_id"]

    def _save_cookies(self):
        cookies = {
            "access_token": self.access_token,
            "nickname": self.nickname,
            "user_id": self.user_id,
        }
        self.logger.debug("Saving cookies: %s", self.cookie_filename)

        with open(self.cookie_filename, "w", encoding="utf-8") as file:
            json.dump(cookies, file, ensure_ascii=False, indent=4)

    def _load_cookies(self):
        self.logger.debug("Loading cookies: %s", self.cookie_filename)

        with open(self.cookie_filename, encoding="utf-8") as file:
            cookies = json.load(file)

        self.access_token = cookies["access_token"]
        self.nickname = cookies["nickname"]
        self.user_id = cookies["user_id"]

    def _remove_cookies(self):
        if os.path.exists(self.cookie_filename):
            self.logger.debug("Removing cookies: %s", self.cookie_filename)
            os.remove(self.cookie_filename)
