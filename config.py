import json
from aqt import mw
import logging


class DeckConfig:
    def __init__(self, logger: logging, deck_id: str) -> None:
        self.logger: logging = logger
        self.deck_id = deck_id
        self.raw_data = mw.col.decks.config_dict_for_deck_id(deck_id)
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
