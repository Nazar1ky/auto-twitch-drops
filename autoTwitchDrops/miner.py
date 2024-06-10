import logging

from . import Campaign, Channel
from .utils import sort_campaigns

logger = logging.getLogger()

class TwitchMiner:
    logger = logging.getLogger(__name__)

    def __init__(self, login, api):
        self.login = login
        self.api = api

    async def run(self):
        self.logger.info("Running miner")
        streamer = await self.pick_streamer()


    async def pick_streamer(self):
        await self.update_inventory()
        await self.update_campaigns()
        await self.claim_all_drops()
        self.campaigns = sort_campaigns(self.campaigns)
        streamer = await self.get_channel_to_mine()

    async def get_channel_to_mine(self):
        for campaign in self.campaigns:
            if campaign.channelsEnabled:
                streamers = await self.get_online_channels(campaign.channels, campaign.game["id"])

                if streamers:
                    break

            else:
                streamers = [channel["node"]["broadcaster"]["login"] for channel in (await self.api.get_category_streamers(campaign.game["slug"]))]
                if streamers:
                    break

        return streamers

        # return by campaign first available channel

    async def get_online_channels(self, channels, game_id):
        response =  [Channel(channel) for channel in await self.api.get_channels_information(channels)]

        return [channel.nickname for channel in response if channel.isStream and channel.game["id"] == game_id]

    async def update_inventory(self):
        self.inventory = [Campaign(x) for x in (await self.api.get_inventory())["dropCampaignsInProgress"]]
        self.claimed_drops_ids = []

        for campaign in self.inventory:
            for drop in campaign.drops:
                if drop.claimed or drop.required_time <= drop.watched_time:
                    self.claimed_drops_ids.append(drop.id_)

        logger.info("Inventory updated")

    async def update_campaigns(self):
        # campaigns = list(filter(lambda x: x["status"] == "ACTIVE", await self.api.get_campaigns()))
        response = await self.api.get_campaigns()

        campaigns_ids = [campaign["id"] for campaign in response if campaign["status"] == "ACTIVE"]

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
