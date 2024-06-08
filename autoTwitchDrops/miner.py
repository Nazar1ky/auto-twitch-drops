import logging

from .utils import sort_campaigns
from .WebSocket import TwitchWebSocket

logger = logging.getLogger()

class TwitchMiner:
    logger = logging.getLogger(__name__)

    def __init__(self, login, api):
        self.login = login
        self.api = api

    async def run(self):
        self.logger.info("Running miner")
        streamer = await self.pick_streamer()
        # WiP

    async def pick_streamer(self):
        await self.update_inventory()
        await self.update_campaigns() # HACK we need to make campaigns without user etc...
        await self.claim_all_drops()
        # self.campaigns = sort_campaigns(self.campaigns)
        # streamer = await self.get_channel_to_mine()
        # return streamer

    # async def get_channel_to_mine(self):
    #     for campaign in self.campaigns:
    #         if campaign["allow"]["isEnabled"]:
    #             channels = [x["name"] for x in campaign["channels"]]
    #             channels_to_watch = self.get_channels_to_mine(channels, campaign["game"]["id"])
    #             if channels_to_watch:
    #                 streamer = channels_to_watch[0]
    #                 break

    #         else:
    #             streamer = self.api.get_category_streamers(campaign["game"]["slug"])[0]
    #             break

    #     return streamer

        # return by campaign first available channel

    async def update_inventory(self):
        self.inventory = await self.api.get_inventory()
        self.claimed_drops_ids = []

        for campaign in self.inventory["dropCampaignsInProgress"]:
            for drop in campaign["timeBasedDrops"]:
                if drop["self"]["isClaimed"] or drop["requiredMinutesWatched"] <= drop["self"]["currentMinutesWatched"]:
                    self.claimed_drops_ids.append(drop["id"])

        logger.info("Inventory updated")

    async def update_campaigns(self):
        campaigns = list(filter(lambda x: x["status"] == "ACTIVE", await self.api.get_campaigns()))

        campaigns_ids = [campaign["id"] for campaign in campaigns]

        self.campaigns = await self.api.get_full_campaigns_data(campaigns_ids)

        for i, campaign in enumerate(self.campaigns):
            for j, drop in enumerate(campaign["user"]["dropCampaign"]["timeBasedDrops"]):
                if drop["id"] in self.claimed_drops_ids:
                    logger.debug(f"Removed drop {drop["id"]} Name: {drop["name"]}")
                    del self.campaigns[i]["user"]["dropCampaign"]["timeBasedDrops"][j]

            if len(campaign["user"]["dropCampaign"]["timeBasedDrops"]) == 0:
                logger.debug(f"Removed campaign {campaign["user"]["dropCampaign"]["id"]} Name: {campaign["user"]["dropCampaign"]["name"]}")
                del self.campaigns["user"]["dropCampaign"][i]

        logger.info(f"Campaigns updated - {len(self.campaigns)}")

    async def claim_all_drops(self):
        for campaign in self.inventory["dropCampaignsInProgress"]:
            for item in campaign["timeBasedDrops"]:
                if item["requiredMinutesWatched"] <= item["self"]["currentMinutesWatched"] and item["self"]["isClaimed"] is False:
                    await self.api.claim_drop(item["self"]["dropInstanceID"])
                    logger.info(f"Claimed drop {item["name"]}")

    # async def get_channels_to_mine(self, channels, game_id):
    #     response = self.api.get_channels_information(channels)

    #     result = list(filter(lambda x: x["user"] and x["user"]["stream"] and x["user"]["broadcastSettings"]["game"] and x["user"]["broadcastSettings"]["game"]["id"] == game_id, response))
    #     return [i["user"]["login"] for i in result]
