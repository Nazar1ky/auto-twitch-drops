import copy
import logging
import urllib

import aiohttp

from .constants import (
    GQLOperations,
)


class TwitchApi:
    logger = logging.getLogger(__name__)

    def __init__(self, session, login):
        self._sess = session
        self.login = login
        self._sess.headers.update({
            "authorization": f"OAuth {login.access_token}",
        })
        self.max_requests_per_batch = 35

    async def send_requests(self, request):
        self.logger.debug(f"Requests {request}")

        async with self._sess.post(GQLOperations.url, json=request) as response:
            data = await response.json()

        self.logger.debug(f"Responses {data}")

        for i, r in enumerate(data):
            if r.get("errors"):
                raise RuntimeError(f"Error in request {request}\nResponse: {data}")

            data[i] = data[i]["data"]

        return data

    async def send_request(self, request):

        self.logger.debug(f"Request {request}")

        attempt = 0

        while True:
            async with self._sess.post(GQLOperations.url, json=request) as response:
                data = await response.json()

            self.logger.debug(f"Response {data}")

            if data.get("errors"):
                self.logger.error(f"Error in request {request}\nResponse: {data}")
                attempt += 1
                if attempt >= 3:
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

    async def playback_access_token(self, channel_name):
        data = copy.deepcopy(GQLOperations.PlaybackAccessToken)
        data["variables"]["login"] = channel_name

        response = await self.send_request(data)

        if not response.get("streamPlaybackAccessToken"):
            raise RuntimeError("Streamer not founded")

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
        data["variables"]["limit"] = 100 # To request 100 channels per request (Limit)
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

            data["variables"]["cursor"] = response["edges"][-1]["cursor"]

        return channels # HACK Idk, if raise there error but if no streamers it return just [] (empty list)


    async def get_channels_information(self, channels):
        result = []

        for i in range(0, len(channels), self.max_requests_per_batch):
            channels_to_request = channels[i:i+self.max_requests_per_batch]

            request = []

            for channel in channels_to_request:
                data = copy.deepcopy(GQLOperations.VideoPlayerStreamInfoOverlayChannel)
                data["variables"]["channel"] = channel

                request.append(data)
            result.extend(await self.send_requests(request))

        return result

    async def get_full_campaigns_data(self, ids):
        campaigns = []

        for i in range(0, len(ids), self.max_requests_per_batch):
            ids_to_request = ids[i:i+self.max_requests_per_batch]

            request = []

            for id_ in ids_to_request:
                data = copy.deepcopy(GQLOperations.DropCampaignDetails)
                data["variables"]["channelLogin"] = self.login.user_id
                data["variables"]["dropID"] = id_

                request.append(data)

            campaigns.extend(await self.send_requests(request))

        return campaigns

    async def send_watch(self, channel_name): # Used to watch, request every 15 seconds
        data = await self.playback_access_token(channel_name)

        value = urllib.parse.quote_plus(data["value"])
        signature = data["signature"]

        try:
            async with self._sess.get(f"https://usher.ttvnw.net/api/channel/hls/{channel_name}.m3u8?sig={signature}&token={value}") as response:
                video_urls = await response.text()
        except aiohttp.client_exceptions.ClientResponseError as ex:
            raise RuntimeError("Streamer offline.") from ex

        self.logger.debug(video_urls)

        video_url = video_urls.split("\n")[-1]

        async with self._sess.get(video_url) as response:
            low_quality_video = await response.text()

        self.logger.debug(low_quality_video)

        # urls = re.findall(r"https?://[^\s]+", low_quality_video) # We can requests these urls every 2 seconds like Twitch do, but we request last one every 15 seconds.
        lowest_quality_url = low_quality_video.split("\n")[-2]

        await self._sess.head(lowest_quality_url)

    async def claim_drop(self, drop_id):
        data = copy.deepcopy(GQLOperations.DropsPage_ClaimDropRewards)

        data["variables"] = {
            "input": {
                "dropInstanceID": drop_id,
            },
        }

        response = await self.send_request(data)

        if not response.get("claimDropRewards"):
            raise RuntimeError("Incorrect drop id to claim")

        return response
