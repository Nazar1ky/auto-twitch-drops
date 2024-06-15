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

    if not os.path.exists("cookies"):
        os.mkdir("cookies")

    cookie_files = [f"cookies/{f}" for f in os.listdir("cookies/") if f.endswith(".json")]

    if len(cookie_files) == 0:
        return

    bots = []
    sessions = []

    # SETUP WEBSOCKET
    websocket = TwitchWebSocket()
    await websocket.connect()

    # TASKS FOR WEBSOCKET
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

21:05:05 | ERROR | send_requests            | Error in requests [{'operationName': 'VideoPlayerStreamInfoOverlayChannel', 'variables': {'channel': 'rivers_gg'}, 'extensions': {'persistedQuery': {'version': 1, 'sha256Hash': 'a5f2e34d626a9f4f5c0204f910bab2194948a9502089be558bb6e779a9e1b3d2'}}}]
Response: [{'errors': [{'message': 'service timeout', 'path': ['user', 'stream']}], 'data': {'user': {'id': '734906922', 'profileURL': 'https://www.twitch.tv/rivers_gg', 'displayName': 'rivers_gg', 'login': 'rivers_gg', 'profileImageURL': 'https://static-cdn.jtvnw.net/jtv_user_pictures/0e6f8782-d5b9-4a51-ae8a-9c952c213487-profile_image-150x150.png', 'broadcastSettings': {'id': '734906922', 'title': 'DROPS - BELLUM DIA 4', 'game': {'id': '509658', 'displayName': 'Just Chatting', 'name': 'Just Chatting', '__typename': 'Game'}, '__typename': 'BroadcastSettings'}, 'stream': None, '__typename': 'User'}}, 'extensions': {'durationMilliseconds': 188, 'operationName': 'VideoPlayerStreamInfoOverlayChannel', 'requestID': '01J0BYSB7QNJ7CHGXAC2ZSRS2T'}}]


NielsenContentMetadata
PlayerTrackingContextQuery
"""
