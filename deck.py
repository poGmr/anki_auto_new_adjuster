from aqt import mw
from collections.abc import Sequence
import logging
from .config import DeckConfig
from time import time
from .addon_config import AddonConfig


class Deck:
    def __init__(self, deck_id: str, logger: logging.Logger) -> None:
        self.logger: logging.Logger = logger
        self.add_on_config: AddonConfig = AddonConfig(self.logger)
        self.raw_data: dict[str, str] = mw.col.decks.get(deck_id)
        self.id: str = str(self.raw_data["id"])
        self.name = self.raw_data["name"]
        self.deck_config: DeckConfig = DeckConfig(logger=self.logger, did=self.id)
        self.LOW_YOUNG_MAX_DIFFICULTY = 21
        self.HIGH_YOUNG_MAX_DIFFICULTY = 210
        self.AGAIN_LOW_FACTOR = 85
        self.AGAIN_HIGH_FACTOR = 95

    def _get_card_difficulty(self, card_id: int) -> float:
        query = f"SELECT json_extract(data, '$.d') FROM cards WHERE id={card_id}"
        d = mw.col.db.all(query)[0][0]
        d = (d - 1) / 9
        return d

    def _get_count_cards_introduced_today(self) -> int:
        query = f"deck:{self.name} introduced:1"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def _get_count_still_in_queue(self) -> int:
        query = f"deck:{self.name} is:due"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def _get_deck_young_difficulty_sum(self) -> int:
        cards_id = self._get_ids_young_cards()
        difficulty_sum = 0.0
        for card_id in cards_id:
            difficulty_sum += self._get_card_difficulty(card_id=card_id)
        return round(difficulty_sum)

    def _get_ids_young_cards(self) -> Sequence:
        query = f'"deck:{self.name}" AND '
        query += f'("is:review" AND -"is:learn") AND '
        query += f'"prop:ivl<21" AND '
        query += f'-("is:buried" OR "is:suspended")'
        ids = mw.col.find_cards(query)
        return ids

    def _get_todays_again_hit(self) -> float:
        query = f"deck:{self.name} AND rated:1"
        all_cards_count = len(mw.col.find_cards(query))
        query = f"deck:{self.name} AND rated:1:1"
        all_again_cards_count = len(mw.col.find_cards(query))
        if all_cards_count != 0:
            return round(1.0 - (all_again_cards_count / all_cards_count), 2)
        else:
            return 0.9

    def set_deck_difficulty(self):
        last_updated = self.add_on_config.raw["decks"][self.id]["last_updated"]
        young_max_difficulty = self.add_on_config.raw["decks"][self.id]["young_max_difficulty"]
        cut_off_time = mw.col.sched.day_cutoff
        if cut_off_time - last_updated <= 60 * 60 * 24:
            logger_output = f"[{self.name}] Deck difficulty has been already changed today."
            logger_output += f" Next change is going to happen in {cut_off_time - int(time())} sec."
            self.logger.debug(logger_output)
            return

        todays_again_hit = round(self._get_todays_again_hit() * 100)
        info_log = f"[{self.name}] Today's again hit: {todays_again_hit}%."
        if todays_again_hit < self.AGAIN_LOW_FACTOR:
            young_max_difficulty = max(self.LOW_YOUNG_MAX_DIFFICULTY, young_max_difficulty - 1)
            self.add_on_config.set_young_max_difficulty(self.id, young_max_difficulty)
            info_log += f" Difficulty decreased to {young_max_difficulty}."

        if self.AGAIN_LOW_FACTOR <= todays_again_hit < self.AGAIN_HIGH_FACTOR:
            info_log += f" No need to adjust deck difficulty."

        if todays_again_hit >= self.AGAIN_HIGH_FACTOR:
            young_max_difficulty = min(self.HIGH_YOUNG_MAX_DIFFICULTY, young_max_difficulty + 1)
            info_log += f" Difficulty increased to {young_max_difficulty}."
            self.add_on_config.set_young_max_difficulty(self.id, young_max_difficulty)
        self.logger.info(info_log)
        self.add_on_config.set_last_updated(self.id, int(time()))

    def set_new_cards_count(self):
        young_max_difficulty = self.add_on_config.raw["decks"][self.id]["young_max_difficulty"]
        deck_new_config_limit = young_max_difficulty
        deck_new_config_limit -= self._get_deck_young_difficulty_sum()
        deck_new_config_limit += self._get_count_cards_introduced_today()
        deck_new_config_limit = max(0, deck_new_config_limit)

        self.deck_config.set_new_count(new_count=deck_new_config_limit)

        logger_output = f"[{self.name}] Today's deck difficulty: {self._get_deck_young_difficulty_sum()}."
        logger_output += f" Max allowed difficulty: {young_max_difficulty}"
        self.logger.info(logger_output)
