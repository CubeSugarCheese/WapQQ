import yaml
from pathlib import Path

from loguru import logger


class Config:
    http_host: str
    ws_host: str
    verify_key: str
    account: int
    init: bool

    def __init__(self):
        self.load_config()

    def load_config(self):
        try:
            with Path("config/config.yaml").open("r") as f:
                config_ = yaml.safe_load(f)
                if not config_["init"] is True:
                    logger.critical("你还没有完成设置！请将 init 设置为 true！")
                    quit()
                self.http_host = config_["http_host"]
                self.ws_host = config_["ws_host"]
                self.verify_key = config_["verify_key"]
                self.account = config_["account"]
                self.init = config_["init"]
        except FileNotFoundError:
            logger.critical("你还没有完成设置！请编辑 config.yaml.sample 文件并将文件名改为 config.yaml ！")


appConfig = Config()
