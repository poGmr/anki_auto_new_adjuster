from aqt import mw
import logging
from typing import Dict, Any
import os
import json
from collections import Counter


class AddonConfig:
    def __init__(self, logger: logging.Logger):
        self.logger: logging.Logger = logger
        self.logger.debug("__init__")
        self.raw: Dict[str, Any] = self._load()
        self._init_decks_update()

    def __exit__(self):
        self.logger.debug("__exit__")
        self._save()

    def _load(self):
        self.logger.debug("_load")
        profile_folder = mw.pm.profileFolder()
        config_path = os.path.join(profile_folder, "auto_new_adjuster_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
        else:
            config = {}
        return config

    def _save(self):
        self.logger.debug("_save")
        profile_folder = mw.pm.profileFolder()
        config_path = os.path.join(profile_folder, "auto_new_adjuster_config.json")
        with open(config_path, "w") as f:
            json.dump(self.raw, f, indent=4)

    def _init_decks_update(self):
        self.logger.debug("_init_decks_update")
        self._add_new_decks_to_add_on_config()
        self._update_decks_in_add_on_config()
        self._remove_old_decks_from_add_on_config()

    def _add_new_decks_to_add_on_config(self):
        self.logger.debug("_add_new_decks_to_add_on_config")
        if "global" not in self.raw:
            self.raw["global"] = {}
            self.raw["global"]["low_focus_level"] = 0.85
            self.raw["global"]["high_focus_level"] = 0.95
            self.raw["global"]["lowest_young_max_difficulty_sum"] = 1
            self.raw["global"]["highest_young_max_difficulty_sum"] = 210

        if "decks" not in self.raw:
            self.raw["decks"]: dict = {}

        for deck in mw.col.decks.all_names_and_ids():
            d_id = str(deck.id)
            deck_info = mw.col.decks.get(d_id)
            if deck_info['dyn'] == 1:
                # No filter decks
                continue
            if "::" in deck_info["name"]:
                # No subdecks
                continue
            if d_id not in self.raw["decks"]:
                self.raw["decks"][d_id] = {
                    "name": deck.name,
                    "enabled": False,
                    "young_max_difficulty_sum": 0,
                    "last_updated": 0,
                    "young_current_difficulty_sum": 0,
                    "new_done": 0,
                    "todays_user_focus_level": 1.0,
                    "config_id": deck_info['conf'],
                    "status": "-"
                }

    def _update_decks_in_add_on_config(self):
        self.logger.debug("_update_decks_in_add_on_config")
        for deck in mw.col.decks.all_names_and_ids():
            d_id = str(deck.id)
            deck_info = mw.col.decks.get(d_id)
            if deck_info['dyn'] == 1:
                continue
            if "::" in deck_info["name"]:
                continue
            if d_id in self.raw["decks"]:
                if self.raw["decks"][d_id]["name"] != deck.name:
                    self.logger.warning(
                        f"Deck ID: {d_id} has been renamed from '{self.raw['decks'][d_id]['name']}' to '{deck.name}'")
                    self.raw["decks"][d_id]["name"] = deck.name

                if self.raw["decks"][d_id]["config_id"] != deck_info["conf"]:
                    self.logger.warning(
                        f"Deck ID: {d_id} has been changed config from '{self.raw['decks'][d_id]['config_id']}' to '{deck_info['conf']}'")
                    self.raw["decks"][d_id]["config_id"] = deck_info["conf"]
            else:
                self.logger.warning(f"Deck ID {d_id} not found in the configuration.")

    def _remove_old_decks_from_add_on_config(self):
        self.logger.debug("_remove_old_decks_from_add_on_config")
        anki_deck_ids = [str(deck.id) for deck in mw.col.decks.all_names_and_ids()]
        addon_decks = list(self.raw["decks"].keys())

        for addon_deck_id in addon_decks:
            if addon_deck_id not in anki_deck_ids:
                self.logger.warning(
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
        else:
            self.logger.error(f"set_global_state error")

    def get_deck_state(self, did: str, key: str):
        if did in self.raw["decks"] and key in self.raw["decks"][did]:
            value = self.raw["decks"][did][key]
            self.logger.debug(f"get_deck_state did {did} key {key} value {value}")
            return value
        else:
            self.logger.error(f"get_deck_state did {did} key {key}")
            return None

    def set_deck_state(self, did: str, key: str, value):
        self.logger.debug(f"set_deck_state did {did} key {key} value {value}")
        if did in self.raw["decks"]:
            self.raw["decks"][did][key] = value
        else:
            self.logger.error(f"set_deck_state error")

    def get_decks_ids(self) -> list[str]:
        # return sorted(list(self.raw["decks"].keys()))
        # Return keys but sort then via name of the deck
        return sorted(self.raw["decks"].keys(), key=lambda deck_id: self.raw["decks"][deck_id]["name"])

    def get_duplicated_config_ids(self) -> list[str]:
        config_ids: list = []
        for did in self.raw["decks"]:
            config_ids.append(str(self.raw["decks"][did]["config_id"]))
        duplicated_config_ids = Counter(config_ids)
        duplicated_config_ids = [config_id for config_id, count in duplicated_config_ids.items() if count > 1]
        self.logger.debug(f"duplicated_config_ids {duplicated_config_ids}")
        return duplicated_config_ids
