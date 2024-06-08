import string
from datetime import datetime
from random import sample


def create_nonce(length=30) -> str:
    return "".join(sample(string.digits + string.ascii_letters, length))

def sort_campaigns(data): # HACK I need make that better!
    data.sort(key=lambda x: (x["game"]["displayName"], -x["allow"]["isEnabled"],  datetime.fromisoformat(x["endAt"]), datetime.fromisoformat(x["endAt"])))
    for campaign in data:
        campaign["timeBasedDrops"].sort(key=lambda x: x["requiredMinutesWatched"])
    return data
