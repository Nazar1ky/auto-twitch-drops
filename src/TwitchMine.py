import logging
from src.TwitchApi import TwitchApi
import requests
import urllib
import time
import json
import asyncio
import aiohttp
import re

# Currently project stopped

class TwitchMine:
    def __init__(self, login):
        self.api = TwitchApi(login)
        self.get_inventory()
        self.update_campaigns()

    def start(self):
        # Btw need to start by watched time
        campaigns = self.get_campaigns_to_mine("rust")
        for campaign in campaigns:
            if campaign.get("channels"):
                for channel in campaign["channels"]: # Scrap category to check all streamers
                    channel_information = self.api.get_channel_information(channel["name"])
                    logging.debug(f"Checking {channel["name"]} | {channel_information}")
                    if channel_information["stream"] and channel_information["broadcastSettings"]["game"]["id"] == campaign["game"]["id"]:
                        logging.info(f"CHANNEL | Starting Watch {channel["name"]} | Time {campaign["time_required"]}.")
                        self.watch(channel["name"], campaign["drop_id"], campaign["time_required"])

            else: # WiP
                pass
                # channel = self.get_campaigns_to_mine(campaign["gameSlug"])
                # logging.info(f"CATEGORY | Starting Watch {channel} | Time {campaign["time_required"]}.")
                # self.watch(self.get_campaigns_to_mine(campaign["gameSlug"]), campaign["time_required"])


    def watch(self, channel_name, drop_id):

        while True:
            self.send_watch(channel_name)
            time.sleep(20)

            # check for websockets here, if drop mined - break.


            # if time.time() - start_time > duration:
                # self.get_inventory()
                # inv = self.inventory
                # for campaign in inv["dropCampaignsInProgress"]:
                #     for item in campaign["timeBasedDrops"]:
                #         if item["benefitEdges"][0]["benefit"]["id"] == drop_id and item["requiredMinutesWatched"] <= item["self"]["currentMinutesWatched"]:
                #             self.api.claim_drop(drop_id)
                #             break
                #         else:
                #             duration += (item["requiredMinutesWatched"] - item["self"]["currentMinutesWatched"] + 5) * 60

    def send_watch(self, channel_name):
        data = self.api.playback_access_token(channel_name)

        value = urllib.parse.quote_plus(data["value"])
        signature = data["signature"]

        r = requests.get(f"https://usher.ttvnw.net/api/channel/hls/{channel_name}.m3u8?sig={signature}&token={value}")
        logging.debug(r.text)
        video_url = r.text.split("\n")[-1]

        r = requests.get(video_url)
        logging.debug(r.text)
        urls = re.findall(r'https?://[^\s]+', r.text)
        lowest_quality_url = r.text.split("\n")[-2]

        # r = requests.head(lowest_quality_url)
        # if r.status_code == 200:
        #     logging.info(f"Request to watch {channel_name} sent successfully")
        # time.sleep(1.8)

    def claim_all_drops(self):
        inventory = self.my_inventory

        for campaign in inventory["dropCampaignsInProgress"]:
            for item in campaign["timeBasedDrops"]:
                if item["requiredMinutesWatched"] <= item["self"]["currentMinutesWatched"] and item["self"]["isClaimed"] is False:

                    self.api.claim_drop(item["self"]["dropInstanceID"])
                    logging.info(f"Claimed drop {item["name"]}")


        result = []

    def get_category_streamers(self, game_slug):
        data = self.api.get_category_streamers(game_slug)

        for streamer in data:
            streamer_id = streamer["node"]["broadcaster"]["id"]
            # if streamer_id in self.streamers:
                # continue

            result.append(streamer["login"])

        return result


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

                logging.info(f"DROP | Founded eligable drop {drop["benefitEdges"][0]["benefit"]["name"]}")

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
                    "time_required": time_required,
                    "game": campaign["game"],
                    "drop_id": drop_id,
                    "drop_name": drop["benefitEdges"][0]["benefit"]["name"]
                })

        # BTW sort by end too required.

        return result

    def get_inventory(self):
        self.inventory = self.api.get_inventory()
        self.claimed_drops = [drop["id"] for drop in self.inventory["gameEventDrops"]]
    
        logging.info("Inventory loaded")

    # def get_full_campaign_data(self, campaign_id):
    #     result = self.api.get_full_campaign_data(campaign_id)
    #     return result

    def update_campaigns(self):
        campaigns = self.campaigns if hasattr(self, "campaigns") else self.load_campaigns_cache()

        new_campaigns = list(filter(lambda x: x["status"] == "ACTIVE", self.api.get_campaigns()))

        result = []
        # Try to update all campaigns with one requests becuz graphql allow to send many operations 
        logging.debug(new_campaigns)

        for new_campaign in new_campaigns:
            need_get_full_data = True

            for campaign in campaigns:
                if campaign["id"] != new_campaign["id"]:
                    continue

                result.append(campaign)
                need_get_full_data = False
                break

            if need_get_full_data:
                full_campaign = self.api.get_full_campaign_data(new_campaign["id"])
                result.append(full_campaign)
                logging.info(f"Added new campaign {new_campaign["name"]}")

        self.campaigns = result
        self.save_campaigns_cache(self.campaigns)

        logging.info(f"Loaded {len(self.campaigns)} campaigns")
        # Should be searched in campaigns, if not founded then scrap, and update cache :)

    def load_campaigns_cache(self):
        try:
            with open("campaigns.json", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return {}

    def save_campaigns_cache(self, data):
        with open("campaigns.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
