from aqt.gui_hooks import profile_did_open, profile_will_close
from aqt.gui_hooks import reviewer_did_answer_card, reviewer_will_end
from aqt.gui_hooks import sync_did_finish
from aqt.reviewer import Reviewer
from anki.cards import Card
from .addon_config import AddonConfig
from .manager import Manager
from .gui import GUI
from typing import Literal
from PyQt6.QtGui import QAction
import logging
import os
from logging.handlers import RotatingFileHandler
from aqt import mw


def initialize_logging():
    log_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "auto_new_adjuster.log")
    handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s][%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


initialize_logging()
logger = logging.getLogger(__name__)


@profile_did_open.append
def profile_did_open():
    global add_on_config
    global menu_button
    global gui_menu
    global manager
    logger.debug("#")
    logger.debug("################################### profile_did_open ###################################")
    logger.info("###")
    add_on_config = AddonConfig()
    manager = Manager(add_on_config=add_on_config)
    gui_menu = GUI(add_on_config)
    menu_button = QAction("Auto New Adjuster", mw)
    menu_button.triggered.connect(manager.update_all_decks)
    menu_button.triggered.connect(gui_menu.create_settings_window)
    mw.form.menuTools.addAction(menu_button)


@profile_will_close.append
def profile_will_close():
    global add_on_config
    global menu_button
    global gui_menu
    global manager
    logger.debug("#")
    logger.debug("################################### profile_will_close ###################################")
    logger.debug("#")
    manager.update_all_decks()
    try:
        if menu_button:
            mw.form.menuTools.removeAction(menu_button)
            menu_button.triggered.disconnect(gui_menu.create_settings_window)
            menu_button.triggered.disconnect(manager.update_all_decks)
            del menu_button
    except NameError:
        pass  # menu_button was not defined, ignore
    del gui_menu
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
    logger.debug("#")
    logger.debug("################################### reviewer_did_answer_card ###################################")
    logger.debug("#")
    manager.update_all_decks()


@sync_did_finish.append
def sync_did_finish():
    global manager
    logger.debug("#")
    logger.debug("################################### sync_did_finish ###################################")
    logger.info("#")
    manager.update_all_decks()


add_on_config: AddonConfig
menu_button: QAction
gui_menu: GUI
manager: Manager
