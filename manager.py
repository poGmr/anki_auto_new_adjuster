from aqt import mw
from .deck import Deck
import logging


class Manager:
    def __init__(self, logger: logging) -> None:
        self.logger: logging = logger
        self.raw_add_on_config: dict[str, any] = mw.addonManager.getConfig(__name__)
        self.raw_decks: list = mw.col.decks.all()
        self.update_add_on_config()
        self.decks: set[Deck] = self.get_decks()

    def __del__(self) -> None:
        mw.addonManager.writeConfig(__name__, self.raw_add_on_config)

    def update(self) -> None:
        for deck in self.decks:
            deck.set_new_deck_difficulty()
            deck.set_new_cards_count()

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
                young_difficulty_max = self.raw_add_on_config["decks"][deck_id]["young_max_difficulty"]
                last_updated = self.raw_add_on_config["decks"][deck_id]["last_updated"]
                deck = Deck(deck_id=deck_id,
                            young_difficulty_max=young_difficulty_max,
                            logger=self.logger, last_updated=last_updated)
                decks_set.add(deck)
        return decks_set
