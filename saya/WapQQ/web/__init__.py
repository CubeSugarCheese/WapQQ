import asyncio
from asyncio import Task

from graia.ariadne.app import Ariadne
from uvicorn import Config
from uvicorn.server import Server

from .config import host, port
from .utils import rewrite_logging_logger, rewrite_ariadne_logger, ModifiedServer
from .webserver import sanic, setApplication

rewrite_logging_logger('uvicorn.error')
rewrite_logging_logger('uvicorn.access')
rewrite_logging_logger('uvicorn.asgi')

rewrite_ariadne_logger()


task: Task
server: ModifiedServer
application: Ariadne


async def launch_webserver(app: Ariadne):
    global server, task, application
    server = Server(Config(sanic, host=host, port=port, log_config=None, reload=False))
    task = asyncio.create_task(server.serve())
    application = app
    await setApplication(app)


async def stop_webserver():
    global server, task
    server.should_exit = True
    times = 0
    while not server.shutdown_status:
        if times > 10:
            server.force_exit = True
        elif times > 20:
            break
        await asyncio.sleep(0.1)
        times += 1
    task.cancel()
