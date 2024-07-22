import json

from aqt import mw
import logging
from typing import Dict, Any


class AddonConfig:
    def __init__(self, logger: logging.Logger):
        self.logger: logging.Logger = logger
        self.raw: Dict[str, Any] = mw.addonManager.getConfig(__name__)
        self._add_new_decks_to_add_on_config()
        self._update_decks_in_add_on_config()
        self._remove_old_decks_from_add_on_config()
        self._save()
        self.logger.debug(f"Addon config loaded and updated: {json.dumps(self.raw, indent=4)}")

    def __del__(self):
        self._save()

    def _save(self):
        mw.addonManager.writeConfig(__name__, self.raw)
        self.logger.debug(f"Addon config saved.")

    def _add_new_decks_to_add_on_config(self):
        if "decks" not in self.raw:
            self.raw["decks"] = {}

        for deck in mw.col.decks.all_names_and_ids():
            d_id = str(deck.id)
            if d_id not in self.raw["decks"]:
                self.raw["decks"][d_id] = {
                    "name": deck.name,
                    "enabled": False,
                    "young_max_difficulty": 21,
                    "last_updated": 0
                }

    def _update_decks_in_add_on_config(self):
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
        anki_deck_ids = [str(deck.id) for deck in mw.col.decks.all_names_and_ids()]
        addon_decks = list(self.raw["decks"].keys())

        for addon_deck_id in addon_decks:
            if addon_deck_id not in anki_deck_ids:
                self.logger.debug(
                    f"Deck: {self.raw['decks'][addon_deck_id]['name']} has been removed from addon config.")
                del self.raw["decks"][addon_deck_id]

    def update_deck(self, ids: str, young_difficulty_max: int, last_updated: int):
        if ids in self.raw["decks"]:
            self.raw["decks"][ids]["young_max_difficulty"] = young_difficulty_max
            self.raw["decks"][ids]["last_updated"] = last_updated
            self._save()
            self.logger.debug(
                f"Addon config updated deck id: {ids} with ydm: {young_difficulty_max} and lu: {last_updated}")
        else:
            self.logger.error(f"Deck ID {ids} not found in the configuration.")

    def set_enable_deck_state(self, did: str, state: bool):
        if did in self.raw["decks"]:
            self.raw["decks"][did]["enabled"] = state
            self._save()
        else:
            self.logger.error(f"set_enable_deck_state error")
