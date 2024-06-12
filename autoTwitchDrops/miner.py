import asyncio
import json
import logging

from aiohttp.client_exceptions import ServerDisconnectedError
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from . import Channel
from .twitchsocket import TwitchWebSocket
from .utils import filter_campaigns, get_drops_to_claim, sort_campaigns

logger = logging.getLogger()


class TwitchMiner:
    logger = logging.getLogger(__name__)

    def __init__(self, login, api, game=None):
        self.login = login
        self.api = api

        self.wanted_game = game

        self.inventory = None
        self.campaigns = None

        self.drop_mined = False

        self.channel_id = None
        self.game_to_mine = None
        self.actual_game = None

        self.topics = [f"user-drop-events.{self.login.user_id}", f"onsite-notifications.{self.login.user_id}"]

    async def handle_websocket(self):
        while True:
            try:
                data = await self.websocket.receive_message()

            except (ConnectionClosedError, ConnectionClosedOK):
                logger.exception("Websocket error, reconnect.")
                self.websocket.connect()

            if not data or not data.get("message"):
                continue

            message = json.loads(data["message"])

            if data["topic"] == f"onsite-notifications.{self.login.user_id}":  # noqa: SIM102
                if message["type"] == "create-notification":
                    data = message["data"]["notification"]
                    if data["type"] == "user_drop_reward_reminder_notification":
                        self.drop_mined = True

                    return

            if data["topic"] == f"broadcast-settings-update.{self.channel_id}":  # noqa: SIM102
                if message["type"] == "broadcast_settings_update":
                    self.current_game = message["game_id"]

    async def run(self):
        self.logger.info("Please don't use Twitch while mining to avoid errors")
        self.logger.info("To track your drops progress: https://www.twitch.tv/drops/inventory")

        try:
            self.websocket = TwitchWebSocket(self.login, self.topics)

            await self.websocket.connect()

            asyncio.create_task(self.handle_websocket())

            asyncio.create_task(self.websocket.run_ping())

            while True:
                streamer = await self.pick_streamer()

                await self.websocket.listen_channel_updates(streamer.id)

                self.channel_id = streamer.id
                self.game_to_mine = streamer.game["id"]

                try:
                    await self.watch(streamer)

                except RuntimeError: # Except if stream goes offline
                    self.logger.exception("Streamer seems changed game/go offline, switch.")
                    continue
                except ServerDisconnectedError:
                    self.logger.exception("Critical error while watching. Restarting.")
                    continue
                finally:
                    self.channel_id = None
                    self.game_to_mine = None
                    self.actual_game = None
                    self.drop_mined = False

                    await self.websocket.unlisten_channel_updates()

        finally:
            await self.websocket.close()

    async def watch(self, streamer):
        if not self.game_to_mine:
            raise RuntimeError("No game choosed")

        while not self.drop_mined:

            if self.actual_game and self.game_to_mine != self.actual_game:
                raise RuntimeError("Streamer changed game")

            await self.api.send_watch(streamer.nickname)
            self.logger.info(f"Watch sent to {streamer.nickname}")
            await asyncio.sleep(15)

    async def pick_streamer(self):
        # UPDATES
        await self.update_inventory()
        await self.update_campaigns()
        self.campaigns = filter_campaigns(self.inventory, self.campaigns)
        self.campaigns = sort_campaigns(self.campaigns)

        # CLAIM DROPS
        await self.claim_all_drops()

        # FIND STREAMER TO MINE
        while True:
            streamers = (await self.get_channel_to_mine())

            if streamers:
                break

            self.logger.info("No streamers to mine... We will continue in 60 seconds")
            await asyncio.sleep(60)

        self.logger.debug(f"Streamers to mine: {[streamer.nickname for streamer in streamers]}")

        return streamers[0]

    async def get_channel_to_mine(self):
        streamers = None

        for campaign in self.campaigns:
            if self.wanted_game and self.wanted_game != campaign.game["displayName"]:
                continue

            if campaign.channelsEnabled:
                streamers = await self.get_online_channels(campaign.channels, campaign.game["id"])

                if streamers:
                    break

                self.logger.debug(f"{campaign.name} {campaign.channels} Offline")

            else:
                response = await self.api.get_category_streamers(campaign.game["slug"])

                streamers = [Channel(channel["node"]) for channel in response if channel["node"].get("broadcaster")] # we need to check because sometimes twitch give forbidden data
                if streamers:
                    break

                self.logger.debug(f"{campaign.name} No streamers in category")

        return streamers

    async def get_online_channels(self, channels, game_id):
        response = await self.api.get_channels_information(channels)
        response = [Channel(channel["user"]) for channel in response if channel["user"]["stream"] and channel["user"]["broadcastSettings"]["game"]]
        return list(filter(lambda x: x.game["id"] == game_id, response))

    async def update_inventory(self):
        self.inventory = await self.api.get_inventory()
        logger.info("Inventory fetched")

    async def update_campaigns(self):
        response = await self.api.get_campaigns()
        campaigns_ids = [campaign["id"] for campaign in response if campaign["status"] == "ACTIVE"]
        response = await self.api.get_full_campaigns_data(campaigns_ids)
        self.campaigns = [x["user"]["dropCampaign"] for x in response]

        logger.info(f"Campaigns updated - {len(self.campaigns)}")

    async def claim_all_drops(self):
        if not self.inventory:
            return

        for drop in get_drops_to_claim(self.inventory):
            await self.api.claim_drop(drop)
            logger.info(f"Claimed drop {drop}")
