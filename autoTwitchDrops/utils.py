import string
from datetime import datetime
from random import sample

from . import Campaign, Drop


def create_nonce(length=30) -> str:
    return "".join(sample(string.digits + string.ascii_letters, length))

def sort_campaigns(data):
    return sorted(data, key=lambda x: (
        -x.channelsEnabled,
        x.game["displayName"],
        x.endAt))

def get_drops_to_claim(inventory):
    drops_to_claim = []
    if inventory.get("dropCampaignsInProgress"):
        for campaign in inventory["dropCampaignsInProgress"]:
            if campaign["status"] == "EXPIRED":
                continue

            if not campaign.get("timeBasedDrops"):
                continue

            for drop in campaign["timeBasedDrops"]:
                if not drop["self"]["isClaimed"] and drop["self"]["currentMinutesWatched"] >= drop["requiredMinutesWatched"]:
                    drops_to_claim.append(drop["self"]["dropInstanceID"])  # noqa: PERF401

    return drops_to_claim

def filter_campaigns(inventory, total_campaigns):  # noqa: C901
    campaigns = []
    claimed_drops_ids = []
    claimed_benefits = {}

    if inventory.get("dropCampaignsInProgress"):
        for campaign in inventory["dropCampaignsInProgress"]:
            if campaign["status"] == "EXPIRED":
                continue

            if not campaign.get("timeBasedDrops"):
                continue

            for drop in campaign["timeBasedDrops"]:
                if drop["self"]["isClaimed"] or drop["self"]["currentMinutesWatched"] >= drop["requiredMinutesWatched"]:
                    claimed_drops_ids.append(drop["id"])  # noqa: PERF401
    else:
        claimed_drops_ids = []

    if inventory.get("gameEventDrops"):
        for benefit in inventory["gameEventDrops"]:
            claimed_benefits[benefit["id"]] = datetime.fromisoformat(benefit["lastAwardedAt"])

    else:
        claimed_benefits = []

    if total_campaigns:
        for campaign in total_campaigns:
            this_campaign_added = False

            if campaign["status"] == "EXPIRED":
                continue

            if not campaign.get("timeBasedDrops"):
                continue

            started_at = datetime.fromisoformat(campaign["startAt"])

            for drop in campaign["timeBasedDrops"]:
                add_this_drop = False

                if drop["id"] in claimed_drops_ids:
                    continue

                for benefit in drop["benefitEdges"]:
                    if claimed_benefits.get(benefit["benefit"]["id"]):
                        if started_at > claimed_benefits[benefit["benefit"]["id"]]:
                            add_this_drop = True
                    else:
                        add_this_drop = True

                if add_this_drop:
                    if not this_campaign_added:
                        campaigns.append(Campaign(campaign))
                        this_campaign_added = True

                    campaigns[-1].drops.append(Drop(drop))
    else:
        campaigns = []

    return campaigns
