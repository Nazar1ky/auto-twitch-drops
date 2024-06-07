CLIENT_ID = "r8s4dac0uhzifbpu9sjdiwzctle17ff"
USER_AGENT = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.366"
DIRECTORYPAGE_REQUESTID = "JIRA-VXP-2397"
WEBSOCKET = "wss://pubsub-edge.twitch.tv/v1"

HASHES = {
    "Inventory": "37fea486d6179047c41d0f549088a4c3a7dd60c05c70956a1490262f532dccd9",
    "DropsPage_ClaimDropRewards": "a455deea71bdc9015b78eb49f4acfbce8baa7ccbedd28e549bb025bd0f751930",
    "ViewerDropsDashboard": "8d5d9b5e3f088f9d1ff39eb2caab11f7a4cf7a3353da9ce82b5778226ff37268",
    "DropCampaignDetails": "e5916665a37150808f8ad053ed6394b225d5504d175c7c0b01b9a89634c57136",
    "VideoPlayerStreamInfoOverlayChannel": "a5f2e34d626a9f4f5c0204f910bab2194948a9502089be558bb6e779a9e1b3d2",
    "DirectoryPage_Game": "3c9a94ee095c735e43ed3ad6ce6d4cbd03c4c6f754b31de54993e0d48fd54e30",
}

class GQLOperations:
    url = "https://gql.twitch.tv/gql"

    DirectoryPage_Game = {
        "operationName": "DirectoryPage_Game",
        "variables": {
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
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "3c9a94ee095c735e43ed3ad6ce6d4cbd03c4c6f754b31de54993e0d48fd54e30",
            },
        },
    }
    PlaybackAccessToken = {
        "operationName": "PlaybackAccessToken",
        "variables": {
                "isLive": True,
                "isVod": False,
                "vodID": "",
                "playerType": "site",
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "3093517e37e4f4cb48906155bcd894150aef92617939236d2508f3375ab732ce",
            },
        },
    }
    WithIsStreamLiveQuery = {
        "operationName": "WithIsStreamLiveQuery",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "04e46329a6786ff3a81c01c50bfa5d725902507a0deb83b0edbf7abe7a3716ea",
            },
        },
    }
    VideoPlayerStreamInfoOverlayChannel = {
        "operationName": "VideoPlayerStreamInfoOverlayChannel",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "a5f2e34d626a9f4f5c0204f910bab2194948a9502089be558bb6e779a9e1b3d2",
            },
        },
    }
    ClaimCommunityPoints = {
        "operationName": "ClaimCommunityPoints",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "46aaeebe02c99afdf4fc97c7c0cba964124bf6b0af229395f1f6d1feed05b3d0",
            },
        },
    }
    CommunityMomentCallout_Claim = {
        "operationName": "CommunityMomentCallout_Claim",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "e2d67415aead910f7f9ceb45a77b750a1e1d9622c936d832328a0689e054db62",
            },
        },
    }
    DropsPage_ClaimDropRewards = {
        "operationName": "DropsPage_ClaimDropRewards",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "a455deea71bdc9015b78eb49f4acfbce8baa7ccbedd28e549bb025bd0f751930",
            },
        },
    }
    ChannelPointsContext = {
        "operationName": "ChannelPointsContext",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "1530a003a7d374b0380b79db0be0534f30ff46e61cffa2bc0e2468a909fbc024",
            },
        },
    }
    JoinRaid = {
        "operationName": "JoinRaid",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "c6a332a86d1087fbbb1a8623aa01bd1313d2386e7c63be60fdb2d1901f01a4ae",
            },
        },
    }
    ModViewChannelQuery = {
        "operationName": "ModViewChannelQuery",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "df5d55b6401389afb12d3017c9b2cf1237164220c8ef4ed754eae8188068a807",
            },
        },
    }
    Inventory = {
        "operationName": "Inventory",
        "variables": {"fetchRewardCampaigns": True},
        # "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "37fea486d6179047c41d0f549088a4c3a7dd60c05c70956a1490262f532dccd9",
            },
        },
    }
    MakePrediction = {
        "operationName": "MakePrediction",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "b44682ecc88358817009f20e69d75081b1e58825bb40aa53d5dbadcc17c881d8",
            },
        },
    }
    ViewerDropsDashboard = {
        "operationName": "ViewerDropsDashboard",
        # "variables": {},
        "variables": {"fetchRewardCampaigns": True},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "8d5d9b5e3f088f9d1ff39eb2caab11f7a4cf7a3353da9ce82b5778226ff37268",
            },
        },
    }
    DropCampaignDetails = {
        "operationName": "DropCampaignDetails",
        "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "f6396f5ffdde867a8f6f6da18286e4baf02e5b98d14689a69b5af320a4c7b7b8",
            },
        },
    }
    DropsHighlightService_AvailableDrops = {
        "operationName": "DropsHighlightService_AvailableDrops",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "9a62a09bce5b53e26e64a671e530bc599cb6aab1e5ba3cbd5d85966d3940716f",
            },
        },
    }
    ReportMenuItem = {  # Use for replace https://api.twitch.tv/helix/users?login={self.username}
        "operationName": "ReportMenuItem",
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "8f3628981255345ca5e5453dfd844efffb01d6413a9931498836e6268692a30c",
            },
        },
    }
    PersonalSections = (
        {
            "operationName": "PersonalSections",
            "variables": {
                "input": {
                    "sectionInputs": ["FOLLOWED_SECTION"],
                    "recommendationContext": {"platform": "web"},
                },
                "channelLogin": None,
                "withChannelUser": False,
                "creatorAnniversariesExperimentEnabled": False,
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "9fbdfb00156f754c26bde81eb47436dee146655c92682328457037da1a48ed39",
                },
            },
        },
    )
    ChannelFollows = {
        "operationName": "ChannelFollows",
        "variables": {"limit": 100, "order": "ASC"},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "eecf815273d3d949e5cf0085cc5084cd8a1b5b7b6f7990cf43cb0beadf546907",
            },
        },
    }
