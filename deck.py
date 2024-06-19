from aqt import mw
from collections.abc import Sequence
import logging


class Deck:
    def __init__(self, raw_data: dict[str, str], young_difficulty_max: int, logger: logging) -> None:
        self.logger: logging = logger
        self.rawData: dict[str, str] = raw_data
        self.young_difficulty_max: int = young_difficulty_max
        self.id = self.rawData["id"]
        self.name = self.rawData["name"]
        self.configID = self.rawData["conf"]

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
