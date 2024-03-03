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

    def get_pretty_config_data(self):
        return json.dumps(self.rawData, indent=4)

    def get_count_cards_count_done_today(self):
        query = f"deck:{self.name} rated:1"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def get_count_cards_introduced_today(self):
        query = f"deck:{self.name} introduced:1"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def get_count_still_in_queue(self):
        query = f"deck:{self.name} is:due"
        cards_count = len(mw.col.find_cards(query))
        return cards_count

    def get_young_count(self):
        query = f'"deck:{self.name}" AND '
        query += f'("is:review" AND -"is:learn") AND '
        query += f'"prop:ivl<21" AND '
        query += f'-("is:buried" OR "is:suspended")'
        cards_count = len(mw.col.find_cards(query))
        return cards_count
