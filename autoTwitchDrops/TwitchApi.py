import logging

import requests

from .constants import CLIENT_ID, DIRECTORYPAGE_REQUESTID, HASHES, USER_AGENT

logger = logging.getLogger()

class TwitchApi:
    def __init__(self, login):
        self.login = login
        self.headers = {
            "authorization": f"OAuth {login.access_token}",
            "client-id": CLIENT_ID,
            # "device-id": login.unique_id,
            "user-agent": USER_AGENT,
        }

    def send_raw_request(self, request):
        response = requests.post(
        url="https://gql.twitch.tv/gql",
        json=request,
        headers=self.headers,
        timeout=15,
        ).json()

        return response

    def send_request(self, operation_name, variables = None):
        query = {
            "operationName": operation_name,
            "variables": variables,
            "extensions": {
                "persistedQuery": {
                     "sha256Hash": HASHES[operation_name],
                        "version": 1,
                },
            },
        }

        response = requests.post(
            url="https://gql.twitch.tv/gql",
            json=query,
            headers=self.headers,
            timeout=15,
            ).json()

        if response.get("error"):
            logger.error(f"{response} | {query}")
            return None

        return response["data"]

    def get_channel_information(self, channel_name):
        variables = {
                "channel": channel_name,
        }

        data = self.send_request("VideoPlayerStreamInfoOverlayChannel", variables)

        return data["user"]

    def claim_drop(self, drop_id):
        variables = {
            "input": {
                "dropInstanceID": drop_id,
            },
        }

        self.send_request("DropsPage_ClaimDropRewards", variables)

        # if "status" in data["claimDropRewards"]:
        #     return True

        # TODO need to check somehow if claimed

        return True

    def playback_access_token(self, channel_name):
        variables = {
                "isLive": True,
                "login": channel_name,
                "isVod": False,
                "vodID": "",
                "playerType": "site",
            }

        data = self.send_request("PlaybackAccessToken", variables)

        return data["streamPlaybackAccessToken"]

        # value = urllib.parse.quote_plus(data["streamPlaybackAccessToken"]["value"])
        # signature = data["streamPlaybackAccessToken"]["signature"]

    def get_full_campaign_data(self, campaign_id):
        variables = {
            "channelLogin": self.login.user_id,
            "dropID": campaign_id,
        }

        data = self.send_request("DropCampaignDetails", variables)["user"]["dropCampaign"]

        return data

    def get_inventory(self):
        data = self.send_request("Inventory")

        return data["currentUser"]["inventory"]

    def get_campaigns(self):
        data = {
            "operationName": "ViewerDropsDashboard",
        }

        data = self.send_request("ViewerDropsDashboard")

        return data["currentUser"]["dropCampaigns"]


    def get_category_streamers(self, game_slug, limit = 50):
        variables = {
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

        return data["game"]["streams"]["edges"]
