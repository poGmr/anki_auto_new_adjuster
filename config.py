import json
from aqt import mw
import logging
from .addon_config import AddonConfig


class DeckConfig:
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, did: str, add_on_config: AddonConfig) -> None:
        self.add_on_config: AddonConfig = add_on_config
        self.did = did
        self.raw_data = mw.col.decks.config_dict_for_deck_id(did)
        self.id: str = str(self.raw_data["id"])
        self.name = self.raw_data["name"]

    def get_pretty_config_data(self) -> str:
        return json.dumps(self.raw_data, indent=4)

    def set_new_count(self, new_count: int) -> None:
        if self.raw_data["new"]["perDay"] == new_count:
            self.logger.debug(f"[{self.name}] No change of value ({new_count}) is needed.")
            return
        if new_count < 0:
            self.logger.debug(f"[{self.name}] Input value ({new_count}) is less than zero.")
            return
        self.raw_data["new"]["perDay"] = new_count
        mw.col.decks.save(self.raw_data)
        self.logger.debug(f"[{self.name}] value {new_count} of new cards per day has been saved to the configuration.")
