from aqt import mw
from .deck import Deck
from .config import Config
import logging


class Manager:
    def __init__(self, logger: logging) -> None:
        self.add_on_config: dict[str, any] = mw.addonManager.getConfig(__name__)
        self.logger: logging = logger
        self.decks: set[Deck] = self.get_decks()
        self.configs: set[Config] = self.get_configs()

    def __del__(self) -> None:
        mw.addonManager.writeConfig(__name__, self.add_on_config)

    def update(self) -> None:
        post_diff_sum: int = 0
        for deck in self.decks:
            for config in self.configs:
                if config.id == deck.configID:
                    self.set_new_cards_count(deck=deck, deck_config=config)
                    post_diff_sum += deck.get_todays_post_difficulty_sum()
                    break
        self.logger.debug(f"Today's sum of difficulty: {post_diff_sum}")

    def get_decks(self) -> set[Deck]:
        decks_set: set[Deck] = set()
        raw_decks = mw.col.decks.get_all_legacy()
        allowed_decks: dict[str, str] = self.add_on_config["includedDecks"]
        for rawDeck in raw_decks:
            if rawDeck["name"] in allowed_decks:
                deck = Deck(raw_data=rawDeck, new_limit=int(allowed_decks[rawDeck["name"]]))
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

    def set_new_cards_count(self, deck: Deck, deck_config: Config):
        young_deck_difficulty_sum: int = round(deck.get_all_young_deck_difficulty_sum())
        deck_get_count_cards_introduced_today: int = deck.get_count_cards_introduced_today()
        deck_new_limit: int = deck.newLimit
        deck_new_config_limit: int = max(0,
                                         deck_new_limit - young_deck_difficulty_sum + deck_get_count_cards_introduced_today)
        deck_get_count_still_in_queue: int = deck.get_count_still_in_queue()
        debug_message: str = f"[{deck_config.name}][{deck.name}] "
        debug_message += f"deck_newLimit {deck_new_limit} | "
        debug_message += f"young_deck_difficulty_sum {young_deck_difficulty_sum} | "
        debug_message += f"deck_get_count_cards_introduced_today {deck_get_count_cards_introduced_today} | "
        debug_message += f"deck_new_config_limit {deck_new_config_limit} | "
        debug_message += f"deck.get_todays_post_difficulty_sum(): {round(deck.get_todays_post_difficulty_sum())}"
        self.logger.debug(debug_message)
        if deck_get_count_still_in_queue == 0:
            deck_config.set_new_count(new_count=deck_new_config_limit)
        else:
            deck_config.set_new_count(new_count=0)
