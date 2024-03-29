from aqt import mw
from .deck import Deck
from .config import Config


class Manager:
    def __init__(self, logger) -> None:
        self.add_on_config = mw.addonManager.getConfig(__name__)
        self.logger = logger
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

    def get_configs(self):
        config_list = []
        raw_configs = mw.col.decks.all_config()
        for rawConfig in raw_configs:
            if rawConfig["id"] != 1:
                config = Config(rawConfig, self.logger)
                config_list.append(config)
        return config_list

    def set_new_cards_count(self, deck: Deck, deck_config: Config):
        deck_hard_young_count = deck.get_hard_young_count()
        deck_get_count_cards_introduced_today = deck.get_count_cards_introduced_today()
        deck_new_limit = max(1, deck.newLimit + deck_get_count_cards_introduced_today - deck_hard_young_count)
        deck_get_count_still_in_queue = deck.get_count_still_in_queue()
        debug_message = f"[{deck_config.name}][{deck.name}] "
        debug_message += f"newLimit {deck.newLimit} | "
        debug_message += f"hard_young_count {deck_hard_young_count} | "
        debug_message += f"new_limit {deck_new_limit} | "
        debug_message += f"get_count_cards_introduced_today {deck_get_count_cards_introduced_today}"
        self.logger.debug(debug_message)
        if deck_get_count_still_in_queue == 0:
            deck_config.set_new_count(new_count=deck_new_limit)
        else:
            deck_config.set_new_count(new_count=0)
