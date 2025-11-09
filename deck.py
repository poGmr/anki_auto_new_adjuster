from aqt import mw
from collections.abc import Sequence
import logging
from .config import DeckConfig
from .addon_config import AddonConfig
from typing import Optional
import datetime
import math


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
        self._update_young_current_young_sum()
        self._update_todays_young_current_young_sum()
        if self.deck_config.id in self.add_on_config.get_duplicated_config_ids():
            self._set_error_status()
            return
        if self._get_count_still_in_queue() > 0:
            self._set_review_status()
            return
        self._update_new_done_cards()

        if not self._check_if_any_new_exist():
            self._set_no_new_status()
            return
        todays_young_current_young_sum = self.add_on_config.get_deck_state(did=self.id,
                                                                           key="todays_young_current_young_sum")
        todays_max_young_sum = self.add_on_config.get_deck_state(did=self.id,
                                                                 key="todays_young_max_young_sum")
        if todays_young_current_young_sum >= todays_max_young_sum:
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

    def _set_no_new_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="NO NEW")
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
        query += '("is:review" OR "is:learn") AND '
        query += '("prop:ivl<21" OR "introduced:1") AND '
        query += '-("is:buried" OR "is:suspended")'
        ids = mw.col.find_cards(query)
        return ids

    def _get_today_young_cards_ids(self) -> Sequence:
        query = f'"deck:{self.name}" AND '
        query += '(rated:1 OR prop:due<=0) AND '
        query += '("is:review" OR "is:learn") AND '
        query += '("prop:ivl<21" OR "introduced:1") AND '
        query += '-("is:buried" OR "is:suspended")'
        ids = mw.col.find_cards(query)
        self.logger.info(f"[{self.name}] Today's young cards count: {len(ids)}")
        for id in ids:
            self.logger.info(
                f"[{self.name}] Today's young card ID: {id}, Retrievability: {self._get_card_retrievability(id)}")
        return ids

    def _update_new_done_cards(self) -> None:
        query = f'"deck:{self.name}" AND introduced:1'
        count = len(mw.col.find_cards(query))
        self.add_on_config.set_deck_state(did=self.id, key="new_done", value=count)

    def _update_young_current_young_sum(self) -> None:
        cards_id = self._get_young_cards_ids()
        young_current_young_sum = len(cards_id)
        self.add_on_config.set_deck_state(did=self.id, key="young_current_young_sum",
                                          value=young_current_young_sum)
        self.logger.debug(f"[{self.name}] Young current difficulty sum: {young_current_young_sum}")

    def _update_todays_young_current_young_sum(self) -> None:
        cards_id = self._get_today_young_cards_ids()
        todays_young_current_young_sum = len(cards_id)
        self.add_on_config.set_deck_state(did=self.id, key="todays_young_current_young_sum",
                                          value=todays_young_current_young_sum)
        self.logger.debug(f"[{self.name}] Today's young current difficulty sum: {todays_young_current_young_sum}")

    def _get_count_still_in_queue(self) -> int:
        query = f"deck:{self.name} AND is:due"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def _check_if_any_new_exist(self) -> bool:
        query = f' deck:{self.name} "is:new" AND -("is:buried" OR "is:suspended")'
        cards_count = len(mw.col.find_cards(query))
        if cards_count > 0:
            return True
        else:
            return False

    def _get_card_retrievability(self, card_id: int) -> Optional[float]:
        """
        Calculate current retrievability (probability of recall) for a given card
        based on FSRS model parameters.

        FSRS retrievability formula:
            R = exp(-t / S)

        where:
            t = time since last review (in days)
            S = card stability (in days)

        Parameters
        ----------
        card_id : int
            The unique card ID (from col.cards.id).

        Returns
        -------
        Optional[float]
            Retrievability between 0.0 and 1.0, or None if data is unavailable.
        """
        try:
            # Step 1: Query FSRS metadata from Anki DB (available in v24+ FSRS system)
            # Custom data stored in the 'cards' table (json in 'data' field)
            card = mw.col.get_card(card_id)
            data = getattr(card, "fsrs", None)
            self.logger.info(F"[FSRS Addon] Card ID: {card_id}, FSRS data: {data}")

            # If FSRS metadata not yet available
            if not data or "stability" not in data:
                return None

            stability = float(data["stability"])
            last_review_ts = data.get("last_review", card.mod)  # fallback to modified time

            # Step 2: Compute days since last review
            last_review_date = datetime.datetime.fromtimestamp(last_review_ts)
            today = datetime.datetime.now()
            elapsed_days = (today - last_review_date).days

            # Safety guard
            if stability <= 0:
                return None

            # Step 3: Compute retrievability using FSRS decay model
            retrievability = math.exp(-elapsed_days / stability)

            # Clip to [0, 1] range just in case of rounding
            return max(0.0, min(1.0, retrievability))

        except Exception as e:
            print(f"[FSRS Addon] Failed to compute retrievability for card {card_id}: {e}")
            return None
