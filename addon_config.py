from aqt import mw
import logging
from typing import Dict, Any


class AddonConfig:
    def __init__(self, logger: logging.Logger):
        self.logger: logging.Logger = logger
        self.logger.debug("__init__")
        self.raw: Dict[str, Any] = mw.addonManager.getConfig(__name__)
        self._init_decks_update()

    def __del__(self):
        self.logger.debug("__del__")
        self._save()

    def _save(self):
        self.logger.debug("_save")
        mw.addonManager.writeConfig(__name__, self.raw)

    def _init_decks_update(self):
        self._add_new_decks_to_add_on_config()
        self._update_decks_in_add_on_config()
        self._remove_old_decks_from_add_on_config()
        self.logger.debug(f"Addon config loaded and updated.")
        self._save()

    def _add_new_decks_to_add_on_config(self):
        self.logger.debug("_add_new_decks_to_add_on_config")
        if "global" not in self.raw:
            self.raw["global"] = {}
        self.raw["global"]["low_focus_level"] = 0.85
        self.raw["global"]["high_focus_level"] = 0.95
        self.raw["global"]["lowest_young_max_difficulty_sum"] = 21
        self.raw["global"]["highest_young_max_difficulty_sum"] = 210

        if "decks" not in self.raw:
            self.raw["decks"] = {}

        for deck in mw.col.decks.all_names_and_ids():
            d_id = str(deck.id)
            if d_id not in self.raw["decks"]:
                self.raw["decks"][d_id] = {
                    "name": deck.name,
                    "enabled": False,
                    "young_max_difficulty_sum": 21,
                    "last_updated": 0,
                    "young_current_difficulty_sum": 0,
                    "new_set": 0,
                    "new_done": 0,
                    "todays_user_focus_level": 0
                }

    def _update_decks_in_add_on_config(self):
        self.logger.debug("_update_decks_in_add_on_config")
        for deck in mw.col.decks.all_names_and_ids():
            d_id = str(deck.id)
            if d_id in self.raw["decks"]:
                if self.raw["decks"][d_id]["name"] != deck.name:
                    self.logger.debug(
                        f"Deck ID: {d_id} has been renamed from '{self.raw['decks'][d_id]['name']}' to '{deck.name}'")
                    self.raw["decks"][d_id]["name"] = deck.name
            else:
                self.logger.warning(f"Deck ID {d_id} not found in the configuration.")

    def _remove_old_decks_from_add_on_config(self):
        self.logger.debug("_remove_old_decks_from_add_on_config")
        anki_deck_ids = [str(deck.id) for deck in mw.col.decks.all_names_and_ids()]
        addon_decks = list(self.raw["decks"].keys())

        for addon_deck_id in addon_decks:
            if addon_deck_id not in anki_deck_ids:
                self.logger.debug(
                    f"Deck: {self.raw['decks'][addon_deck_id]['name']} has been removed from addon config.")
                del self.raw["decks"][addon_deck_id]

    def get_global_state(self, key: str):
        self.logger.debug(f"get_global_state key {key}")
        if key in self.raw["global"]:
            return self.raw["global"][key]
        else:
            self.logger.error(f"get_global_state error")
            return None

    def set_global_state(self, key: str, value):
        self.logger.debug(f"set_global_state key {key} value {value}")
        if key in self.raw["global"]:
            self.raw["global"][key] = value
            self._save()
        else:
            self.logger.error(f"set_global_state error")

    def get_deck_state(self, did: str, key: str):
        self.logger.debug(f"get_deck_state did {did} key {key}")
        if did in self.raw["decks"] and key in self.raw["decks"][did]:
            return self.raw["decks"][did][key]
        else:
            self.logger.error(f"get_deck_state error")
            return None

    def set_deck_state(self, did: str, key: str, value):
        self.logger.debug(f"set_deck_state did {did} key {key} value {value}")
        if did in self.raw["decks"]:
            self.raw["decks"][did][key] = value
            self._save()
        else:
            self.logger.error(f"set_deck_state error")
