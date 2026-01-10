from aqt import mw
from anki.cards import CardId
from collections.abc import Sequence
import logging
from .config import DeckConfig
from .addon_config import AddonConfig

logger: logging.Logger = logging.getLogger(__name__)


def get_global_count_still_in_queue() -> int:
    query = "is:due"
    cards_count = len(mw.col.find_cards(query))
    return cards_count


class Deck:
    def __init__(self, did: str, add_on_config: AddonConfig) -> None:
        self.add_on_config: AddonConfig = add_on_config
        self.raw_data: dict[str, str] = mw.col.decks.get(did)
        self.id: str = str(self.raw_data["id"])
        self.name: str = self.raw_data["name"]
        self.deck_config: DeckConfig = DeckConfig(did=self.id, add_on_config=add_on_config)

    def update_status(self) -> None:
        self._update_nlry_sum()
        self._update_todays_nlry_sum()
        self._update_last_100_nlry_reviews_retention_rate()
        ##########################################
        if self.deck_config.id in self.add_on_config.get_duplicated_config_ids():
            self._set_error_status()
            return
        ##########################################
        if self._get_count_still_in_queue() > 0:
            self._set_review_status()
            return
        ##########################################
        self._update_new_done_cards()
        todays_nlry_sum = int(self.add_on_config.get_deck_state(did=self.id,
                                                                key="todays_nlry_sum"))
        todays_max_nlry_sum = int(self.add_on_config.get_deck_state(did=self.id,
                                                                    key="todays_nlry_max"))
        if todays_nlry_sum >= todays_max_nlry_sum:
            self._set_done_status()
            return
        ##########################################
        if not self._check_if_any_new_exist():
            self._set_no_new_status()
        ##########################################
        if self._get_status() == "NO NEW":
            all_todays_reviews_count = self._get_all_todays_reviews_count()
            if all_todays_reviews_count < todays_max_nlry_sum:
                self._set_future_status()
            return
        ##########################################
        new_after_review_all_decks = self.add_on_config.get_global_state(key="new_after_review_all_decks")
        if new_after_review_all_decks and get_global_count_still_in_queue() > 0:
            self._set_wait_status()
            return
        ##########################################
        self._set_new_status()

    def _get_status(self) -> str:
        status = self.add_on_config.get_deck_state(did=self.id, key="status")
        return status

    def _set_error_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="ERROR")
        logger.error(f"[{self.name}] Config '{self.deck_config.name}' is used by other deck.")

    def _set_review_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="REVIEW")
        self.add_on_config.set_deck_state(did=self.id, key="new_done", value=0)
        self.deck_config.set_new_count(new_count=1)
        logger.debug(f"[{self.name}] Cards still in review queue - no action to take.")

    def _set_done_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="DONE")
        self.deck_config.set_new_count(new_count=1)

    def _set_no_new_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="NO NEW")
        self.deck_config.set_new_count(new_count=1)
        logger.debug(f"[{self.name}] No new cards left in deck.")

    def _set_wait_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="WAIT")
        self.deck_config.set_new_count(new_count=1)
        logger.debug(f"[{self.name}] Due cards still in review queue in other decks - no action to take.")

    def _set_new_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="NEW")
        self.deck_config.set_new_count(new_count=999)

    def _set_future_status(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="FUTURE")
        self.deck_config.set_new_count(new_count=1)
        next_card_id: CardId = self._get_cid_next_in_nearest_due()
        if next_card_id is not None:  # "<" due to order of operations
            self._set_due_for_today(cid=next_card_id)

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
        logger.debug(f"[{self.name}] Today's nlry cards count: {len(ids)}")
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
        logger.debug(f"[{self.name}] nlry sum: {nlry_sum}")

    def _update_todays_nlry_sum(self) -> None:
        cards_id = self._get_today_nlry_cards_ids()
        todays_nlry_sum = len(cards_id)
        self.add_on_config.set_deck_state(did=self.id, key="todays_nlry_sum",
                                          value=todays_nlry_sum)
        logger.debug(f"[{self.name}] Today's nlry sum: {todays_nlry_sum}")

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

    def _get_all_todays_reviews_count(self) -> int:
        query = f'"deck:{self.name}" AND rated:1 AND -("is:buried" OR "is:suspended")'
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def _get_cid_next_in_nearest_due(self) -> CardId | None:
        query = f'"deck:{self.name}" AND prop:due>0 AND -("is:buried" OR "is:suspended" OR rated:1)'
        card_ids = mw.col.find_cards(query, order="due")
        if len(card_ids) == 0:
            logger.warning(f"[{self.name}] No cards in due>0 queue.")
            return None
        cid_next_in_nearest_due = CardId(card_ids[0])
        logger.debug(f"[{self.name}] Next card ID in nearest due queue: {cid_next_in_nearest_due}.")
        return cid_next_in_nearest_due

    def _set_due_for_today(self, cid: CardId) -> None:
        card = mw.col.get_card(cid)
        card.due = mw.col.sched.today
        card.flush()
        logger.debug(f"[{self.name}] Card ID {cid} due date set to today.")

    def _update_last_100_nlry_reviews_retention_rate(self) -> None:
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
            logger.warning(
                f"[{self.name}] Not enough reviews to calculate retention rate (only {len(rows)} reviews).")
            self.add_on_config.set_deck_state(did=self.id, key="last_100_nlry_reviews_retention",
                                              value=0.0)
        correct = sum(1 for (ease,) in rows if ease > 1)
        retention = correct / len(rows)
        self.add_on_config.set_deck_state(did=self.id, key="last_100_nlry_reviews_retention",
                                          value=retention)
        logger.debug(
            f"[{self.name}] Retention rate for last 100 reviews: {retention:.0%}")
