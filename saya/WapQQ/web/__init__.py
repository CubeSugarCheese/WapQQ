import asyncio
from asyncio import Task

from graia.ariadne.app import Ariadne
from uvicorn import Config

from .config import host, port
from .utils import NoSignalServer
from .webserver import sanic, setApplication


task: Task
server: NoSignalServer


async def launch_webserver():
    global server, task
    server = NoSignalServer(Config(sanic, host=host, port=port, log_config=None, reload=False))
    task = asyncio.create_task(server.serve())


async def stop_webserver():
    global server, task
    server.should_exit = True
    times = 0
    while not task.done():
        if times > 10:
            server.force_exit = True
        elif times > 20:
            task.cancel()
            break
        await asyncio.sleep(0.1)
        times += 1
