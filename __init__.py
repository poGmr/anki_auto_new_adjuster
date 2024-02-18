from aqt import gui_hooks
import logging
from aqt import mw
import json
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s [%(filename)s][%(funcName)s:%(lineno)s][%(levelname)s]: %(message)s"
logFilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "auto_new_adjuster.log")
file_handler = RotatingFileHandler(logFilePath, maxBytes=1e6, backupCount=3)
formatter = logging.Formatter(FORMAT)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


class Deck:
    def __init__(self, raw_data, new_limit) -> None:
        self.rawData = raw_data
        self.newLimit = new_limit
        self.id = ""
        self.name = ""
        self.configID = ""
        self.update()

    def update(self):
        self.id = self.rawData["id"]
        self.name = self.rawData["name"]
        self.configID = self.rawData["conf"]

    def get_pretty_config_data(self):
        return json.dumps(self.rawData, indent=4)

    def get_count_cards_count_done_today(self):
        query = f"deck:{self.name} rated:1"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def get_count_still_in_queue(self):
        query = f"deck:{self.name} is:due"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def get_young_count(self):
        query = f'"deck:{self.name}" AND '
        query += f'("is:review" AND -"is:learn") AND '
        query += f'"prop:ivl<21" AND '
        query += f'-("is:buried" OR "is:suspended")'
        cards_count = len(mw.col.find_cards(query))
        return cards_count


class Config:
    def __init__(self, raw_data) -> None:
        self.rawData = raw_data
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
            logger.info(f"[{self.name}] value {new_count} of new cards per day has been saved to the configuration.")
            self.update()


class Manager:
    def __init__(self) -> None:
        self.add_on_config = mw.addonManager.getConfig(__name__)
        self.decks = []
        self.configs = []

    def __del__(self):
        mw.addonManager.writeConfig(__name__, self.add_on_config)

    def update(self):
        self.decks: list[Deck] = self.get_decks()
        self.configs = self.get_configs()

        for deck in self.decks:
            for config in self.configs:
                if config.id == deck.configID:
                    self.set_new_cards_count(deck=deck, deck_config=config)
                    break

    def get_decks(self):
        decks_list = []
        raw_decks = mw.col.decks.get_all_legacy()
        allowed_decks = self.add_on_config["includedDecks"]
        for rawDeck in raw_decks:
            if rawDeck["name"] in allowed_decks:
                deck = Deck(raw_data=rawDeck, new_limit=allowed_decks[rawDeck["name"]])
                decks_list.append(deck)
        return decks_list

    @staticmethod
    def get_configs():
        config_list = []
        raw_configs = mw.col.decks.all_config()
        for rawConfig in raw_configs:
            if rawConfig["id"] != 1:
                config = Config(raw_data=rawConfig)
                config_list.append(config)
        return config_list

    @staticmethod
    def set_new_cards_count(deck: Deck, deck_config: Config):
        deck_young_count = deck.get_young_count()
        deck_new_limit = max(1, deck.newLimit - deck_young_count)
        deck_get_count_still_in_queue = deck.get_count_still_in_queue()
        debug_message = f"[{deck_config.name}][{deck.name}] "
        debug_message += f"deck.newLimit {deck.newLimit} | "
        debug_message += f"deck_young_count {deck_young_count} | "
        debug_message += f"deck_new_limit {deck_new_limit}"
        logger.debug(debug_message)
        if deck_get_count_still_in_queue == 0:
            deck_config.set_new_count(new_count=deck_new_limit)
        else:
            deck_config.set_new_count(new_count=0)


def sync_did_finish():
    logger.info("#")
    logger.info("####################################################################################")
    logger.info("#")
    manager: Manager = Manager()
    manager.update()


gui_hooks.sync_did_finish.append(sync_did_finish)
