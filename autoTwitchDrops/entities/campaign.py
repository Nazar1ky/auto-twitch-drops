from datetime import datetime

from .drop import Drop


class Campaign:
    def __init__(self, data):
        self.id_ = data["id"]
        self.name = data["name"]
        self.status = data["status"]
        self.game = data["game"]
        self.endAt = datetime.fromisoformat(data["endAt"])
        self.drops = [Drop(x) for x in data["timeBasedDrops"]]
        self.channelsEnabled = data["allow"]["isEnabled"] if data["allow"].get("isEnabled") is not None else None
        self.channels = [x["name"] for x in data["allow"]["channels"]] if self.channelsEnabled else None

