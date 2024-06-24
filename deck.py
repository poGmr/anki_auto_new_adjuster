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
        self.low_young_difficulty_max = 50
        self.high_young_difficulty_max = 150

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

    def get_deck_young_difficulty_sum(self) -> float:
        cards_id = self.get_ids_young_cards()
        difficulty_sum = 0.0
        for card_id in cards_id:
            difficulty_sum += self.get_card_difficulty(card_id=card_id)
        return difficulty_sum

    def get_todays_again_hit(self):
        query = f"deck:{self.name} AND rated:1"
        all_cards_count = len(mw.col.find_cards(query))
        query = f"deck:{self.name} AND rated:1:1"
        all_again_cards_count = len(mw.col.find_cards(query))
        if all_cards_count != 0:
            return round(1.0 - (all_again_cards_count / all_cards_count), 2)
        else:
            return 0.9

    def set_new_cards_count(self):
        deck_young_difficulty_sum: int = round(self.get_deck_young_difficulty_sum())
        deck_count_cards_introduced_today: int = self.get_count_cards_introduced_today()
        deck_new_config_limit: int = 0
        if self.get_count_still_in_queue() == 0:
            self.set_new_deck_difficulty()
            deck_new_config_limit = max(0,
                                        self.young_difficulty_max - deck_young_difficulty_sum + deck_count_cards_introduced_today)

        self.deck_config.set_new_count(new_count=deck_new_config_limit)

        debug_message: str = f"[{self.deck_config.name}][{self.name}] "
        debug_message += f"deck_young_difficulty_max {self.young_difficulty_max} | "
        debug_message += f"deck_young_difficulty_sum {deck_young_difficulty_sum} | "
        debug_message += f"deck_count_cards_introduced_today {deck_count_cards_introduced_today}"
        self.logger.debug(debug_message)

    def set_new_deck_difficulty(self):
        # self.logger.debug(f"[{deck.name}] young_max_difficulty: {deck.young_max_difficulty}")
        if time() - self.last_updated <= 20 * 60 * 60:
            # self.logger.debug(f"[{deck.name}] Updated in last 20h - no action is needed.")
            return
        current_value = self.young_difficulty_max
        todays_again_hit = self.get_todays_again_hit()
        debug_message: str = f"[{self.name}] Today again hit: {round(todays_again_hit * 100)}% | "
        debug_message += f"current young_difficulty_max: {current_value} | "
        if todays_again_hit >= 0.95:
            current_value = min(self.high_young_difficulty_max, current_value + 1)
        if todays_again_hit < 0.85:
            current_value = max(self.low_young_difficulty_max, current_value - 1)
        debug_message += f"new young_difficulty_max: {current_value}"
        self.logger.debug(debug_message)
        self.last_updated = int(time())
        self.young_difficulty_max = current_value
