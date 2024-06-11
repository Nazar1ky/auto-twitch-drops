import asyncio
import ctypes
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
    logging.getLogger("websockets").setLevel(logging.ERROR)
    logging.getLogger("autoTwitchDrops.twitch").setLevel(logging.ERROR)

async def main():
    setup_logger()

    headers = {
        "client-id": constants.CLIENT_ID,
        "user-agent": constants.USER_AGENT,
    }
    SSL_ENABLED = True

    async with aiohttp.ClientSession(raise_for_status=True, timeout=aiohttp.ClientTimeout(total=60), headers=headers, connector=aiohttp.TCPConnector(ssl=SSL_ENABLED)) as session:
        # AUTH
        twitch_login = TwitchLogin(session, cookie_filename="cookies.json")
        await twitch_login.login()
        logging.info(f"Successfully logged in as {twitch_login.nickname}")

        ctypes.windll.kernel32.SetConsoleTitleW(twitch_login.nickname)

        # API
        api = TwitchApi(session, twitch_login)

        # MINER
        miner = TwitchMiner(twitch_login, api, game=None) # Put there game in str game="Rust"
        await miner.run()

if __name__ == "__main__":
    asyncio.run(main())

""" TODO:
Unittests
File Logging Rotate
README
Better check if that drop which we need mined
Restart websocket if it closed
Test websocket multiaccounts (partically done)
Maybe send from api entities?
Fix issue with removing drops and campaigns
fix issue with checking if streamer enabled drops

Sorting:
* We need sort in groups by game name. Then by endAt. (We need actually mine campaign that end soon)
* Then every campaigns in group have flag ["allow"]["isEnabled"]. We need sort (False, True, True) -> (True, True, False)
* Every campaign have **DROPS** we need sort timeBasedDrops by requiredMinutesWatched
"""
