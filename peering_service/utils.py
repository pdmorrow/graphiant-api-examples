import datetime


def epoch_to_utc(seconds: int, nanos: int) -> str:
    dt = datetime.datetime.fromtimestamp(
        seconds + nanos / 1e9, tz=datetime.timezone.utc
    )
    return dt.strftime("%Y-%m-%dT%H:%M")


def readable_status(status: str) -> str:
    return status.split("_")[-1]


def short_peer_type(peer_type: str) -> str:
    if peer_type == "non_graphiant_peer":
        return "External"
    else:
        return "Graphiant"
