from dataclasses import dataclass
from typing import Optional
from time import strftime, localtime

from graia.ariadne.message.chain import MessageChain


@dataclass
class MessageContainer:
    time: str
    timestamp: float
    message: MessageChain
    sender_id: int
    sender_name: str
    group_id: Optional[int]
    group_name: Optional[str]


def get_time_by_timestamp(timestamp: float) -> str:
    return strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp))
