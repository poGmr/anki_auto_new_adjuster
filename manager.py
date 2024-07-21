from .deck import Deck
from .addon_config import AddonConfig
import logging


class Manager:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger: logging.Logger = logger
        self.add_on_config: AddonConfig = AddonConfig(logger)
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
            self.add_on_config.update_deck(d_id, deck.young_difficulty_max, deck.last_updated)

    def get_decks(self) -> dict[str, Deck]:
        decks_dict: dict[str, Deck] = {}
        for d_id in self.add_on_config.raw["decks"]:
            if self.add_on_config.raw["decks"][d_id]["enabled"]:
                young_difficulty_max = self.add_on_config.raw["decks"][d_id]["young_max_difficulty"]
                last_updated = self.add_on_config.raw["decks"][d_id]["last_updated"]
                deck = Deck(deck_id=d_id,
                            young_difficulty_max=young_difficulty_max,
                            logger=self.logger, last_updated=last_updated)
                decks_dict[d_id] = deck
        return dict(sorted(decks_dict.items()))
