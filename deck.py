from aqt import mw
from collections.abc import Sequence
import logging
from .config import DeckConfig
from time import time


class Deck:
    def __init__(self, deck_id: str, young_difficulty_max: int, logger: logging, last_updated: int) -> None:
        self.logger: logging = logger
        self.raw_data: dict[str, str] = mw.col.decks.get(deck_id)
        self.young_difficulty_max: int = young_difficulty_max
        self.last_updated = last_updated
        self.id: str = str(self.raw_data["id"])
        self.name = self.raw_data["name"]
        self.deck_config: DeckConfig = DeckConfig(logger=self.logger, deck_id=self.id)

    def get_count_cards_introduced_today(self) -> int:
        query = f"deck:{self.name} introduced:1"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def get_count_still_in_queue(self) -> int:
        query = f"deck:{self.name} is:due"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def get_ids_young_cards(self) -> Sequence:
        query = f'"deck:{self.name}" AND '
        query += f'("is:review" AND -"is:learn") AND '
        query += f'"prop:ivl<21" AND '
        query += f'-("is:buried" OR "is:suspended")'
        ids = mw.col.find_cards(query)
        return ids

    def get_card_difficulty(self, card_id: int) -> float:
        query = f"SELECT json_extract(data, '$.d') FROM cards WHERE id={card_id}"
        d = mw.col.db.all(query)[0][0]
        d = (d - 1) / 9
        return d

    def get_deck_young_difficulty_sum(self) -> int:
        cards_id = self.get_ids_young_cards()
        difficulty_sum = 0.0
        for card_id in cards_id:
            difficulty_sum += self.get_card_difficulty(card_id=card_id)
        return round(difficulty_sum)

    def get_todays_again_hit(self):
        query = f"deck:{self.name} AND rated:1"
        all_cards_count = len(mw.col.find_cards(query))
        query = f"deck:{self.name} AND rated:1:1"
        all_again_cards_count = len(mw.col.find_cards(query))
        if all_cards_count != 0:
            return round(1.0 - (all_again_cards_count / all_cards_count), 2)
        else:
            return 0.9

    def adjust_new_cards_count(self):
        if self.get_count_still_in_queue() > 0:
            self.deck_config.set_new_count(new_count=0)
            self.logger.debug(f"[{self.name}] Cards still in queue - no new cards allowed.")
            return

        deck_new_config_limit = self.young_difficulty_max - self.get_deck_young_difficulty_sum() + self.get_count_cards_introduced_today()
        deck_new_config_limit = max(0, deck_new_config_limit)
        self.deck_config.set_new_count(new_count=deck_new_config_limit)

    def set_deck_difficulty(self):
        low_young_difficulty_max = 21
        high_young_difficulty_max = 210
        AGAIN_LOW_FACTOR = 0.85
        AGAIN_HIGH_FACTOR = 0.95

        if time() - self.last_updated <= 20 * 60 * 60:
            self.logger.debug(f"[{self.name}] Deck difficulty has been changed in less than 20h.")
            return
        todays_again_hit = self.get_todays_again_hit()

        if AGAIN_LOW_FACTOR < todays_again_hit <= AGAIN_HIGH_FACTOR:
            self.logger.debug(
                f"[{self.name}] Today's again hit: {todays_again_hit}. No need to adjust deck difficulty.")
            return

        if todays_again_hit >= AGAIN_HIGH_FACTOR:
            self.young_difficulty_max = min(high_young_difficulty_max, self.young_difficulty_max + 1)
            self.logger.info(
                f"[{self.name}] Today's again hit: {todays_again_hit}. Difficulty increased to {self.young_difficulty_max}.")
        if todays_again_hit < AGAIN_LOW_FACTOR:
            self.young_difficulty_max = max(low_young_difficulty_max, self.young_difficulty_max - 1)
            self.logger.info(
                f"[{self.name}] Today's again hit: {todays_again_hit}. Difficulty decreased to {self.young_difficulty_max}.")
        self.last_updated = int(time())
