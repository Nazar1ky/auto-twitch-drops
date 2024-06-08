import logging

from . import Campaign

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
        self.inventory = [Campaign(x) for x in (await self.api.get_inventory())["dropCampaignsInProgress"]]
        self.claimed_drops_ids = []

        for campaign in self.inventory:
            for drop in campaign.drops:
                if drop.claimed or drop.required_time <= drop.watched_time:
                    self.claimed_drops_ids.append(drop.id_)

        logger.info("Inventory updated")

    async def update_campaigns(self):
        campaigns = list(filter(lambda x: x["status"] == "ACTIVE", await self.api.get_campaigns()))
        campaigns_ids = [campaign["id"] for campaign in campaigns]

        self.campaigns = [Campaign(x["user"]["dropCampaign"]) for x in await self.api.get_full_campaigns_data(campaigns_ids)]

        for i, campaign in enumerate(self.campaigns):
            for j, drop in enumerate(campaign.drops):
                if drop.id_ in self.claimed_drops_ids:
                    logger.debug(f"Removed drop {drop.id_} Name: {drop.name}")
                    del self.campaigns[i].drops[j]

            if len(campaign.drops) == 0:
                logger.debug(f"Removed campaign {campaign.id_} Name: {campaign.name}")
                del self.campaigns[i]

        logger.info(f"Campaigns updated - {len(self.campaigns)}")

    async def claim_all_drops(self):
        for campaign in self.inventory:
            for drop in campaign.drops:
                if drop.required_time <= drop.watched_time and drop.claimed is False:
                    await self.api.claim_drop(drop.instanceId)
                    logger.info(f"Claimed drop {drop.name}")

    # async def get_channels_to_mine(self, channels, game_id):
    #     response = self.api.get_channels_information(channels)

    #     result = list(filter(lambda x: x["user"] and x["user"]["stream"] and x["user"]["broadcastSettings"]["game"] and x["user"]["broadcastSettings"]["game"]["id"] == game_id, response))
    #     return [i["user"]["login"] for i in result]
