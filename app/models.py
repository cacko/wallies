from enum import StrEnum


class ZSONType(StrEnum):
    REQUEST = "request"
    RESPONSE = "response"
    PING = "ping"
    PONG = "pong"
