import json
import logging
import time
import urllib
from datetime import datetime

import requests

from .constants import HASHES
from .TwitchApi import TwitchApi
from .utils import get_drop_image_id
from .WebSocket import TwitchWebSocket

logger = logging.getLogger()

class TwitchMine:
    def __init__(self, login):
        self.login = login
        self.can_be_claimed = []
        self.campaigns = None
        self.api = TwitchApi(login)
        self.get_inventory()
        self.update_campaigns()
        self.claim_all_drops()
        self.socket = TwitchWebSocket(self)
        self.socket.run()

    def start(self):
        # Btw need to start by watched time drops and required time TODO
        campaigns = self.get_campaigns_to_mine("MultiVersus")
        for campaign in campaigns:
            if campaign.get("channels"):
                for channel in campaign["channels"]: # Scrap category to check all streamers
                    channel_information = self.api.get_channel_information(channel["name"])
                    logger.info(f"Channel Information {channel["name"]}")
                    logger.debug(f"Checking {channel["name"]} | {channel_information}")
                    if channel_information["stream"] and channel_information["broadcastSettings"]["game"]["id"] == campaign["game"]["id"]:
                        logger.info(f"CHANNEL | Starting Watch {channel["name"]} | Time {campaign["time_required"]}.")
                        self.watch(channel["name"], campaign["drop_id"], campaign["time_watched"], campaign["time_required"])

            else:
                channel = self.get_category_streamers(campaign["game"]["slug"])[0]["node"]["broadcaster"]["login"]
                logger.info(f"CATEGORY | Starting Watch {channel} | Time {campaign["time_required"]}.")
                self.watch(channel, campaign["drop_image_id"])


    def watch(self, channel_name, drop_image_id):
        while True:
            self.send_watch(channel_name)
            if drop_image_id in self.can_be_claimed:
                logger.info("Mined drop!")
                self.get_inventory()
                self.claim_all_drops()

                # TODO
                # can be maked without claiming all drops with that build: USER_ID#0990315b-0147-11ef-b296-0a58a9feac02#470f72e7-0147-11ef-8eac-0a58a9feac02
                #                                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                #                                                                            CAMPAIGN ID                             DROP ID

                self.can_be_claimed.remove(drop_image_id)
                break

            time.sleep(14)

    def send_watch(self, channel_name):
        data = self.api.playback_access_token(channel_name)

        value = urllib.parse.quote_plus(data["value"])
        signature = data["signature"]

        r = requests.get(f"https://usher.ttvnw.net/api/channel/hls/{channel_name}.m3u8?sig={signature}&token={value}")
        logger.debug(r.text)
        video_url = r.text.split("\n")[-1]

        r = requests.get(video_url)
        logger.debug(r.text)
        # urls = re.findall(r"https?://[^\s]+", r.text)
        lowest_quality_url = r.text.split("\n")[-2]

        r = requests.head(lowest_quality_url)
        if r.status_code == 200:
            logger.info(f"Request to watch {channel_name} sent successfully")


    def claim_all_drops(self):
        inventory = self.inventory

        for campaign in inventory["dropCampaignsInProgress"]:
            for item in campaign["timeBasedDrops"]:
                if item["requiredMinutesWatched"] <= item["self"]["currentMinutesWatched"] and item["self"]["isClaimed"] is False:
                    self.api.claim_drop(item["self"]["dropInstanceID"])
                    logger.info(f"Claimed drop {item["name"]}")


    def get_category_streamers(self, game_slug):
        streamers = self.api.get_category_streamers(game_slug)

        return streamers


    def get_campaigns_to_mine(self, game_name = None):
        game_name = game_name.lower() if game_name else None

        result = []

        for campaign in self.campaigns:

            if game_name and campaign["game"]["displayName"].lower() != game_name.lower():
                continue

            # Check if date is valid

            for drop in campaign["timeBasedDrops"]:
                drop_id = drop["benefitEdges"][0]["benefit"]["id"]
                if drop_id in self.claimed_drops:
                    continue

                logger.info(f"Founded eligable drop {drop["benefitEdges"][0]["benefit"]["name"]}")

                already_watched = 0

                founded = False

                for campaigns_inventory in self.inventory["dropCampaignsInProgress"]:
                    if founded:
                        break

                    for drop_inventory in campaigns_inventory["timeBasedDrops"]:
                        if drop_inventory["benefitEdges"][0]["benefit"]["id"] == drop_id:
                            already_watched = drop_inventory["self"]["currentMinutesWatched"]
                            founded = True
                            break

                time_required = drop["requiredMinutesWatched"] - already_watched

                result.append({
                    "channels": campaign["allow"]["channels"],
                    "time_required": drop["requiredMinutesWatched"],
                    "time_watched": already_watched,
                    "time_required_minused": time_required,
                    "game": campaign["game"],
                    "drop_id": drop_id,
                    "drop_name": drop["benefitEdges"][0]["benefit"]["name"],
                    "drop_image_id": get_drop_image_id(drop["benefitEdges"][0]["benefit"]["imageAssetURL"]),
                })

        # BTW sort by end too required.

        return result

    def get_inventory(self):
        self.inventory = self.api.get_inventory()
        self.claimed_drops = [drop["id"] for drop in self.inventory["gameEventDrops"]]

        logger.info("Inventory loaded")

    def update_campaigns(self):
        if self.campaigns is None: self.campaigns = self.load_campaigns_cache()

        new_campaigns = list(filter(lambda x: x["status"] == "ACTIVE", self.api.get_campaigns()))

        ids = [campaign["id"] for campaign in new_campaigns]

        self.campaigns = self.get_full_campaign_data_batch(ids)

        self.save_campaigns_cache(self.campaigns)

        logger.info(f"Loaded {len(self.campaigns)} campaigns")
        # Should be searched in campaigns, if not founded then scrap, and update cache :)

    def get_full_campaign_data_batch(self, ids):
        result = []
        for i in range(0, len(ids), 35):
            ids_to_request = ids[i:i+35]
            requests = []
            for id_ in ids_to_request:
                requests.append({
                    "operationName": "DropCampaignDetails",
                    "variables": {
                        "dropID": id_,
                        "channelLogin": self.login.user_id,
                    },
                    "extensions": {
                        "persistedQuery": {
                            "version": 1,
                            "sha256Hash": HASHES["DropCampaignDetails"],
                        },
                    },
                })

            result.extend(self.api.send_raw_request(requests))

        for i in range(len(result)):
            result[i] = result[i]["data"]["user"]["dropCampaign"]

        result.sort(key=lambda x: datetime.strptime(x["endAt"], "%Y-%m-%dT%H:%M:%S.%fZ"))  # noqa: DTZ007

        return result

    def load_campaigns_cache(self):
        try:
            with open("campaigns.json", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return {}

    def save_campaigns_cache(self, data):
        with open("campaigns.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
