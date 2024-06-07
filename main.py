import asyncio
import logging

import aiohttp

from autoTwitchDrops import TwitchApi, TwitchLogin, constants


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("{asctime} | {levelname} | {funcName:<24s} | {message}", style="{", datefmt="%H:%M:%S")

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
    async with aiohttp.ClientSession(raise_for_status=True, timeout=aiohttp.ClientTimeout(total=60), headers={"client-id": constants.CLIENT_ID,"user-agent": constants.USER_AGENT}) as session:
        # AUTH
        twitch_login = TwitchLogin(session, cookie_filename="cookies.json")
        await twitch_login.login()
        logging.info(f"Successfully logged in as {twitch_login.nickname}")

        # API
        api = TwitchApi(session, twitch_login)

        # miner(api)
        # print(await api.get_channel_information("lenovolegion"))
        # print(await api.playback_access_token("thegiftingchannel"))
        # print(await api.get_full_campaign_data("1d17dc2f-2115-11ef-b66c-0a58a9feac02"))
        # print(await api.get_inventory())
        campaigns = await api.get_campaigns()
        ids = []
        for campaign in campaigns:
            ids.append(campaign["id"])
        print(ids)
        await api.get_full_campaigns_data(ids)
        # print(await api.get_category_streamers("party-quiz"))
        # print(await api.test())


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
