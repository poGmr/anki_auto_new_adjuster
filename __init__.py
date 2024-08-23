from aqt.gui_hooks import profile_did_open, profile_will_close, reviewer_did_answer_card, reviewer_will_end
from aqt.gui_hooks import addon_config_editor_will_display_json, addon_config_editor_will_save_json
from aqt.reviewer import Reviewer
from anki.cards import Card
import logging
import os
from logging.handlers import RotatingFileHandler
from .manager import Manager
from .addon_config import AddonConfig
from .gui import GUI
from typing import Literal
from PyQt6.QtGui import QAction
from aqt import mw
import json


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
    global manager
    global menu_button
    global gui_menu
    logger.debug("#")
    logger.debug("################################### profile_did_open ###################################")
    logger.info("#")
    add_on_config = AddonConfig(logger=logger)
    manager = Manager(logger, add_on_config)
    gui_menu = GUI(logger, add_on_config)
    menu_button = QAction("Auto New Adjuster", mw)
    menu_button.triggered.connect(manager.update_all_decks)
    menu_button.triggered.connect(gui_menu.create_settings_window)
    mw.form.menuTools.addAction(menu_button)


@profile_will_close.append
def profile_will_close():
    global add_on_config
    global manager
    global menu_button
    global gui_menu
    logger.debug("#")
    logger.debug("################################### profile_will_close ###################################")
    logger.debug("#")
    manager.update_all_decks()
    mw.form.menuTools.removeAction(menu_button)
    menu_button.triggered.disconnect(gui_menu.create_settings_window)
    menu_button.triggered.disconnect(manager.update_all_decks)
    del menu_button
    del gui_menu
    del manager
    add_on_config.__exit__()
    del add_on_config


@reviewer_did_answer_card.append
def reviewer_did_answer_card(reviewer: Reviewer, card: Card, ease: Literal[1, 2, 3, 4]):
    global manager
    logger.debug("#")
    logger.debug("################################### reviewer_did_answer_card ###################################")
    logger.debug("#")
    if card.odid == 0:
        did = str(card.did)
    else:
        did = str(card.odid)
    manager.update_deck(did=did)


@reviewer_will_end.append
def reviewer_will_end():
    global manager
    manager.update_all_decks()


# @addon_config_editor_will_save_json.append
# def addon_config_editor_will_save_json(text: str):
#     global logger
#     global add_on_config
#     add_on_config.raw = json.loads(text)
#     return text
#
#
# @addon_config_editor_will_display_json.append
# def addon_config_editor_will_display_json(text: str):
#     global logger
#     global add_on_config
#     return json.dumps(add_on_config.raw, indent=4)


############################################################################################

logger = initialize_logger()
add_on_config: AddonConfig
manager: Manager
menu_button: QAction
gui_menu: GUI
