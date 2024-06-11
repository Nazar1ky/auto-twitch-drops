class Drop:
    def __init__(self, data):
        self.id_ = data["id"]
        self.name = data["name"]
        self.required_time = data["requiredMinutesWatched"]
        self.benefits_ids = [benefit["benefit"]["id"] for benefit in data["benefitEdges"]]

        if data.get("self"):
            self.claimed = data["self"]["isClaimed"]
            self.watched_time = data["self"]["currentMinutesWatched"]
            self.instanceId = data["self"]["dropInstanceID"]
