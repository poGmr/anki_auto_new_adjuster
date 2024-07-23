from .deck import Deck
from .addon_config import AddonConfig
import logging


class Manager:
    def __init__(self, logger: logging.Logger, add_on_config: AddonConfig) -> None:
        self.logger: logging.Logger = logger
        self.add_on_config: AddonConfig = add_on_config
        self.decks: dict[str, Deck] = self.get_decks()

    def update(self) -> None:
        for d_id in self.decks:
            deck = self.decks[d_id]
            if deck._get_count_still_in_queue() > 0:
                deck.deck_config.set_new_count(new_count=0)
                self.logger.debug(f"[{deck.name}] Cards still in queue - no action to take.")
                continue
            deck.set_deck_difficulty()
            deck.set_new_cards_count()

    def get_decks(self) -> dict[str, Deck]:
        decks_dict: dict[str, Deck] = {}
        for d_id in self.add_on_config.raw["decks"]:
            if self.add_on_config.raw["decks"][d_id]["enabled"]:
                deck = Deck(deck_id=d_id, logger=self.logger)
                decks_dict[d_id] = deck
        return dict(sorted(decks_dict.items()))
