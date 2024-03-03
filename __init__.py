from aqt import gui_hooks
import logging
import os
from logging.handlers import RotatingFileHandler
from .manager import Manager

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s [%(filename)s][%(funcName)s:%(lineno)s][%(levelname)s]: %(message)s"
logFilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "auto_new_adjuster.log")
file_handler = RotatingFileHandler(logFilePath, maxBytes=1e6, backupCount=3)
formatter = logging.Formatter(FORMAT)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


def sync_did_finish():
    logger.info("#")
    logger.info("####################################################################################")
    logger.info("#")
    manager: Manager = Manager(logger)
    manager.update()
    logger.debug(os.path.abspath(__file__))


gui_hooks.sync_did_finish.append(sync_did_finish)
