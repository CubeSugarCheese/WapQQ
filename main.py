import os
import asyncio

from pathlib import Path

from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast import BroadcastBehaviour
from loguru import logger
from graia.broadcast import Broadcast
from graia.saya import Saya
from graia.ariadne.app import Ariadne
from graia.ariadne.model import MiraiSession

from config import appConfig

LOGPATH = Path("./logs")
LOGPATH.mkdir(exist_ok=True)
logger.add(
    LOGPATH.joinpath("latest.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="30 days",
    compression="tar.xz",
    colorize=False,
)
logger.info("Bot is starting...")

ignore = ["__init__.py", "__pycache__"]

loop = asyncio.new_event_loop()
bcc = Broadcast(loop=loop)
inc = InterruptControl(bcc)
app = Ariadne(
    broadcast=bcc,
    connect_info=MiraiSession(
        host=appConfig.host,
        account=appConfig.account,
        verify_key=appConfig.verify_key,
    ),
)
saya = Saya(bcc)
saya.install_behaviours(BroadcastBehaviour(bcc))
with saya.module_context():
    for module in os.listdir("saya"):
        if module in ignore:
            continue
        if os.path.isdir(module):
            saya.require(f"saya.{module}")
        else:
            saya.require(f"saya.{module.split('.')[0]}")
    logger.info("saya加载完成")

if __name__ == "__main__":
    app.launch_blocking()
