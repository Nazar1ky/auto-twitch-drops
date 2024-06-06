import copy
import logging

import aiohttp

from .constants import (
    CLIENT_ID,
    DIRECTORYPAGE_REQUESTID,
    USER_AGENT,
    GQLOperations,
)


class TwitchApi:
    logger = logging.getLogger()

    def __init__(self, login):
        self.login = login
        self.check_auth()
        self.headers = {
            "authorization": f"OAuth {login.access_token}",
            "client-id": CLIENT_ID,
            "user-agent": USER_AGENT,
            # "device-id": login.unique_id,
        }
        self.session = aiohttp.ClientSession()

    def check_auth(self):
        if not (self.login.nickname or self.login.user_id or self.login.access_token):
            raise RuntimeError("Not authorized.")

    async def close_session(self):
        await self.session.close()

    async def send_request(self, request):
        async with self.session.post(GQLOperations.url, json=request, headers=self.headers, raise_for_status=True) as response:
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

    def get_inventory(self):
        data = self.send_request("Inventory")

        return data["currentUser"]["inventory"]

    def get_campaigns(self):
        data = {
            "operationName": "ViewerDropsDashboard",
        }

        data = self.send_request("ViewerDropsDashboard")

        return data["currentUser"]["dropCampaigns"]


    def get_category_streamers(self, game_slug, cursor = None, limit = 100):
        variables = {
            "cursor": cursor,
            "limit": limit,
            "slug": game_slug,
            "imageWidth": 50,
            "options": {
                "broadcasterLanguages": [],
                "freeformTags": None,
                "includeRestricted": ["SUB_ONLY_LIVE"],
                "recommendationsContext": {"platform": "web"},
                "sort": "RELEVANCE",
                "tags": [],
                "systemFilters": [
                    "DROPS_ENABLED",
                ],
                "requestID": DIRECTORYPAGE_REQUESTID,
            },
            "sortTypeIsRecency": False,
        }

        data = self.send_request("DirectoryPage_Game", variables)

        return data["game"]["streams"]

# Here should be also imported claim_all_drops get_channels_to_mine get_full_campaign_data_batch
