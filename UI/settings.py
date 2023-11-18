# %%
import json
from collections import UserDict

from typing import Any
from config import config


class Settings(UserDict):
    def __init__(self):
        super().__init__(self._get_settings())

    def save_settings(self):
        with open(config.SETTINGS_PATH, "w") as file:
            json.dump(self.data, file, indent=4)

    def _get_settings(self) -> dict:
        with open(config.SETTINGS_PATH, "r") as file:
            return json.load(file)