from aqt.gui_hooks import profile_did_open, profile_will_close
from aqt.gui_hooks import reviewer_did_answer_card, reviewer_will_end
from aqt.gui_hooks import sync_did_finish
from aqt.gui_hooks import deck_browser_will_render_content
from aqt.reviewer import Reviewer
from anki.cards import Card
from .addon_config import AddonConfig
from .gui import GUI
from typing import Literal
from PyQt6.QtGui import QAction
from .deck import Deck
import logging
import os
from logging.handlers import RotatingFileHandler
from aqt import mw


def update_all_decks() -> None:
    global add_on_config
    if 'add_on_config' in globals() and add_on_config is not None:
        for did in add_on_config.raw["decks"]:
            update_deck(did=did)


def update_deck(did: str) -> None:
    global logger
    global add_on_config
    if add_on_config.get_deck_state(did=did, key="enabled"):
        deck = Deck(did=did, logger=logger, add_on_config=add_on_config)
        deck.update_status()


def initialize_logger():
    result = logging.getLogger(__name__)
    if not result.handlers:
        log_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "auto_new_adjuster.log")
        file_handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3)
        log_format = "%(asctime)s [%(levelname)s]: %(message)s"
        formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)
        result.addHandler(file_handler)
        result.setLevel(logging.INFO)
    return result


@profile_did_open.append
def profile_did_open():
    global add_on_config
    global menu_button
    global gui_menu
    logger.debug("#")
    logger.debug("################################### profile_did_open ###################################")
    logger.info("#")
    add_on_config = AddonConfig(logger=logger)
    gui_menu = GUI(logger, add_on_config)
    menu_button = QAction("Auto New Adjuster", mw)
    menu_button.triggered.connect(update_all_decks)
    menu_button.triggered.connect(gui_menu.create_settings_window)
    mw.form.menuTools.addAction(menu_button)


@profile_will_close.append
def profile_will_close():
    global add_on_config
    global menu_button
    global gui_menu
    logger.debug("#")
    logger.debug("################################### profile_will_close ###################################")
    logger.debug("#")
    update_all_decks()
    try:
        if menu_button:
            mw.form.menuTools.removeAction(menu_button)
            menu_button.triggered.disconnect(gui_menu.create_settings_window)
            menu_button.triggered.disconnect(update_all_decks)
            del menu_button
    except NameError:
        pass  # menu_button was not defined, ignore
    del gui_menu
    add_on_config.__exit__()
    del add_on_config


@reviewer_did_answer_card.append
def reviewer_did_answer_card(reviewer: Reviewer, card: Card, ease: Literal[1, 2, 3, 4]):
    global logger
    logger.debug("#")
    logger.debug("################################### reviewer_did_answer_card ###################################")
    logger.debug("#")
    if card.odid == 0:
        did = str(card.did)
    else:
        did = str(card.odid)
    update_deck(did=did)


@reviewer_will_end.append
def reviewer_will_end():
    global logger
    logger.debug("#")
    logger.debug("################################### reviewer_did_answer_card ###################################")
    logger.debug("#")
    update_all_decks()


@sync_did_finish.append
def sync_did_finish():
    global logger
    logger.debug("#")
    logger.debug("################################### sync_did_finish ###################################")
    logger.debug("#")
    update_all_decks()


# @deck_browser_will_render_content.append
# def deck_browser_will_render_content(deck_browser: DeckBrowser, content: DeckBrowserContent):
#     global logger
#     global add_on_config
#     logger.debug("#")
#     logger.debug(
#         "################################### deck_browser_will_render_content ###################################")
#     logger.debug("#")
#     due_header = "\n<th class=count>Due</th>"
#     opts_header = "\n<th class=optscol>"
#     content.tree = content.tree.replace(due_header + opts_header,
#                                         due_header + "\n<th class=count>Today's<br>difficulty</th>" + opts_header)
#
#     deck_id_pattern = re.compile(r'\d{13}')
#     deck_id_results = deck_id_pattern.findall(content.tree)
#     for did in set(deck_id_results):
#         opts_td = "<td align=center class=opts>"
#         pycmd_onclick = f"<a onclick=\'return pycmd(\"opts:{did}\")"
#         if add_on_config.get_deck_state(did=did, key="enabled"):
#             deck = Deck(did=did, logger=logger, add_on_config=add_on_config)
#             deck.update_status()
#             todays_difficulty_avg = add_on_config.get_deck_state(did=did, key="todays_difficulty_avg")
#             diff_td = f"<td align=end>{round(100 * todays_difficulty_avg)}%"
#             content.tree = content.tree.replace(opts_td + pycmd_onclick,
#                                                 diff_td + opts_td + pycmd_onclick)
#         else:
#             diff_td = f"<td align=end>-"
#             content.tree = content.tree.replace(opts_td + pycmd_onclick,
#                                                 diff_td + opts_td + pycmd_onclick)


############################################################################################

logger = initialize_logger()
add_on_config: AddonConfig
menu_button: QAction
gui_menu: GUI
