from aqt import mw
from collections.abc import Sequence
import logging
from .config import DeckConfig
from time import time
from .addon_config import AddonConfig
from anki.consts import QUEUE_TYPE_REV, QUEUE_TYPE_DAY_LEARN_RELEARN


def get_card_difficulty(card_id: int) -> float:
    query = f"SELECT json_extract(data, '$.d') FROM cards WHERE id={card_id}"
    init_diff: float | None = mw.col.db.all(query)[0][0]
    if init_diff is None:
        return 0.5
    else:
        return (init_diff - 1) / 9


def get_global_count_still_in_queue() -> int:
    query = "is:due"
    cards_count = len(mw.col.find_cards(query))
    return cards_count


class Deck:
    def __init__(self, did: str, logger: logging.Logger, add_on_config: AddonConfig) -> None:
        self.logger: logging.Logger = logger
        self.add_on_config: AddonConfig = add_on_config
        self.raw_data: dict[str, str] = mw.col.decks.get(did)
        self.id: str = str(self.raw_data["id"])
        self.name: str = self.raw_data["name"]
        self.deck_config: DeckConfig = DeckConfig(logger=self.logger, did=self.id, add_on_config=add_on_config)

    def update_status(self) -> None:
        self._update_todays_difficulty_avg()
        self._update_young_current_difficulty_sum()
        if self.deck_config.id in self.add_on_config.get_duplicated_config_ids():
            self._set_error_status()
            return
        if self._get_count_still_in_queue() > 0:
            self._set_review_status()
            return

        # self._update_deck_difficulty()
        self._update_new_done_cards()

        young_current_difficulty_sum = self.add_on_config.get_deck_state(did=self.id,
                                                                         key="young_current_difficulty_sum")
        young_max_difficulty_sum = self.add_on_config.get_deck_state(did=self.id, key="young_max_difficulty_sum")
        if young_current_difficulty_sum >= young_max_difficulty_sum:
            self._set_done_status()
            return
        new_after_review_all_decks = self.add_on_config.get_global_state(key="new_after_review_all_decks")
        if new_after_review_all_decks and get_global_count_still_in_queue() > 0:
            self._set_wait_status()
            return
        self._set_new_status()

    def _set_error_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="ERROR")
        self.logger.error(f"[{self.name}] Config '{self.deck_config.name}' is used by other deck.")

    def _set_review_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="REVIEW")
        self.add_on_config.set_deck_state(did=self.id, key="new_done", value=0)
        self.deck_config.set_new_count(new_count=0)
        self.logger.debug(f"[{self.name}] Cards still in review queue - no action to take.")

    def _set_done_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="DONE")
        self.deck_config.set_new_count(new_count=0)

    def _set_wait_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="WAIT")
        self.deck_config.set_new_count(new_count=0)
        self.logger.debug(f"[{self.name}] Due cards still in review queue in other decks - no action to take.")

    def _set_new_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="NEW")
        self.deck_config.set_new_count(new_count=999)

    def _get_young_cards_ids(self) -> Sequence:
        query = f'"deck:{self.name}" AND '
        # query += f'("is:review" AND -"is:learn") AND '
        query += f'"is:review" AND '
        query += f'"prop:ivl<21" AND '
        query += f'-("is:buried" OR "is:suspended")'
        ids = mw.col.find_cards(query)
        return ids

    def _get_todays_cards_ids(self) -> Sequence:
        query = f'"deck:{self.name}" AND '
        query += f'("prop:due=0")'
        ids = mw.col.find_cards(query)
        return ids

    def _update_new_done_cards(self):
        query = f'"deck:{self.name}" AND "introduced:1"'
        count = len(mw.col.find_cards(query))
        self.add_on_config.set_deck_state(did=self.id, key="new_done", value=count)

    def _update_young_current_difficulty_sum(self) -> None:
        cards_id = self._get_young_cards_ids()
        young_current_difficulty_sum = 0.0
        for card_id in cards_id:
            young_current_difficulty_sum += get_card_difficulty(
                card_id=card_id) + 1.0  # Sum card difficulty and card count (to solve problem with 0% difficulty)
        young_current_difficulty_sum = round(young_current_difficulty_sum)
        self.add_on_config.set_deck_state(did=self.id, key="young_current_difficulty_sum",
                                          value=young_current_difficulty_sum)
        self.logger.debug(f"[{self.name}] Young current difficulty sum: {young_current_difficulty_sum}")

    def _update_todays_difficulty_avg(self) -> None:
        cards_id = self._get_todays_cards_ids()
        todays_difficulty_avg = 0.0
        n = len(cards_id)
        if n != 0:
            for card_id in cards_id:
                todays_difficulty_avg += get_card_difficulty(card_id=card_id)
            todays_difficulty_avg /= n
        self.add_on_config.set_deck_state(did=self.id, key="todays_difficulty_avg",
                                          value=todays_difficulty_avg)
        self.logger.debug(f"[{self.name}] Today difficulty avg: {round(100 * todays_difficulty_avg)}%")

    def _get_count_still_in_queue(self) -> int:
        query = f"deck:{self.name} is:due"
        cards_count = len(mw.col.find_cards(query))
        return cards_count
