from aqt import gui_hooks
from aqt.reviewer import Reviewer
from anki.cards import Card
import logging
import os
from logging.handlers import RotatingFileHandler
from .manager import Manager
from .addon_config import AddonConfig
from .gui import GUI
from typing import Literal


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


def profile_did_open():
    global add_on_config
    global manager
    logger.info("#")
    add_on_config = AddonConfig(logger=logger)
    manager = Manager(logger, add_on_config)
    addon_gui = GUI(logger, add_on_config)
    gui_hooks.profile_did_open.append(addon_gui.add_menu_button)


def sync_did_finish():
    global manager
    logger.debug("#")
    logger.debug("################################### sync_did_finish ###################################")
    logger.debug("#")
    manager.update_all_decks()


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


def reviewer_will_end():
    logger.debug("#")
    logger.debug("################################### reviewer_will_end ###################################")
    logger.debug("#")


logger = initialize_logger()
logger.debug("#")
logger.debug("#")
logger.debug("#")
add_on_config: AddonConfig
manager: Manager

gui_hooks.sync_did_finish.append(sync_did_finish)
gui_hooks.profile_did_open.append(profile_did_open)
gui_hooks.reviewer_did_answer_card.append(reviewer_did_answer_card)
