from PyQt6.QtWidgets import QDialog, QLabel, QCheckBox, QGridLayout, QGroupBox, QVBoxLayout, QSpinBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
import logging
from .addon_config import AddonConfig


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

    def spin_update_value(self, value, spin):
        did = spin.property("did")
        # self.logger.info(f"update_value did, value {did}, {value}")
        self.add_on_config.set_deck_state(did=did, key="young_max_difficulty_sum", value=value)

    def get_global_settings_group_box(self):
        global_group_box = QGroupBox("GLOBAL")
        global_grid_layout = QGridLayout()
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("Low focus level:"), 0, 0)
        low_focus_level_value = round(100 * self.add_on_config.get_global_state(key="low_focus_level"))
        low_focus_level = QLabel(str(low_focus_level_value) + "%")
        global_grid_layout.addWidget(low_focus_level, 0, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("High focus level:"), 1, 0)
        high_focus_level_value = round(100 * self.add_on_config.get_global_state(key="high_focus_level"))
        high_focus_level = QLabel(str(high_focus_level_value) + "%")
        global_grid_layout.addWidget(high_focus_level, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("Lowest deck difficulty:"), 2, 0)
        lowest_young_max_difficulty_sum = QLabel(
            str(self.add_on_config.get_global_state(key="lowest_young_max_difficulty_sum")))
        global_grid_layout.addWidget(lowest_young_max_difficulty_sum, 2, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("Highest deck difficulty:"), 3, 0)
        highest_young_max_difficulty_sum = QLabel(
            str(self.add_on_config.get_global_state(key="highest_young_max_difficulty_sum")))
        global_grid_layout.addWidget(highest_young_max_difficulty_sum, 3, 1, alignment=Qt.AlignmentFlag.AlignLeft)
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
        decks_grid_layout.addWidget(QLabel("DECK"), 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel("ENABLED"), 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel("CURRENT\nDIFFICULTY"), 0, 2,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel("MAX\nDIFFICULTY"), 0, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel("NEW\nDONE"), 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
        # decks_grid_layout.addWidget(QLabel("USER\nFOCUS"), 0, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel("STATUS"), 0, 6, alignment=Qt.AlignmentFlag.AlignCenter)

        i = 1
        for did in self.add_on_config.get_decks_ids():
            ####################################################################################################
            deck_name = QLabel(self.add_on_config.get_deck_state(did=did, key="name"))
            decks_grid_layout.addWidget(deck_name, i, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            ####################################################################################################
            enabled = QCheckBox()
            enabled.setProperty("did", did)
            enabled.setStyleSheet(get_checkbox_css_style())
            enabled.setChecked(self.add_on_config.get_deck_state(did=did, key="enabled"))
            enabled.stateChanged.connect(
                lambda state, checkbox=enabled: self.enable_checkbox_change_state(state, checkbox))
            decks_grid_layout.addWidget(enabled, i, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            if not enabled.isChecked():
                i += 1
                continue
            ####################################################################################################
            young_current_difficulty_sum = QLabel(
                str(self.add_on_config.get_deck_state(did=did, key="young_current_difficulty_sum")))

            decks_grid_layout.addWidget(young_current_difficulty_sum, i, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            new_done = QLabel(str(self.add_on_config.get_deck_state(did=did, key="new_done")))
            decks_grid_layout.addWidget(new_done, i, 4, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            # todays_user_focus_level = self.add_on_config.get_deck_state(did=did, key="todays_user_focus_level")
            # todays_user_focus_level = (round(todays_user_focus_level * 100))
            # todays_user_focus_level = QLabel(str(todays_user_focus_level) + "%")
            # decks_grid_layout.addWidget(todays_user_focus_level, i, 5, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            status_text = str(self.add_on_config.get_deck_state(did=did, key="status"))
            status_label = QLabel(status_text)
            decks_grid_layout.addWidget(status_label, i, 6, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            # trend = str(self.add_on_config.get_deck_state(did=did, key="trend"))
            ####################################################################################################
            young_max_difficulty_sum = str(self.add_on_config.get_deck_state(did=did, key="young_max_difficulty_sum"))
            young_max_difficulty_sum_spin = QSpinBox()
            young_max_difficulty_sum_spin.setRange(0, 1000)
            young_max_difficulty_sum_spin.setValue(int(young_max_difficulty_sum))
            young_max_difficulty_sum_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            young_max_difficulty_sum_spin.setProperty("did", did)
            young_max_difficulty_sum_spin.valueChanged.connect(
                lambda value, spin=young_max_difficulty_sum_spin: self.spin_update_value(value, spin))
            decks_grid_layout.addWidget(young_max_difficulty_sum_spin, i, 3, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            i += 1
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
