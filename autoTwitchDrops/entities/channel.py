class Channel:
    def __init__(self, data):
        self.isStream = data["user"]["stream"] and data["user"]["broadcastSettings"]["game"]
        if self.isStream:
            self.nickname = data["user"]["login"]
            self.game = data["user"]["broadcastSettings"]["game"]
