import copy
import logging

import aiohttp

from .constants import (
    CLIENT_ID,
    USER_AGENT,
    GQLOperations,
)


class TwitchApi:
    logger = logging.getLogger(__name__)

    def __init__(self, session, login):
        self._sess = session
        self.login = login
        self._sess.headers.update({
            "authorization": f"OAuth {login.access_token}",
            "client-id": CLIENT_ID,
            "user-agent": USER_AGENT,
        })

    async def send_request(self, request):
        async with self._sess.post(GQLOperations.url, json=request) as response:
            data = await response.json()

        if isinstance(request, list):
            for i, r in enumerate(data):
                if r.get("errors"):
                    raise RuntimeError(f"Error in request {request}\nResponse: {data}")

                data[i] = data[i]["data"]
        else:
            if data.get("errors"):
                raise RuntimeError(f"Error in request {request}\nResponse: {data}")
            data = data["data"]

        return data

    async def get_channel_information(self, channel_name):
        data = copy.deepcopy(GQLOperations.VideoPlayerStreamInfoOverlayChannel)
        data["variables"] = {"channel": channel_name}

        response = await self.send_request(data)

        if not response.get("user"):
            raise RuntimeError("Streamer not founded")

        return response["user"]

    # async def test(self):
    #     request = []
    #     request.append(copy.deepcopy(GQLOperations.VideoPlayerStreamInfoOverlayChannel))
    #     request.append(copy.deepcopy(GQLOperations.VideoPlayerStreamInfoOverlayChannel))
    #     data = await self.send_request(request)
    #     return data

    async def playback_access_token(self, channel_name):
        data = copy.deepcopy(GQLOperations.PlaybackAccessToken)
        data["variables"]["login"] = channel_name

        response = await self.send_request(data)

        return response["streamPlaybackAccessToken"]

        # value = urllib.parse.quote_plus(data["streamPlaybackAccessToken"]["value"])
        # signature = data["streamPlaybackAccessToken"]["signature"]

    async def get_full_campaign_data(self, campaign_id):
        data = copy.deepcopy(GQLOperations.DropCampaignDetails)

        data["variables"] = {
            "channelLogin": self.login.user_id,
            "dropID": campaign_id,
        }

        response = await self.send_request(data)

        response = response["user"]

        if not response.get("dropCampaign"):
            raise RuntimeError("No campaign founded")

        return response["dropCampaign"]

    async def get_inventory(self):
        data = copy.deepcopy(GQLOperations.Inventory)
        response = await self.send_request(data)

        return response["currentUser"]["inventory"]

    async def get_campaigns(self):
        data = copy.deepcopy(GQLOperations.ViewerDropsDashboard)

        response = await self.send_request(data)

        return response["currentUser"]["dropCampaigns"]

    async def get_category_streamers(self, game_slug, limit = 100):
        data = copy.deepcopy(GQLOperations.DirectoryPage_Game)
        data["variables"]["limit"] = 100 # To request 100 channels per request
        data["variables"]["slug"] = game_slug

        channels = []

        while True:
            response = await self.send_request(data)

            if not response.get("game"):
                raise RuntimeError("That game slug not exists!")

            response = response["game"]["streams"]

            channels.extend(response["edges"])

            if len(channels) >= limit:
                break

            if not response["pageInfo"]["hasNextPage"]:
                break

            response["variables"]["cursor"] = response["edges"][-1]["cursor"]

        return channels # HACK Idk, if raise there error but if no streamers it return just [] (empty list)


# - - - - / IN WORK \ - - - - #

    async def claim_drop(self, drop_id):
        data = copy.deepcopy(GQLOperations.DropsPage_ClaimDropRewards)

        data["variables"] = {
            "input": {
                "dropInstanceID": drop_id,
            },
        }

        response = await self.send_request(data)

        # TODO need to check somehow if claimed

        return True

    async def get_full_campaigns_data(self, ids):
        campaigns = []
        campaigns_per_batch = 35 # This is limit of GraphQL

        for i in range(0, len(ids), campaigns_per_batch):
            ids_to_request = ids[i:i+campaigns_per_batch]

            request = []

            for id_ in ids_to_request:
                data = copy.deepcopy(GQLOperations.DropCampaignDetails)
                data["variables"]["channelLogin"] = self.login.user_id
                data["variables"]["dropID"] = id_

                request.append(data)

            campaigns.append(await self.send_request(request))

        return campaigns

# Here should be also imported claim_all_drops get_channels_to_mine get_full_campaign_data_batch watch

# Renaming:
# api -> twitch (Every api call)
# mine -> miner (Should be used to call api functions and just do array operations)
# WebSocket -> websocket (Websocket system to track mined Twitch drops)
