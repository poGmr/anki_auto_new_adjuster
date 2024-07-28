from PyQt6.QtWidgets import QDialog, QLabel, QCheckBox, QGridLayout, QGroupBox, QVBoxLayout, \
    QDoubleSpinBox, QSpinBox
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
        self.menu_button = QAction("Auto New Adjuster", mw)
        self.menu_button.triggered.connect(self.create_settings_window)
        mw.form.menuTools.addAction(self.menu_button)

    def enable_checkbox_change_state(self, state, checkbox):
        did = checkbox.property("did")
        if state == 0 or state == 1:
            self.add_on_config.set_deck_state(did=did, key="enabled", value=False)
        if state == 2:
            self.add_on_config.set_deck_state(did=did, key="enabled", value=True)

    def get_global_settings_group_box(self):
        global_group_box = QGroupBox("GLOBAL")
        global_grid_layout = QGridLayout()
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("Low focus level:"), 0, 0)
        global_spin_box_low = QDoubleSpinBox()
        global_spin_box_low.setEnabled(False)
        global_spin_box_low.setRange(0.00, 1.00)
        global_spin_box_low.setSingleStep(0.01)
        global_spin_box_low.setDecimals(2)
        global_spin_box_low.setValue(self.add_on_config.get_global_state(key="low_focus_level"))
        global_grid_layout.addWidget(global_spin_box_low, 0, 1)
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("High focus level:"), 1, 0)
        global_spin_box_high = QDoubleSpinBox()
        global_spin_box_high.setEnabled(False)
        global_spin_box_high.setRange(0.00, 1.00)
        global_spin_box_high.setSingleStep(0.01)
        global_spin_box_high.setDecimals(2)
        global_spin_box_high.setValue(self.add_on_config.get_global_state(key="high_focus_level"))
        global_grid_layout.addWidget(global_spin_box_high, 1, 1)
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("Lowest deck difficulty:"), 2, 0)
        global_spin_box_low = QSpinBox()
        global_spin_box_low.setEnabled(False)
        global_spin_box_low.setMinimum(0)
        global_spin_box_low.setMaximum(999)
        global_spin_box_low.setValue(self.add_on_config.get_global_state(key="lowest_young_max_difficulty_sum"))
        global_grid_layout.addWidget(global_spin_box_low, 2, 1)
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("Highest deck difficulty:"), 3, 0)
        global_spin_box_high = QSpinBox()
        global_spin_box_high.setEnabled(False)
        global_spin_box_high.setMinimum(0)
        global_spin_box_high.setMaximum(999)
        global_spin_box_high.setValue(self.add_on_config.get_global_state(key="highest_young_max_difficulty_sum"))
        global_grid_layout.addWidget(global_spin_box_high, 3, 1)
        ####################################################################################################
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
        decks_grid_layout.addWidget(QLabel("USER\nFOCUS"), 0, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel("STATUS"), 0, 6, alignment=Qt.AlignmentFlag.AlignCenter)

        i = 1
        for did in self.add_on_config.get_decks_ids():
            ####################################################################################################
            deck_name = QLabel(self.add_on_config.get_deck_state(did=did, key="name"))
            decks_grid_layout.addWidget(deck_name, i, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            ####################################################################################################
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
            enabled.setChecked(self.add_on_config.get_deck_state(did=did, key="enabled"))
            enabled.stateChanged.connect(
                lambda state, checkbox=enabled: self.enable_checkbox_change_state(state, checkbox))
            decks_grid_layout.addWidget(enabled, i, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            if enabled.isChecked():
                young_current_difficulty_sum = QLabel(
                    str(self.add_on_config.get_deck_state(did=did, key="young_current_difficulty_sum")))
                young_current_difficulty_sum.setHidden(False)

            else:
                young_current_difficulty_sum = QLabel("-")
                young_current_difficulty_sum.setHidden(True)
            decks_grid_layout.addWidget(young_current_difficulty_sum, i, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            young_max_difficulty_sum = QSpinBox()
            young_max_difficulty_sum.setEnabled(False)
            young_max_difficulty_sum.setMinimum(0)
            young_max_difficulty_sum.setMaximum(999)
            young_max_difficulty_sum.setValue(
                self.add_on_config.get_deck_state(did=did, key="young_max_difficulty_sum"))
            if enabled.isChecked():
                young_max_difficulty_sum.setValue(
                    self.add_on_config.get_deck_state(did=did, key="young_max_difficulty_sum"))
                young_max_difficulty_sum.setHidden(False)
            else:
                young_max_difficulty_sum.setHidden(True)
            decks_grid_layout.addWidget(young_max_difficulty_sum, i, 3, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            if enabled.isChecked():
                new_done = QLabel(str(self.add_on_config.get_deck_state(did=did, key="new_done")))
                new_done.setHidden(False)
            else:
                new_done = QLabel("-")
                new_done.setHidden(True)
            decks_grid_layout.addWidget(new_done, i, 4, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            if enabled.isChecked():

                todays_user_focus_level = self.add_on_config.get_deck_state(did=did, key="todays_user_focus_level")
                todays_user_focus_level = (round(todays_user_focus_level * 100))
                todays_user_focus_level = QLabel(str(todays_user_focus_level) + "%")
                todays_user_focus_level.setHidden(False)
            else:
                todays_user_focus_level = QLabel("-")
                todays_user_focus_level.setHidden(True)
            decks_grid_layout.addWidget(todays_user_focus_level, i, 5, alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            if enabled.isChecked():
                status = QLabel(str(self.add_on_config.get_deck_state(did=did, key="status")))
                status.setHidden(False)
            else:
                status = QLabel("-")
                status.setHidden(True)
            decks_grid_layout.addWidget(status, i, 6, alignment=Qt.AlignmentFlag.AlignCenter)
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
