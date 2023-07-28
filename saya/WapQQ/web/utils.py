from pathlib import Path

from uvicorn.server import Server

current_path = Path(__file__).parents[0]


class NoSignalServer(Server):
    def install_signal_handlers(self) -> None:
        """复写该方法，使得 uvicorn 不会接管 signal """
        return
