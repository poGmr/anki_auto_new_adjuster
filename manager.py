from aqt import mw
from .deck import Deck
from .config import Config
import logging
from time import time


class Manager:
    def __init__(self, logger: logging) -> None:
        self.add_on_config: dict[str, any] = mw.addonManager.getConfig(__name__)
        self.logger: logging = logger
        self.decks: set[Deck] = self.get_decks()
        self.configs: set[Config] = self.get_configs()
        self.low_young_difficulty_max = 50
        self.high_young_difficulty_max = 150
        self.update_add_on_config()

    def __del__(self) -> None:
        mw.addonManager.writeConfig(__name__, self.add_on_config)

    def update(self) -> None:
        for deck in self.decks:
            for config in self.configs:
                if config.id == deck.configID:
                    self.set_new_cards_count(deck=deck, deck_config=config)
                    break

    def update_add_on_config(self):
        if "decks" not in self.add_on_config:
            self.add_on_config["decks"] = {}

        for deck in mw.col.decks.get_all_legacy():
            deck_name = deck["name"]
            if deck_name not in self.add_on_config["decks"]:
                self.add_on_config["decks"][deck_name] = {}
                self.add_on_config["decks"][deck_name]["enabled"] = False
                self.add_on_config["decks"][deck_name]["young_max_difficulty"] = 21
                self.add_on_config["decks"][deck_name]["last_updated"] = 0

    def get_decks(self) -> set[Deck]:
        decks_set: set[Deck] = set()
        raw_decks = mw.col.decks.get_all_legacy()
        for rawDeck in raw_decks:
            deck_name = rawDeck["name"]
            if deck_name in self.add_on_config["decks"] and self.add_on_config["decks"][deck_name]["enabled"]:
                deck = Deck(raw_data=rawDeck,
                            young_difficulty_max=self.add_on_config["decks"][deck_name]["young_max_difficulty"],
                            logger=self.logger)
                decks_set.add(deck)
        return decks_set

    def get_configs(self) -> set[Config]:
        config_set: set[Config] = set()
        raw_configs = mw.col.decks.all_config()
        for rawConfig in raw_configs:
            if rawConfig["id"] != 1:
                config = Config(rawConfig, self.logger)
                config_set.add(config)
        return config_set

    def set_new_deck_difficulty(self, deck: Deck):
        # self.logger.debug(f"[{deck.name}] young_max_difficulty: {deck.young_max_difficulty}")
        if time() - self.add_on_config["decks"][deck.name]["last_updated"] <= 20 * 60 * 60:
            # self.logger.debug(f"[{deck.name}] Updated in last 20h - no action is needed.")
            return
        current_value = self.add_on_config["decks"][deck.name]["young_max_difficulty"]
        todays_again_hit = deck.get_todays_again_hit()
        debug_message: str = f"[{deck.name}] Today again hit: {round(todays_again_hit * 100)}% | "
        debug_message += f"current young_difficulty_max: {current_value} | "
        if todays_again_hit >= 0.95:
            current_value = min(self.high_young_difficulty_max, current_value + 1)
        if todays_again_hit < 0.85:
            current_value = max(self.low_young_difficulty_max, current_value - 1)
        debug_message += f"new young_difficulty_max: {current_value}"
        self.logger.debug(debug_message)
        self.add_on_config["decks"][deck.name]["last_updated"] = int(time())
        self.add_on_config["decks"][deck.name]["young_max_difficulty"] = current_value
        deck.young_difficulty_max = current_value
        # self.logger.debug(f"[{deck.name}] New young_max_difficulty: {deck.young_max_difficulty}")

    def set_new_cards_count(self, deck: Deck, deck_config: Config):
        deck_young_difficulty_sum: int = round(deck.get_deck_young_difficulty_sum())
        deck_count_cards_introduced_today: int = deck.get_count_cards_introduced_today()

        deck_get_count_still_in_queue: int = deck.get_count_still_in_queue()
        deck_new_config_limit: int = 0
        if deck_get_count_still_in_queue == 0:
            self.set_new_deck_difficulty(deck)
            deck_new_config_limit: int = max(0,
                                             deck.young_difficulty_max - deck_young_difficulty_sum + deck_count_cards_introduced_today)

        deck_config.set_new_count(new_count=deck_new_config_limit)

        debug_message: str = f"[{deck_config.name}][{deck.name}] "
        debug_message += f"deck_young_difficulty_max {deck.young_difficulty_max} | "
        debug_message += f"deck_young_difficulty_sum {deck_young_difficulty_sum} | "
        debug_message += f"deck_count_cards_introduced_today {deck_count_cards_introduced_today}"
        self.logger.debug(debug_message)
