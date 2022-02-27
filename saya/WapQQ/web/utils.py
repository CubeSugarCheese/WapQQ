from pathlib import Path

from jinja2 import FileSystemLoader, Environment
from uvicorn.server import Server

current_path = Path(__file__).parents[0]


class NoSignalServer(Server):
    def install_signal_handlers(self) -> None:
        """复写该方法，使得 uvicorn 不会接管 signal """
        return


async def _build_env():
    loader = FileSystemLoader(current_path / "resources" / "templates")
    environment = Environment(loader=loader, enable_async=True, lstrip_blocks=True, trim_blocks=True)
    environment.filters["datefmt"] = lambda x: x.strftime('%Y-%m-%d')
    return environment


async def render_template(file_name: str, **kwargs) -> str:
    environment = await _build_env()
    template = environment.get_template(file_name)
    rendered_template = await template.render_async(**kwargs)
    return rendered_template
