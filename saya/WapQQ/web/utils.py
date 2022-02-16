import logging
import os
import socket
import sys
from pathlib import Path
from typing import Optional

import click
from jinja2 import FileSystemLoader, Environment
from loguru import logger
from prompt_toolkit.patch_stdout import StdoutProxy
from sanic import Request
from uvicorn.server import Server

current_path = Path(__file__).parents[0]


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


class ModifiedServer(Server):
    shutdown_status: bool

    async def serve(self, sockets: Optional[list[socket.socket]] = None) -> None:
        # 魔改 —— Start
        logger = logging.getLogger('uvicorn.error')
        self.shutdown_status = False
        # 魔改 —— End

        process_id = os.getpid()

        config = self.config
        if not self.config.loaded:
            config.load()

        self.lifespan = config.lifespan_class(config)

        message = "Started server process [%d]"
        color_message = "Started server process [" + click.style("%d", fg="cyan") + "]"
        logger.info(message, process_id, extra={"color_message": color_message})

        await self.startup(sockets=sockets)
        if self.should_exit:
            return
        await self.main_loop()
        await self.shutdown(sockets=sockets)

        message = "Finished server process [%d]"
        color_message = "Finished server process [" + click.style("%d", fg="cyan") + "]"
        logger.info(message, process_id, extra={"color_message": color_message})

        # 魔改 —— Start
        self.shutdown_status = True
        # 魔改 —— End


async def _build_env():
    loader = FileSystemLoader(current_path / "resources" / "templates")
    environment = Environment(loader=loader, enable_async=True)
    environment.filters["datefmt"] = lambda x: x.strftime('%Y-%m-%d')
    return environment


async def render_template(file_name: str, **kwargs):
    environment = await _build_env()
    template = environment.get_template(file_name)
    rendered_template = await template.render_async(**kwargs)
    return rendered_template
