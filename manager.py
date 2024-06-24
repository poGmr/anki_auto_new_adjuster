from aqt import mw
from .deck import Deck
from .config import Config
import logging
from time import time


class Manager:
    def __init__(self, logger: logging) -> None:
        self.logger: logging = logger
        self.raw_add_on_config: dict[str, any] = mw.addonManager.getConfig(__name__)
        self.raw_decks: list = mw.col.decks.all()
        self.raw_configs: list = mw.col.decks.all_config()
        self.update_add_on_config()
        self.decks: set[Deck] = self.get_decks()
        self.configs: set[Config] = self.get_configs()
        self.low_young_difficulty_max = 50
        self.high_young_difficulty_max = 150

    def __del__(self) -> None:
        mw.addonManager.writeConfig(__name__, self.raw_add_on_config)

    def update(self) -> None:
        for deck in self.decks:
            for config in self.configs:
                if config.id == deck.configID:
                    self.set_new_cards_count(deck=deck, deck_config=config)
                    break

    def update_add_on_config(self):
        if "decks" not in self.raw_add_on_config:
            self.raw_add_on_config["decks"] = {}

        for raw_deck in self.raw_decks:
            deck_id: str = str(raw_deck["id"])
            if deck_id not in self.raw_add_on_config["decks"]:
                self.raw_add_on_config["decks"][deck_id] = {}
                self.raw_add_on_config["decks"][deck_id]["name"] = raw_deck["name"]
                self.raw_add_on_config["decks"][deck_id]["enabled"] = False
                self.raw_add_on_config["decks"][deck_id]["young_max_difficulty"] = 21
                self.raw_add_on_config["decks"][deck_id]["last_updated"] = 0

    def get_decks(self) -> set[Deck]:
        decks_set: set[Deck] = set()
        for raw_deck in self.raw_decks:
            deck_id: str = str(raw_deck["id"])
            if deck_id in self.raw_add_on_config["decks"] and self.raw_add_on_config["decks"][deck_id]["enabled"]:
                deck = Deck(deck_id=deck_id,
                            young_difficulty_max=self.raw_add_on_config["decks"][deck_id]["young_max_difficulty"],
                            logger=self.logger)
                decks_set.add(deck)
        return decks_set

    def get_configs(self) -> set[Config]:
        config_set: set[Config] = set()
        for raw_config in self.raw_configs:
            if raw_config["id"] != 1:
                config = Config(raw_config, self.logger)
                config_set.add(config)
        return config_set

    def set_new_deck_difficulty(self, deck: Deck):
        # self.logger.debug(f"[{deck.name}] young_max_difficulty: {deck.young_max_difficulty}")
        if time() - self.raw_add_on_config["decks"][deck.id]["last_updated"] <= 20 * 60 * 60:
            # self.logger.debug(f"[{deck.name}] Updated in last 20h - no action is needed.")
            return
        current_value = self.raw_add_on_config["decks"][deck.id]["young_max_difficulty"]
        todays_again_hit = deck.get_todays_again_hit()
        debug_message: str = f"[{deck.name}] Today again hit: {round(todays_again_hit * 100)}% | "
        debug_message += f"current young_difficulty_max: {current_value} | "
        if todays_again_hit >= 0.95:
            current_value = min(self.high_young_difficulty_max, current_value + 1)
        if todays_again_hit < 0.85:
            current_value = max(self.low_young_difficulty_max, current_value - 1)
        debug_message += f"new young_difficulty_max: {current_value}"
        self.logger.debug(debug_message)
        self.raw_add_on_config["decks"][deck.id]["last_updated"] = int(time())
        self.raw_add_on_config["decks"][deck.id]["young_max_difficulty"] = current_value
        deck.young_difficulty_max = current_value
        # self.logger.debug(f"[{deck.name}] New young_max_difficulty: {deck.young_max_difficulty}")

    def set_new_cards_count(self, deck: Deck, deck_config: Config):
        deck_young_difficulty_sum: int = round(deck.get_deck_young_difficulty_sum())
        deck_count_cards_introduced_today: int = deck.get_count_cards_introduced_today()
        deck_new_config_limit: int = 0
        if deck.get_count_still_in_queue() == 0:
            self.set_new_deck_difficulty(deck)
            deck_new_config_limit = max(0,
                                        deck.young_difficulty_max - deck_young_difficulty_sum + deck_count_cards_introduced_today)

        deck_config.set_new_count(new_count=deck_new_config_limit)

        debug_message: str = f"[{deck_config.name}][{deck.name}] "
        debug_message += f"deck_young_difficulty_max {deck.young_difficulty_max} | "
        debug_message += f"deck_young_difficulty_sum {deck_young_difficulty_sum} | "
        debug_message += f"deck_count_cards_introduced_today {deck_count_cards_introduced_today}"
        self.logger.debug(debug_message)
