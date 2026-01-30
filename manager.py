import logging
from .addon_config import AddonConfig
from .deck import Deck
from aqt import mw

logger: logging.Logger = logging.getLogger(__name__)


def get_global_count_still_in_queue() -> int:
    query = "is:due"
    cards_count = len(mw.col.find_cards(query))
    return cards_count


class Manager:
    def __init__(self, add_on_config: AddonConfig):
        self.add_on_config: AddonConfig = add_on_config

    def update_all_decks(self) -> None:
        for did in self.add_on_config.raw["decks"]:
            if self.add_on_config.get_deck_state(did=did, key="enabled"):
                self.update_deck(did=did)

    def update_deck(self, did: str) -> None:
        deck = Deck(did=did, add_on_config=self.add_on_config)
        deck.update_status()
        if deck.deck_config.id in self.add_on_config.get_duplicated_config_ids():
            deck.set_status_error()
            return
        ##########################################
        if deck.get_count_still_in_queue() > 0:
            deck.set_status_min_review()
            return
        ##########################################
        todays_workload = int(self.add_on_config.get_deck_state(did=deck.id,
                                                                key="todays_workload"))
        todays_max_workload = int(self.add_on_config.get_deck_state(did=deck.id,
                                                                    key="todays_max_workload"))
        if todays_workload >= todays_max_workload:
            deck.set_status_done()
            return
        ##########################################
        new_after_review_all_decks = self.add_on_config.get_global_state(key="new_after_review_all_decks")
        if new_after_review_all_decks and get_global_count_still_in_queue() > 0:
            deck.set_status_wait()
            return
        ##########################################
        if deck.check_if_any_new_exist():
            deck.set_status_new()
        else:
            cards_to_shift_count = todays_max_workload - todays_workload
            deck.set_status_future(n_to_shift=cards_to_shift_count)

    def get_all_statuses(self) -> list:
        statuses: list = []
        for did in self.add_on_config.raw["decks"]:
            status = self.add_on_config.get_deck_state(did=did, key="status")
            statuses.append(status)
        return statuses
