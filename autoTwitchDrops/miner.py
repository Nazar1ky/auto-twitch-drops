import json
import logging
import time
import urllib
from datetime import datetime, timezone

from .utils import get_drop_image_id
from .WebSocket import TwitchWebSocket

logger = logging.getLogger()

class TwitchMiner:
    logger = logging.getLogger(__name__)

    def __init__(self, login, api):
        self.login = login
        self.api = api
        # self.switch_to_another_campaign = False
        # self.can_be_claimed = []
        # self.campaigns = None

        # self.socket = TwitchWebSocket(self)
        # self.socket.run()

    async def run(self):
        self.logger.info("Running miner")

        # WiP





    def start(self):
        campaigns = self.get_campaigns_to_mine("Aether Gazer")
        for campaign in campaigns:
            if campaign.get("channels"): # HACK
                channels = [x["name"] for x in campaign["channels"]]
                channels_to_watch = self.get_channels_to_mine(channels, campaign["game"]["id"])
                logger.info(f"Founded channels to watch: {channels_to_watch}")
                for channel_to_watch in channels_to_watch:
                    logger.info(f"Mining drop {campaign["drop_name"]}")
                    logger.info(f"CHANNEL | Starting Watch {channel_to_watch} | Time {campaign["time_required"]}.")
                    self.watch(channel_to_watch, campaign["drop_id"])

                    if self.switch_to_another_campaign is True:
                        self.switch_to_another_campaign = False
                        break
            else:
                channel = self.get_category_streamers(campaign["game"]["slug"])[0]["node"]["broadcaster"]["login"]
                logger.info(f"Mining drop {campaign["drop_name"]}")
                logger.info(f"CATEGORY | Starting Watch {channel} | Time {campaign["time_required"]}.")
                self.watch(channel, campaign["drop_image_id"])


    def claim_all_drops(self):
        inventory = self.inventory

        for campaign in inventory["dropCampaignsInProgress"]:
            for item in campaign["timeBasedDrops"]:
                if item["requiredMinutesWatched"] <= item["self"]["currentMinutesWatched"] and item["self"]["isClaimed"] is False:
                    self.api.claim_drop(item["self"]["dropInstanceID"])
                    logger.info(f"Claimed drop {item["name"]}")


    def get_category_streamers(self, game_slug):
        streamers = []

        cursor = None

        while True:
            data = self.api.get_category_streamers(game_slug, cursor)
            streamers.extend(data["edges"])
            if not data["pageInfo"]["hasNextPage"]:
                break

            cursor = data["edges"][-1]["cursor"]
            logger.debug(f"Scraping {cursor} {data["edges"][0]["node"]["title"]}")

        return streamers


    def get_campaigns_to_mine(self, game_name = None):
        game_name = game_name.lower() if game_name else None

        result = []

        for campaign in self.campaigns:
            if game_name and campaign["game"]["displayName"].lower() != game_name.lower():
                continue

            for drop in campaign["timeBasedDrops"]:
                drop_id = drop["benefitEdges"][0]["benefit"]["id"]
                if drop_id in self.claimed_drops:
                    continue

                watched_minutes = self.watched_drops.get(drop_id)

                if watched_minutes and watched_minutes > drop["requiredMinutesWatched"]:
                    continue

                if not watched_minutes:
                    watched_minutes = 0

                logger.info(f"Founded eligable drop {drop["benefitEdges"][0]["benefit"]["name"]}")

                time_required = drop["requiredMinutesWatched"] - watched_minutes

                result.append({
                    "channels": campaign["allow"]["channels"],
                    "isChannelEnabled": campaign["allow"]["isEnabled"],
                    "time_required": drop["requiredMinutesWatched"],
                    "time_watched": watched_minutes,
                    "time_required_minused": time_required,
                    "game": campaign["game"],
                    "drop_id": drop_id,
                    "drop_name": drop["benefitEdges"][0]["benefit"]["name"],
                    "drop_image_id": get_drop_image_id(drop["benefitEdges"][0]["benefit"]["imageAssetURL"]),
                    "end_at": campaign["endAt"],
                })

        result.sort(key = lambda x: (datetime.fromisoformat(x["end_at"]), x["game"]["displayName"], x["isChannelEnabled"], x["time_required"]))

        # with open("camp.json", "w", encoding="utf-8") as fo:
        #     json.dump(result, fo, indent=4, ensure_ascii=False)

        return result

    async def update_inventory(self):
        self.inventory = self.api.get_inventory()
        self.claimed_drops = [drop["id"] for drop in self.inventory["gameEventDrops"]]
        self.watched_drops = {
            drop["id"]: drop["self"]["currentMinutesWatched"]
            for campaign in self.inventory["dropCampaignsInProgress"]
            for drop in campaign["timeBasedDrops"]
        }

        logger.info("Inventory updated")

    def update_campaigns(self):
        if self.campaigns is None: self.campaigns = self.load_campaigns_cache()

        new_campaigns = list(filter(lambda x: x["status"] == "ACTIVE", self.api.get_campaigns()))

        ids = [campaign["id"] for campaign in new_campaigns]

        self.campaigns = self.get_full_campaign_data_batch(ids)

        self.save_campaigns_cache(self.campaigns)

        logger.info(f"Loaded {len(self.campaigns)} campaigns")

    def get_channels_to_mine(self, channels, game_id):
        result = []
        for i in range(0, len(channels), 35):
            request = []
            channels_to_request = channels[i:i+35]

            logger.debug(f"Scraping banch channels {i}")

            for channel in channels_to_request:
                request.append({  # noqa: PERF401
                    "operationName": "VideoPlayerStreamInfoOverlayChannel",
                    "variables": {
                        "channel": channel,
                    },
                    "extensions": {
                        "persistedQuery": {
                             "sha256Hash": HASHES["VideoPlayerStreamInfoOverlayChannel"],
                                "version": 1,
                        },
                    },
                })

            result.extend(self.api.send_raw_request(request))

        result = list(filter(lambda x: x["data"]["user"] and x["data"]["user"]["stream"] and x["data"]["user"]["broadcastSettings"]["game"] and x["data"]["user"]["broadcastSettings"]["game"]["id"] == game_id, result)) # We need to found only LIVE streams and streaming that game.
        return [i["data"]["user"]["login"] for i in result]
