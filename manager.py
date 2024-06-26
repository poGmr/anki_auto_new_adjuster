from aqt import mw
from .deck import Deck
import logging


class Manager:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger: logging.Logger = logger
        self.raw_add_on_config: dict[str, any] = mw.addonManager.getConfig(__name__)
        self.update_add_on_config()
        self.decks: dict[str, Deck] = self.get_decks()

    def __del__(self) -> None:
        mw.addonManager.writeConfig(__name__, self.raw_add_on_config)

    def update(self) -> None:
        for d_id in self.decks:
            deck = self.decks[d_id]
            deck.set_deck_difficulty()
            deck.adjust_new_cards_count()
            self.raw_add_on_config["decks"][deck.id]["young_max_difficulty"] = deck.young_difficulty_max
            self.raw_add_on_config["decks"][deck.id]["last_updated"] = deck.last_updated

    def update_add_on_config(self):
        if "decks" not in self.raw_add_on_config:
            self.raw_add_on_config["decks"] = {}

        for deck in mw.col.decks.all_names_and_ids():
            d_id = str(deck.id)
            if d_id not in self.raw_add_on_config["decks"]:
                self.raw_add_on_config["decks"][d_id] = {}
                self.raw_add_on_config["decks"][d_id]["name"] = deck.name
                self.raw_add_on_config["decks"][d_id]["enabled"] = False
                self.raw_add_on_config["decks"][d_id]["young_max_difficulty"] = 21
                self.raw_add_on_config["decks"][d_id]["last_updated"] = 0

    def get_decks(self) -> dict[str, Deck]:
        decks_dict: dict[str, Deck] = {}
        for d_id in self.raw_add_on_config["decks"]:
            if d_id in self.raw_add_on_config["decks"] and self.raw_add_on_config["decks"][d_id]["enabled"]:
                young_difficulty_max = self.raw_add_on_config["decks"][d_id]["young_max_difficulty"]
                last_updated = self.raw_add_on_config["decks"][d_id]["last_updated"]
                deck = Deck(deck_id=d_id,
                            young_difficulty_max=young_difficulty_max,
                            logger=self.logger, last_updated=last_updated)
                decks_dict[d_id] = deck
        return dict(sorted(decks_dict.items()))
