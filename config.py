import json
from aqt import mw
import logging


class Config:
    def __init__(self, raw_data: dict[str, dict], logger: logging) -> None:
        self.raw_data: dict[str, dict] = raw_data
        self.logger: logging = logger
        self.id = self.raw_data["id"]
        self.name = self.raw_data["name"]

    def get_pretty_config_data(self) -> str:
        return json.dumps(self.raw_data, indent=4)

    def set_new_count(self, new_count: int) -> None:
        if self.raw_data["new"]["perDay"] != new_count:
            self.raw_data["new"]["perDay"] = new_count
            mw.col.decks.save(self.raw_data)
            self.logger.info(
                f"[{self.name}] value {new_count} of new cards per day has been saved to the configuration.")
