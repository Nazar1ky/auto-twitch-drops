import asyncio
import logging
import os

import aiohttp

from autoTwitchDrops import TwitchLogin, constants

folder = "cookies"
headers = {
    "client-id": constants.CLIENT_ID,
    "user-agent": constants.USER_AGENT,
}

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("{asctime} | {levelname:<5s} | {funcName:<24s} | {message}", style="{", datefmt="%H:%M:%S")

ch = logging.StreamHandler()
logger.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

async def main():
    if not os.path.exists(folder):
        os.mkdir(folder)

    cookie_files = len(os.listdir(folder)) + 1

    if cookie_files > 14:
        print("You can't add more accounts")
        return

    while cookie_files < 16:
        async with aiohttp.ClientSession(raise_for_status=True, timeout=aiohttp.ClientTimeout(total=60), headers=headers) as session:
            twitch_login = TwitchLogin(session, cookie_filename=f"{folder}/{cookie_files}.json")
            await twitch_login.login()
            print(f"Successfully logged in as {twitch_login.nickname}")
            cookie_files += 1


if __name__ == "__main__":
    asyncio.run(main())
