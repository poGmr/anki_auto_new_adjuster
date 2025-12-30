from aqt import mw
from collections.abc import Sequence
import logging
from .config import DeckConfig
from .addon_config import AddonConfig


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
        self._update_nlry_sum()
        self._update_todays_nlry_sum()
        self._update_last_100_nlry_reviews_retention_rate()
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
        todays_nlry_sum = self.add_on_config.get_deck_state(did=self.id,
                                                            key="todays_nlry_sum")
        todays_max_nlry_sum = self.add_on_config.get_deck_state(did=self.id,
                                                                key="todays_nlry_max")
        if todays_nlry_sum >= todays_max_nlry_sum:
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
        self.deck_config.set_new_count(new_count=1)
        self.logger.debug(f"[{self.name}] Cards still in review queue - no action to take.")

    def _set_done_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="DONE")
        self.deck_config.set_new_count(new_count=1)

    def _set_no_new_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="NO NEW")
        self.deck_config.set_new_count(new_count=1)

    def _set_wait_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="WAIT")
        self.deck_config.set_new_count(new_count=1)
        self.logger.debug(f"[{self.name}] Due cards still in review queue in other decks - no action to take.")

    def _set_new_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="NEW")
        self.deck_config.set_new_count(new_count=999)

    def _get_nlry_cards_ids(self) -> Sequence:
        query = f'"deck:{self.name}" AND '
        query += '("is:review" OR "is:learn") AND '
        query += '("prop:ivl<21" OR "introduced:1") AND '
        query += '-("is:buried" OR "is:suspended")'
        ids = mw.col.find_cards(query)
        return ids

    def _get_today_nlry_cards_ids(self) -> Sequence:
        query = f'"deck:{self.name}" AND '
        query += '(rated:1 OR prop:due<=0) AND '
        query += '("is:review" OR "is:learn") AND '
        query += '("prop:ivl<21" OR "introduced:1") AND '
        query += '-("is:buried" OR "is:suspended")'
        ids = mw.col.find_cards(query)
        self.logger.debug(f"[{self.name}] Today's nlry cards count: {len(ids)}")
        return ids

    def _update_new_done_cards(self) -> None:
        query = f'"deck:{self.name}" AND introduced:1'
        count = len(mw.col.find_cards(query))
        self.add_on_config.set_deck_state(did=self.id, key="new_done", value=count)

    def _update_nlry_sum(self) -> None:
        cards_id = self._get_nlry_cards_ids()
        nlry_sum = len(cards_id)
        self.add_on_config.set_deck_state(did=self.id, key="nlry_sum",
                                          value=nlry_sum)
        self.logger.debug(f"[{self.name}] nlry sum: {nlry_sum}")

    def _update_todays_nlry_sum(self) -> None:
        cards_id = self._get_today_nlry_cards_ids()
        todays_nlry_sum = len(cards_id)
        self.add_on_config.set_deck_state(did=self.id, key="todays_nlry_sum",
                                          value=todays_nlry_sum)
        self.logger.debug(f"[{self.name}] Today's nlry sum: {todays_nlry_sum}")

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

    def _update_last_100_nlry_reviews_retention_rate(self) -> float:
        query = """
                SELECT revlog.ease
                FROM revlog
                         JOIN cards ON revlog.cid = cards.id
                WHERE cards.did = ?
                  AND revlog.lastIvl < 21
                  AND revlog.type = 1
                ORDER BY revlog.id DESC LIMIT 100
                """

        rows = mw.col.db.all(query, self.id)

        if len(rows) < 100:
            self.logger.warning(
                f"[{self.name}] Not enough reviews to calculate retention rate (only {len(rows)} reviews).")
            return 0.0
        correct = sum(1 for (ease,) in rows if ease > 1)
        retention = correct / len(rows)
        self.add_on_config.set_deck_state(did=self.id, key="last_100_nlry_reviews_retention",
                                          value=retention)
        self.logger.debug(
            f"[{self.name}] Retention rate for last 100 reviews: {retention:.0%}")
