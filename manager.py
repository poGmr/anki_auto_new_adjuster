from .deck import Deck
from .addon_config import AddonConfig
import logging


class Manager:
    def __init__(self, logger: logging.Logger, add_on_config: AddonConfig) -> None:
        self.logger: logging.Logger = logger
        self.add_on_config: AddonConfig = add_on_config

    def update_all_decks(self) -> None:
        for did in self.add_on_config.raw["decks"]:
            self.update_deck(did=did)

    def update_deck(self, did: str) -> None:
        if self.add_on_config.get_deck_state(did=did, key="enabled"):
            deck = Deck(did=did, logger=self.logger, add_on_config=self.add_on_config)
            self.add_on_config.set_deck_state(did=did, key="young_current_difficulty_sum",
                                              value=deck.get_young_current_difficulty_sum())
