import asyncio
import logging
import os
import sys
from pathlib import Path

from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import config, WebsocketClientConfig, HttpClientConfig
from graia.broadcast import Broadcast
from graia.broadcast.interrupt import InterruptControl
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from loguru import logger
from prompt_toolkit.patch_stdout import StdoutProxy

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
bcc = create(Broadcast)
inc = InterruptControl(bcc)
app = Ariadne(
    connection=config(
        appConfig.account,  # 你的机器人的 qq 号
        appConfig.verify_key,  # 填入你的 mirai-api-http 配置中的 verifyKey
        HttpClientConfig(host=appConfig.http_host),
        WebsocketClientConfig(host=appConfig.ws_host),
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


# https://loguru.readthedocs.io/en/stable/overview.html?highlight=InterceptHandler#entirely-compatible-with-standard-logging
class InterceptHandler(logging.StreamHandler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        msg = self.format(record)  # 官方实现中使用record.getMessage()来获取msg，但在sanic中会漏掉它配置过的日志模板，因此要用self.format(record)
        logger.opt(depth=depth, exception=record.exc_info).log(level, msg)


def rewrite_logging_logger(logger_name: str):
    logging_logger = logging.getLogger(logger_name)
    for handler in logging_logger.handlers:
        logging_logger.removeHandler(handler)
    logging_logger.addHandler(InterceptHandler())
    logging_logger.setLevel(logging.DEBUG)


def rewrite_ariadne_logger(debug: bool = False, graia_console: bool = False):
    logger.remove()
    if debug:
        log_format = (
            '<green>{time:YYYY-MM-DD HH:mm:ss.SSSS}</green> | <level>{level: <9}</level> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> '
        )
        log_level = 'DEBUG'
    else:
        log_format = (
            '<green>{time:YYYY-MM-DD HH:mm:ss.SS}</green> | <level>{level: <8}</level> | '
            '<cyan>{name}</cyan> - <level>{message}</level>'
        )
        log_level = 'INFO'
    if graia_console:
        logger.add(
            StdoutProxy(raw=True),
            level=log_level,
            format=log_format,
            colorize=True,
            backtrace=True,
            diagnose=True,
            enqueue=False,
        )
    else:
        logger.add(
            sys.stderr, level=log_level, format=log_format, colorize=True, backtrace=True, diagnose=True, enqueue=False
        )
    logger.add(
        Path(Path.cwd(), 'logs', 'latest.log'),
        rotation='00:00',
        retention="30 days",
        compression='zip',
        encoding='utf-8',
        level=log_level,
        format=log_format,
        colorize=False,
        backtrace=True,  # 格式化的异常跟踪是否应该向上扩展，超出捕获点，以显示生成错误的完整堆栈跟踪。
        diagnose=True,  # 异常跟踪是否应显示变量值以简化调试。这应该在生产中设置为 False 以避免泄露敏感数据。
        enqueue=True,  # 要记录的消息是否应在到达接收器之前首先通过多进程安全队列。这在通过多个进程记录到文件时很有用。这也具有使日志记录调用非阻塞的优点。
    )


rewrite_logging_logger('uvicorn.error')
rewrite_logging_logger('uvicorn.access')
rewrite_logging_logger('uvicorn.asgi')

rewrite_ariadne_logger()

if __name__ == "__main__":
    app.launch_blocking()
