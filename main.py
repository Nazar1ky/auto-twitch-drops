import asyncio
import logging
import os

import aiohttp

from autoTwitchDrops import (
    TwitchApi,
    TwitchLogin,
    TwitchMiner,
    TwitchWebSocket,
    constants,
)


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

    cookie_files = [f"cookies/{f}" for f in os.listdir("cookies/") if f.endswith(".json")]

    bots = []
    sessions = []

    # SETUP WEBSOCKET
    websocket = TwitchWebSocket()
    await websocket.connect()
    ping_task = asyncio.create_task(websocket.run_ping())
    handle_messages_task = asyncio.create_task(websocket.handle_websocket_messages())

    for cookie_file in cookie_files:
        # CREATE SESSION
        session = aiohttp.ClientSession(raise_for_status=True, timeout=aiohttp.ClientTimeout(total=60), headers=headers)
        sessions.append(session)

        # AUTH
        twitch_login = TwitchLogin(session, cookie_filename=cookie_file)
        await twitch_login.login()
        logging.info(f"Successfully logged in as {twitch_login.nickname}")

        # WEBSOCKET AUTH
        await websocket.add_topics(twitch_login, [f"user-drop-events.{twitch_login.user_id}",
                                                  f"onsite-notifications.{twitch_login.user_id}"])

        # API
        api = TwitchApi(session, twitch_login)

        # MINER
        miner = TwitchMiner(twitch_login, api, websocket, game=None) # Put there game in str game="Rust"
        bots.append(asyncio.create_task(miner.run()))

    try:
        await asyncio.gather(*bots)
    except asyncio.exceptions.CancelledError:
        pass

    finally:
        for session in sessions: await session.close()
        await websocket.close()

if __name__ == "__main__":
    asyncio.run(main())

""" TODO:
Unittests
File Logging Rotate
README
Better check if that drop which we need mined
Restart websocket if it closed
Test websocket multiaccounts (partically done)
aiohttp.client_exceptions.ServerDisconnectedError
Maybe send from api entities?
fix issue with checking if streamer enabled drops

Sorting:
* We need sort in groups by game name. Then by endAt. (We need actually mine campaign that end soon)
* Then every campaigns in group have flag ["allow"]["isEnabled"]. We need sort (False, True, True) -> (True, True, False)
* Every campaign have **DROPS** we need sort timeBasedDrops by requiredMinutesWatched
"""
