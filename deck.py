from aqt import mw
from collections.abc import Sequence
import logging
from .config import DeckConfig
from time import time
from .addon_config import AddonConfig


def get_card_difficulty(card_id: int) -> float:
    query = f"SELECT json_extract(data, '$.d') FROM cards WHERE id={card_id}"
    d = mw.col.db.all(query)[0][0]
    d = (d - 1) / 9
    return d


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
        self.deck_config: DeckConfig = DeckConfig(logger=self.logger, did=self.id)
        self.update_status()

    def update_status(self) -> None:
        self._update_young_current_difficulty_sum()
        self._update_todays_user_focus_level()
        if self._get_count_still_in_queue() > 0:
            self.add_on_config.set_deck_state(did=self.id, key="status", value="REVIEW")
            self.add_on_config.set_deck_state(did=self.id, key="new_done", value=0)
            self.deck_config.set_new_count(new_count=0)
            self.logger.debug(f"[{self.name}] Cards still in review queue - no action to take.")
            return

        self._update_deck_difficulty()
        self._update_new_done_cards()

        young_current_difficulty_sum = self.add_on_config.get_deck_state(did=self.id,
                                                                         key="young_current_difficulty_sum")
        young_max_difficulty_sum = self.add_on_config.get_deck_state(did=self.id, key="young_max_difficulty_sum")
        if young_current_difficulty_sum >= young_max_difficulty_sum:
            self.add_on_config.set_deck_state(did=self.id, key="status", value="DONE")
            self.deck_config.set_new_count(new_count=0)
            return
        if get_global_count_still_in_queue() > 0:
            self.add_on_config.set_deck_state(did=self.id, key="status", value="WAIT")
            return
        self.add_on_config.set_deck_state(did=self.id, key="status", value="NEW")
        self.deck_config.set_new_count(new_count=999)

    def _update_todays_user_focus_level(self) -> None:
        cut_off_time = (mw.col.sched.day_cutoff - (60 * 60 * 24)) * 1000
        query = f"SELECT count(*), SUM(CASE WHEN revlog.ease = 1 THEN 1 ELSE 0 END) "
        query += f"FROM revlog JOIN cards ON revlog.cid = cards.id "
        query += f"WHERE revlog.id >= '{cut_off_time}' "
        query += f"AND cards.did='{self.id}';"
        result = mw.col.db.all(query)
        all_cards_count = result[0][0]
        all_again_cards_count = result[0][1]
        if all_cards_count != 0:
            todays_user_focus_level = round(1.0 - (all_again_cards_count / all_cards_count), 2)
        else:
            todays_user_focus_level = 0.90
        self.logger.debug(f"[{self.name}] Today's user focus level: {round(todays_user_focus_level * 100)}%")
        self.add_on_config.set_deck_state(did=self.id, key="todays_user_focus_level", value=todays_user_focus_level)

    def _get_young_cards_ids(self) -> Sequence:
        query = f'"deck:{self.name}" AND '
        query += f'("is:review" AND -"is:learn") AND '
        query += f'"prop:ivl<21" AND '
        query += f'-("is:buried" OR "is:suspended")'
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
            young_current_difficulty_sum += get_card_difficulty(card_id=card_id)
        young_current_difficulty_sum = round(young_current_difficulty_sum)
        self.add_on_config.set_deck_state(did=self.id, key="young_current_difficulty_sum",
                                          value=young_current_difficulty_sum)
        self.logger.debug(f"[{self.name}] Young current difficulty sum: {young_current_difficulty_sum}.")

    def _get_count_still_in_queue(self) -> int:
        query = f"deck:{self.name} is:due"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def _update_deck_difficulty(self) -> None:
        low_young_max_difficulty = self.add_on_config.get_global_state(key="lowest_young_max_difficulty_sum")
        high_young_max_difficulty = self.add_on_config.get_global_state(key="highest_young_max_difficulty_sum")
        low_focus_level = self.add_on_config.get_global_state(key="low_focus_level")
        high_focus_level = self.add_on_config.get_global_state(key="high_focus_level")
        last_updated = self.add_on_config.get_deck_state(did=self.id, key="last_updated")
        young_max_difficulty_sum = self.add_on_config.get_deck_state(did=self.id, key="young_max_difficulty_sum")
        cut_off_time = mw.col.sched.day_cutoff
        if cut_off_time - last_updated <= 60 * 60 * 24:
            logger_output = f"[{self.name}] Young max difficulty sum has been already checked today."
            logger_output += f" Next check is going to happen after {(cut_off_time - int(time())) // (60 * 60)} hours."
            self.logger.debug(logger_output)
            return

        todays_user_focus_level = self.add_on_config.get_deck_state(did=self.id, key="todays_user_focus_level")
        self.logger.info(f"[{self.name}] Today's user focus level: {round(todays_user_focus_level * 100)}%")
        if todays_user_focus_level < low_focus_level:
            young_max_difficulty_sum = max(low_young_max_difficulty, young_max_difficulty_sum - 1)
            self.add_on_config.set_deck_state(did=self.id, key="young_max_difficulty_sum",
                                              value=young_max_difficulty_sum)
            self.logger.info(f"[{self.name}] Young max difficulty sum \u2193 to {young_max_difficulty_sum}.")

        if low_focus_level <= todays_user_focus_level < high_focus_level:
            self.logger.info(f"[{self.name}] No need to \u2191\u2193 young max difficulty sum.")

        if todays_user_focus_level >= high_focus_level:
            young_max_difficulty_sum = min(high_young_max_difficulty, young_max_difficulty_sum + 1)
            self.logger.info(f"[{self.name}] Young max difficulty sum \u2191 to {young_max_difficulty_sum}.")
            self.add_on_config.set_deck_state(did=self.id, key="young_max_difficulty_sum",
                                              value=young_max_difficulty_sum)
        self.add_on_config.set_deck_state(did=self.id, key="last_updated", value=int(time()))
