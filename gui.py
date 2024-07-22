from PyQt6.QtWidgets import QDialog, QLabel, QCheckBox, QGridLayout
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
import logging
from .addon_config import AddonConfig
from aqt import mw


class GUI:
    def __init__(self, logger: logging.Logger, add_on_config: AddonConfig):
        self.logger: logging.Logger = logger
        self.add_on_config: AddonConfig = add_on_config
        self.menu_button = None

    def add_menu_button(self):
        self.menu_button = QAction("Auto New Adjuster Settings", mw)
        self.menu_button.triggered.connect(self.on_button_click)
        mw.form.menuTools.addAction(self.menu_button)

    def enable_checkbox_change_state(self, state, checkbox):
        did = checkbox.property("did")
        if state == 0 or state == 1:
            self.add_on_config.set_enable_deck_state(did=did, state=False)
        if state == 2:
            self.add_on_config.set_enable_deck_state(did=did, state=True)

    def on_button_click(self):
        dlg = QDialog()
        dlg.setWindowTitle("Auto New Adjuster Settings")
        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(QLabel("DECK"), 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(QLabel("ENABLED"), 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        i = 1
        for did in self.add_on_config.raw["decks"]:
            deck = self.add_on_config.raw["decks"][did]
            deck_name = QLabel(deck["name"])
            enabled = QCheckBox()
            enabled.setProperty("did", did)
            enabled.setStyleSheet("""
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
                QCheckBox::indicator:checked {
                    background-color: green;
                }
                QCheckBox::indicator:unchecked {
                    background-color: red;
                }
                        """)
            enabled.setChecked(deck["enabled"])
            enabled.stateChanged.connect(
                lambda state, checkbox=enabled: self.enable_checkbox_change_state(state, checkbox))
            layout.addWidget(deck_name, i, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(enabled, i, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            i += 1
        dlg.setLayout(layout)
        dlg.exec()
