from .deck import Deck
from .addon_config import AddonConfig
import logging


class Manager:
    def __init__(self, logger: logging.Logger, add_on_config: AddonConfig) -> None:
        self.logger: logging.Logger = logger
        self.add_on_config: AddonConfig = add_on_config

    def update_all(self) -> None:
        for did in self.add_on_config.raw["decks"]:
            deck = Deck(did=did, logger=self.logger, add_on_config=self.add_on_config)
            if self.add_on_config.raw["decks"][did]["enabled"]:
                if deck.get_count_still_in_queue() > 0:
                    deck.deck_config.set_new_count(new_count=0)
                    self.logger.debug(f"[{deck.name}] Cards still in queue - no action to take.")
                    continue
                deck.set_deck_difficulty()
                deck.set_new_cards_count()
