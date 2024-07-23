from aqt import gui_hooks

import logging
import os
from logging.handlers import RotatingFileHandler
from .manager import Manager
from .addon_config import AddonConfig
from .gui import GUI


def initialize_logger():
    result = logging.getLogger(__name__)
    if not result.handlers:
        log_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "auto_new_adjuster.log")
        file_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=3)
        log_format = "%(asctime)s [%(levelname)s]: %(message)s"
        formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)
        result.addHandler(file_handler)
        result.setLevel(logging.INFO)
    return result


logger = initialize_logger()


def profile_did_open():
    addon_gui = GUI(logger)
    gui_hooks.profile_did_open.append(addon_gui.add_menu_button)


def sync_will_start():
    logger.info("#")
    logger.info("####################################################################################")
    logger.info("#")
    logger.debug("Sync has been requested.")


def sync_did_finish():
    logger.debug("Sync has been finished.")
    add_on_config = AddonConfig(logger)
    m1: Manager = Manager(logger, add_on_config)
    m1.update()


gui_hooks.sync_did_finish.append(sync_did_finish)
gui_hooks.sync_will_start.append(sync_will_start)
gui_hooks.profile_did_open.append(profile_did_open)
