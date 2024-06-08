import asyncio
import json
import logging

import aiohttp

from autoTwitchDrops import TwitchApi, TwitchLogin, TwitchMiner, constants


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("{asctime} | {levelname:<5s} | {funcName:<24s} | {message}", style="{", datefmt="%H:%M:%S")

    # console logger
    ch = logging.StreamHandler()
    logger.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # file logger
    fh = logging.FileHandler("AutoTwitchDrops.log", encoding="utf-8")
    logger.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # suppress verbose logs from external libraries
    logging.getLogger("chardet.charsetprober").setLevel(logging.ERROR)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("websocket").setLevel(logging.ERROR)

async def main():
    setup_logger()

    headers = {
        "client-id": constants.CLIENT_ID,
        "user-agent": constants.USER_AGENT,
    }

    async with aiohttp.ClientSession(raise_for_status=True, timeout=aiohttp.ClientTimeout(total=60), headers=headers) as session:
        # AUTH
        twitch_login = TwitchLogin(session, cookie_filename="cookies.json")
        await twitch_login.login()
        logging.info(f"Successfully logged in as {twitch_login.nickname}")

        # API
        api = TwitchApi(session, twitch_login)

        # MINER
        miner = TwitchMiner(twitch_login, api)
        await miner.run()

if __name__ == "__main__":
    asyncio.run(main())

""" TODO:
Refactor
Unittests(?)
AIOHTTP


Smart Load:
* Load all streamers that stream that game
* Find last drop or more mined drop and mine it

more functions find_channel_to_watch

refactor everything

module logging queue required

file logging


Found campaign and drop, if all okay - start scraping category, if in category founded streamers that in campaign list - mine, no - skip.

need to sort drop by channels/watch time/campaign game name bruh u

entities for campaigns and drops
"""
