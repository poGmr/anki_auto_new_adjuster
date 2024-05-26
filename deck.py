from aqt import mw
import json


class Deck:
    def __init__(self, raw_data, new_limit) -> None:
        self.rawData = raw_data
        self.newLimit = new_limit
        self.id = ""
        self.name = ""
        self.configID = ""
        self.update()

    def update(self):
        self.id = self.rawData["id"]
        self.name = self.rawData["name"]
        self.configID = self.rawData["conf"]

    # def get_pretty_config_data(self):
    #     return json.dumps(self.rawData, indent=4)

    # def get_count_cards_count_done_today(self):
    #     query = f"deck:{self.name} rated:1"
    #     cards_count = len(mw.col.find_cards(query))
    #     return cards_count

    def get_count_cards_introduced_today(self):
        query = f"deck:{self.name} introduced:1"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def get_count_still_in_queue(self):
        query = f"deck:{self.name} is:due"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    # def get_todays_cards_ids(self):
    #     query = f"deck:{self.name} (is:due OR rated:1)"
    #     ids = mw.col.find_cards(query)
    #     return ids

    # def get_hard_young_count(self):
    #     query = f'"deck:{self.name}" AND '
    #     query += f'("is:review" AND -"is:learn") AND '
    #     query += f'"prop:ivl<21" AND '
    #     query += f'"prop:d>0.5" AND '
    #     query += f'-("is:buried" OR "is:suspended")'
    #     cards_count = len(mw.col.find_cards(query))
    #     return cards_count

    def get_ids_young_cards(self):
        query = f'"deck:{self.name}" AND '
        query += f'("is:review" AND -"is:learn") AND '
        query += f'"prop:ivl<21" AND '
        query += f'-("is:buried" OR "is:suspended")'
        ids = mw.col.find_cards(query)
        return ids

    # def get_cards_difficulty(self, due_days: int = 1):
    #     query = f"deck:{self.name} AND prop:due<={due_days}"
    #     cards_ids = mw.col.find_cards(query)
    #     sum_result = 0
    #     n_result = 0
    #     for card_id in cards_ids:
    #         card_difficulty = self.get_card_difficulty(card_id)
    #         card_review_count = self.get_card_review_count(card_id)
    #         sum_result += card_difficulty * card_review_count
    #         n_result += card_review_count
    #     return sum_result / n_result

    def get_card_difficulty(self, card_id: int = 1397074673154) -> float:
        query = f"SELECT json_extract(data, '$.d') FROM cards WHERE id={card_id}"
        d = mw.col.db.all(query)[0][0]
        d = (d - 1) / 9
        return d

    # def get_card_review_count(self, card_id: int = 1397074673154) -> int:
    #     query = f"SELECT count() FROM revlog WHERE cid={card_id}"
    #     result = mw.col.db.scalar(query)
    #     return result

    # def get_todays_deck_difficulty_count(self):
    #     ids = self.get_todays_cards_ids()
    #     difficulty_sum = 0.0
    #     for id in ids:
    #         difficulty_sum += self.get_card_difficulty(card_id=id)
    #     return difficulty_sum

    def get_all_young_deck_difficulty_sum(self):
        ids = self.get_ids_young_cards()
        difficulty_sum = 0.0
        for id in ids:
            difficulty_sum += self.get_card_difficulty(card_id=id)
        return difficulty_sum

    def get_todays_all_difficulty(self):
        query = f"deck:{self.name} AND rated:1"
        ids = mw.col.find_cards(query)
        difficulty_sum = 0.0
        for id in ids:
            difficulty_sum += self.get_card_difficulty(card_id=id)
        return round(difficulty_sum)
