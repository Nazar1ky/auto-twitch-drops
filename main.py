import asyncio
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
    logging.getLogger("autoTwitchDrops.twitch").setLevel(logging.ERROR)

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
Unittests
File Logging Rotate
README


Sorting:
* We need sort in groups by game name. Then by endAt. (We need actually mine campaign that end soon)
* Then every campaigns in group have flag ["allow"]["isEnabled"]. We need sort (False, True, True) -> (True, True, False)
* Every campaign have **DROPS** we need sort timeBasedDrops by requiredMinutesWatched

timeBasedDrops - Is drops
Every drop can have many items in benefitEdges
Like I can watch drop 60 minutes and I will get two items.

Drop have id
And item have id (benefit)
INVENTORY use ITEM id
So IDK how to check if we claimed drop...
"""
