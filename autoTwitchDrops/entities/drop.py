class Drop:
    def __init__(self, data):
        self.id_ = data["id"]
        self.name = data["name"]
        self.required_time = data["requiredMinutesWatched"]
        if data.get("self"):
            self.claimed = data["self"]["isClaimed"]
            self.watched_time = data["self"]["currentMinutesWatched"]
            self.instanceId = data["self"]["dropInstanceID"]
