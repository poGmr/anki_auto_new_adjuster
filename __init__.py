from aqt import gui_hooks
import logging
import os
from logging.handlers import RotatingFileHandler
from .manager import Manager

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s [%(filename)s][%(funcName)s:%(lineno)s][%(levelname)s]: %(message)s"
logFilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "auto_new_adjuster.log")
file_handler = RotatingFileHandler(logFilePath, maxBytes=10 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter(FORMAT)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def sync_will_start():
    logger.info("#")
    logger.info("####################################################################################")
    logger.info("#")
    logger.info("Sync has been requested.")


def sync_did_finish():
    logger.info("Sync has been finished.")
    m1: Manager = Manager(logger)
    m1.update()


gui_hooks.sync_did_finish.append(sync_did_finish)
gui_hooks.sync_will_start.append(sync_will_start)
