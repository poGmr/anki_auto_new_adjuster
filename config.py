import json
from aqt import mw


class Config:
    def __init__(self, raw_data, logger) -> None:
        self.rawData = raw_data
        self.logger = logger
        self.id = self.rawData["id"]
        self.name = self.rawData["name"]
        self.update()

    def update(self):
        self.id = self.rawData["id"]
        self.name = self.rawData["name"]

    def get_pretty_config_data(self):
        return json.dumps(self.rawData, indent=4)

    def set_new_count(self, new_count: int):
        if self.rawData["new"]["perDay"] != new_count:
            self.rawData["new"]["perDay"] = new_count
            mw.col.decks.save(self.rawData)
            self.logger.info(
                f"[{self.name}] value {new_count} of new cards per day has been saved to the configuration.")
            self.update()
