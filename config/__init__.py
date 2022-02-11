import yaml
from pathlib import Path

from loguru import logger


class Config:
    host: str
    verify_key: str
    account: int
    init: bool

    def __init__(self):
        self.load_config()

    def load_config(self):
        with Path("config\config.yaml").open("r") as f:
            config_ = yaml.load(f)
            if not config_["init"] is True:
                logger.critical("你还没有完成设置！请将 init 设置为 true！")
                quit()
            self.host = config_["host"]
            self.verify_key = config_["verify_key"]
            self.account = config_["account"]
            self.init = config_["init"]


appConfig = Config()
