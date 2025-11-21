from PyQt6.QtWidgets import QDialog, QLabel, QCheckBox, QGridLayout, QGroupBox, QVBoxLayout, QSpinBox
from PyQt6.QtCore import Qt
import logging
from .addon_config import AddonConfig


class DC:
    NAME = 0
    ENABLED = 1
    TODAYS_NLRY = 2
    TODAYS_NLRY_MAX = 3
    ALL_NLRY = 4
    NEW_DONE = 5
    STATUS = 6


def get_checkbox_css_style() -> str:
    return """
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
                                """


def get_header_table_ql(text: str) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("font-weight: bold;")
    return label


class GUI:
    def __init__(self, logger: logging.Logger, add_on_config: AddonConfig):
        # TODO: add TextBox to show todays logging
        self.logger: logging.Logger = logger
        self.add_on_config: AddonConfig = add_on_config

    def change_global_checkbox_state(self, state, checkbox):
        key = checkbox.property("key")
        if state == 0 or state == 1:
            self.add_on_config.set_global_state(key=key, value=False)
        if state == 2:
            self.add_on_config.set_global_state(key=key, value=True)

    def enable_checkbox_change_state(self, state, checkbox):
        did = checkbox.property("did")
        if state == 0 or state == 1:
            self.add_on_config.set_deck_state(did=did, key="enabled", value=False)
        if state == 2:
            self.add_on_config.set_deck_state(did=did, key="enabled", value=True)

    def todays_spin_update_value(self, value, spin):
        did = spin.property("did")
        self.add_on_config.set_deck_state(did=did, key="todays_nlry_max", value=value)

    def get_global_settings_group_box(self):
        global_group_box = QGroupBox("GLOBAL")
        global_grid_layout = QGridLayout()
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("Show new cards after review all decks"), 4, 0)
        chb_new_after_review_all_decks = QCheckBox()
        chb_new_after_review_all_decks.setStyleSheet(get_checkbox_css_style())
        chb_new_after_review_all_decks.setProperty("key", "new_after_review_all_decks")
        chb_new_after_review_all_decks.stateChanged.connect(
            lambda state, checkbox=chb_new_after_review_all_decks: self.change_global_checkbox_state(state, checkbox))
        chb_new_after_review_all_decks.setChecked(
            self.add_on_config.get_global_state(key=chb_new_after_review_all_decks.property("key")))
        global_grid_layout.addWidget(chb_new_after_review_all_decks, 4, 1)
        global_group_box.setLayout(global_grid_layout)

        return global_group_box

    def get_deck_settings_group_box(self):
        decks_grid_layout = QGridLayout()
        decks_grid_layout.setContentsMargins(5, 5, 5, 5)
        decks_grid_layout.addWidget(get_header_table_ql("NAME"), 0, DC.NAME,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(get_header_table_ql("ENABLED"), 0, DC.ENABLED,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(get_header_table_ql("TODAY'S\nNLRY"), 0, DC.TODAYS_NLRY,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(get_header_table_ql("TODAY'S\nNLRY MAX"), 0, DC.TODAYS_NLRY_MAX,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(get_header_table_ql("ALL\nNLRY"), 0, DC.ALL_NLRY,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(get_header_table_ql("NEW\nDONE"), 0, DC.NEW_DONE,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(get_header_table_ql("STATUS"), 0, DC.STATUS,
                                    alignment=Qt.AlignmentFlag.AlignCenter)

        row = 1
        all_nlry_count = 0
        today_nlry_sum = 0
        today_nlry_max_sum = 0
        all_new_done = 0
        for did in self.add_on_config.get_decks_ids():
            ####################################################################################################
            deck_name = QLabel(self.add_on_config.get_deck_state(did=did, key="name"))
            decks_grid_layout.addWidget(deck_name, row, DC.NAME, alignment=Qt.AlignmentFlag.AlignLeft)
            ####################################################################################################
            enabled = QCheckBox()
            enabled.setProperty("did", did)
            enabled.setStyleSheet(get_checkbox_css_style())
            enabled.setChecked(self.add_on_config.get_deck_state(did=did, key="enabled"))
            enabled.stateChanged.connect(
                lambda state, checkbox=enabled: self.enable_checkbox_change_state(state, checkbox))
            decks_grid_layout.addWidget(enabled, row, DC.ENABLED, alignment=Qt.AlignmentFlag.AlignCenter)
            if not enabled.isChecked():
                row += 1
                continue
            ####################################################################################################
            today_nlry = int(self.add_on_config.get_deck_state(did=did, key="todays_nlry_sum"))
            today_nlry_sum += today_nlry
            todays_nlry_sum = QLabel(str(today_nlry))
            decks_grid_layout.addWidget(todays_nlry_sum, row, DC.TODAYS_NLRY,
                                        alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            todays_nlry_max = str(
                self.add_on_config.get_deck_state(did=did, key="todays_nlry_max"))
            today_nlry_max_sum += int(todays_nlry_max)
            todays_nlry_max_spin = QSpinBox()
            todays_nlry_max_spin.setRange(0, 1000)
            todays_nlry_max_spin.setValue(int(todays_nlry_max))
            todays_nlry_max_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            todays_nlry_max_spin.setProperty("did", did)
            todays_nlry_max_spin.valueChanged.connect(
                lambda value, spin=todays_nlry_max_spin: self.todays_spin_update_value(value, spin))
            decks_grid_layout.addWidget(todays_nlry_max_spin, row, DC.TODAYS_NLRY_MAX,
                                        alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            nlry_sum = QLabel(
                str(self.add_on_config.get_deck_state(did=did, key="nlry_sum")))
            all_nlry_count += int(nlry_sum.text())
            decks_grid_layout.addWidget(nlry_sum, row, DC.ALL_NLRY, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            new_done_count = self.add_on_config.get_deck_state(did=did, key="new_done")
            all_new_done += int(new_done_count)
            new_done_label = QLabel(str(new_done_count))
            decks_grid_layout.addWidget(new_done_label, row, DC.NEW_DONE, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            status_text = str(self.add_on_config.get_deck_state(did=did, key="status"))
            status_label = QLabel(status_text)
            decks_grid_layout.addWidget(status_label, row, DC.STATUS, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            row += 1
        # ADD SUMMARY LINE #################################################################################
        decks_grid_layout.addWidget(QLabel("TOTAL"), row, DC.NAME,
                                    alignment=Qt.AlignmentFlag.AlignLeft)
        decks_grid_layout.addWidget(QLabel(str(today_nlry_sum)), row, DC.TODAYS_NLRY,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel(str(today_nlry_max_sum)), row, DC.TODAYS_NLRY_MAX,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel(str(all_nlry_count)), row, DC.ALL_NLRY,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel(str(all_new_done)), row, DC.NEW_DONE,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        ####################################################################################################
        decks_group_box = QGroupBox("DECKS")
        decks_group_box.setLayout(decks_grid_layout)
        return decks_group_box

    def create_settings_window(self):
        dlg = QDialog()
        dlg.setWindowTitle("Auto New Adjuster")
        window_layout = QVBoxLayout()
        window_layout.addWidget(self.get_global_settings_group_box())
        window_layout.addWidget(self.get_deck_settings_group_box())
        dlg.setLayout(window_layout)
        dlg.exec()
