from aqt import mw
from anki.cards import CardId
from collections.abc import Sequence
import logging
from .config import DeckConfig
from .addon_config import AddonConfig

logger: logging.Logger = logging.getLogger(__name__)


class Deck:
    def __init__(self, did: str, add_on_config: AddonConfig) -> None:
        self.add_on_config: AddonConfig = add_on_config
        self.raw_data: dict[str, str] = mw.col.decks.get(did)
        self.id: str = str(self.raw_data["id"])
        self.name: str = self.raw_data["name"]
        self.deck_config: DeckConfig = DeckConfig(did=self.id, add_on_config=add_on_config)

    def update_status(self) -> None:
        self._update_all_todays_cards_count()
        self._update_last_100_reviews_retention_rate()
        self._update_new_done_cards()

    def _get_status(self) -> str:
        status = self.add_on_config.get_deck_state(did=self.id, key="status")
        return status

    def set_status_error(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="ERROR")
        logger.error(f"[{self.name}] Config '{self.deck_config.name}' is used by other deck.")

    def set_status_min_review(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="MIN REVIEW")
        self.add_on_config.set_deck_state(did=self.id, key="new_done", value=0)
        self.deck_config.set_new_count(new_count=1)
        logger.debug(f"[{self.name}] Cards still in review queue - no action to take.")

    def set_status_done(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="DONE")
        self.deck_config.set_new_count(new_count=1)

    def set_status_wait(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="WAIT")
        self.deck_config.set_new_count(new_count=1)
        logger.debug(f"[{self.name}] Due cards still in review queue in other decks - no action to take.")

    def set_status_new(self) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="NEW")
        self.deck_config.set_new_count(new_count=999)

    def set_status_future(self, n_to_shift: int = 1) -> None:
        self.add_on_config.set_deck_state(did=self.id, key="status", value="FUTURE")
        self.deck_config.set_new_count(new_count=1)
        for _ in range(n_to_shift):
            next_card_id: CardId = self._get_cid_next_in_nearest_due()
            if next_card_id is None:
                break
            self._set_due_for_today(cid=next_card_id)

    def _update_new_done_cards(self) -> None:
        query = f'"deck:{self.name}" AND introduced:1'
        count = len(mw.col.find_cards(query))
        self.add_on_config.set_deck_state(did=self.id, key="new_done", value=count)

    def get_count_still_in_queue(self) -> int:
        query = f"deck:{self.name} AND is:due"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def check_if_any_new_exist(self) -> bool:
        query = f' deck:{self.name} "is:new" AND -("is:buried" OR "is:suspended")'
        cards_count = len(mw.col.find_cards(query))
        if cards_count > 0:
            return True
        else:
            return False

    def _update_all_todays_cards_count(self) -> None:
        query = f'"deck:{self.name}" AND (rated:1 OR is:due) AND -("is:buried" OR "is:suspended")'
        cards_count = len(mw.col.find_cards(query))
        self.add_on_config.set_deck_state(did=self.id, key="todays_workload", value=cards_count)

    def _get_cid_next_in_nearest_due(self) -> CardId | None:
        query = f'"deck:{self.name}" AND prop:due>0 AND -("is:buried" OR "is:suspended" OR rated:1)'
        card_ids = mw.col.find_cards(query, order="reps asc")
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

    def _update_last_100_reviews_retention_rate(self) -> None:
        query = """
                SELECT revlog.ease
                FROM revlog
                         JOIN cards ON revlog.cid = cards.id
                WHERE cards.did = ?
                  AND revlog.type = 1
                ORDER BY revlog.id DESC LIMIT 100
                """

        rows = mw.col.db.all(query, self.id)

        if len(rows) < 100:
            logger.warning(
                f"[{self.name}] Not enough reviews to calculate retention rate (only {len(rows)} reviews).")
            self.add_on_config.set_deck_state(did=self.id, key="last_100_reviews_retention",
                                              value=0.0)
            return
        correct = sum(1 for (ease,) in rows if ease > 1)
        retention = correct / len(rows)
        self.add_on_config.set_deck_state(did=self.id, key="last_100_reviews_retention",
                                          value=retention)
        logger.debug(
            f"[{self.name}] Retention rate for last 100 reviews: {retention:.0%}")
