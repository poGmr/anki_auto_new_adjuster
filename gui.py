from PyQt6.QtWidgets import QDialog, QLabel, QCheckBox, QGridLayout, QGroupBox, QVBoxLayout, QSpinBox
from PyQt6.QtCore import Qt
import logging
from .addon_config import AddonConfig


class TableColumnText:
    def __init__(self, cid: int, header: str):
        self.cid: int = cid
        self.header: QLabel = self._get_header(header)

    def _get_header(self, header: str) -> QLabel:
        label = QLabel(header)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-weight: bold;")
        return label

    def get_widget(self, value: str) -> QLabel:
        return QLabel(value)


class TableColumnCheckBox:
    def __init__(self, cid: int, header: str, add_on_config: AddonConfig):
        self.cid: int = cid
        self.header: QLabel = self._get_header(header)
        self.add_on_config: AddonConfig = add_on_config

    def _get_header(self, header: str) -> QLabel:
        label = QLabel(header)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-weight: bold;")
        return label

    def get_widget(self, did: str) -> QCheckBox:
        widget = QCheckBox()
        widget.setTristate(False)
        widget.setProperty("did", did)
        widget.setStyleSheet(self._get_css_style())
        value = bool(self.add_on_config.get_deck_state(did=did, key="enabled") is "True")
        widget.setChecked(value)
        widget.stateChanged.connect(
            lambda state, checkbox=widget: self.change_state(state, checkbox))

        return widget

    def change_state(self, state, checkbox: QCheckBox):
        did = checkbox.property("did")
        self.add_on_config.set_deck_state(did=did, key="enabled", value=checkbox.isChecked())

    def _get_css_style(self) -> str:
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


class TableColumnSpinBox:
    def __init__(self, cid: int, header: str):
        self.cid: int = cid
        self.header: QLabel = self._get_header(header)

    def _get_header(self, header: str) -> QLabel:
        label = QLabel(header)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-weight: bold;")
        return label


class GUI:
    def __init__(self, logger: logging.Logger, add_on_config: AddonConfig):
        self.logger: logging.Logger = logger
        self.add_on_config: AddonConfig = add_on_config

    def change_global_checkbox_state(self, state, checkbox):
        key = checkbox.property("key")
        if state == 0 or state == 1:
            self.add_on_config.set_global_state(key=key, value=False)
        if state == 2:
            self.add_on_config.set_global_state(key=key, value=True)

    def todays_spin_update_value(self, value, spin):
        did = spin.property("did")
        self.add_on_config.set_deck_state(did=did, key="todays_nlry_max", value=value)

    def get_global_settings_group_box(self):
        global_group_box = QGroupBox("GLOBAL")
        global_grid_layout = QGridLayout()
        ####################################################################################################
        global_grid_layout.addWidget(QLabel("Show new cards after review all decks"), 4, 0)
        chb_new_after_review_all_decks = QCheckBox()
        # chb_new_after_review_all_decks.setStyleSheet(get_checkbox_css_style())
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
        #
        # Create columns properties
        #
        col_name: TableColumnText = TableColumnText(0, "NAME")
        col_enabled: TableColumnCheckBox = TableColumnCheckBox(1, "ENABLED", self.add_on_config)
        col_today_nlry: TableColumnText = TableColumnText(2, "TODAY'S\nNLRY")
        col_today_nlry_max: TableColumnSpinBox = TableColumnSpinBox(3, "TODAY'S\nNLRY MAX")
        col_all_nlry: TableColumnText = TableColumnText(4, "ALL\nNLRY")
        col_new_done: TableColumnText = TableColumnText(5, "NEW\nDONE")
        col_status: TableColumnText = TableColumnText(6, "STATUS")
        col_last_100: TableColumnText = TableColumnText(7, "LAST 100")
        #
        # Add GUI columns
        #
        decks_grid_layout.addWidget(col_name.header, 0, col_name.cid, alignment=Qt.AlignmentFlag.AlignCenter)

        decks_grid_layout.addWidget(col_enabled.header, 0, col_enabled.cid,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(col_today_nlry.header, 0, col_today_nlry.cid,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(col_today_nlry_max.header, 0, col_today_nlry_max.cid,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(col_all_nlry.header, 0, col_all_nlry.cid,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(col_new_done.header, 0, col_new_done.cid, alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(col_status.header, 0, col_status.cid, alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(col_last_100.header, 0, col_last_100.cid, alignment=Qt.AlignmentFlag.AlignCenter)

        row = 1
        all_nlry_count = 0
        today_nlry_sum = 0
        today_nlry_max_sum = 0
        all_new_done = 0
        for did in self.add_on_config.get_decks_ids():
            ####################################################################################################
            deck_name = self.add_on_config.get_deck_state(did=did, key="name")
            decks_grid_layout.addWidget(col_name.get_widget(deck_name), row, col_name.cid,
                                        alignment=Qt.AlignmentFlag.AlignLeft)
            ####################################################################################################
            #
            #
            #
            # enabled = QCheckBox()
            # enabled.setProperty("did", did)
            # enabled.setStyleSheet(get_checkbox_css_style())
            # enabled.setChecked(self.add_on_config.get_deck_state(did=did, key="enabled"))
            # enabled.stateChanged.connect(
            #     lambda state, checkbox=enabled: self.enable_checkbox_change_state(state, checkbox))
            #

            # #
            #
            #
            enabled_widget = col_enabled.get_widget(did)
            decks_grid_layout.addWidget(enabled_widget, row,
                                        col_enabled.cid,
                                        alignment=Qt.AlignmentFlag.AlignCenter)
            if not enabled_widget.isChecked():
                row += 1
                continue
            ####################################################################################################
            today_nlry = self.add_on_config.get_deck_state(did=did, key="todays_nlry_sum")
            today_nlry_sum += int(today_nlry)
            decks_grid_layout.addWidget(col_today_nlry.get_widget(today_nlry), row, col_today_nlry.cid,
                                        alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            todays_nlry_max = self.add_on_config.get_deck_state(did=did, key="todays_nlry_max")
            today_nlry_max_sum += int(todays_nlry_max)
            todays_nlry_max_spin = QSpinBox()
            todays_nlry_max_spin.setRange(0, 1000)
            todays_nlry_max_spin.setValue(int(todays_nlry_max))
            todays_nlry_max_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            todays_nlry_max_spin.setProperty("did", did)
            todays_nlry_max_spin.valueChanged.connect(
                lambda value, spin=todays_nlry_max_spin: self.todays_spin_update_value(value, spin))
            decks_grid_layout.addWidget(todays_nlry_max_spin, row, col_today_nlry_max.cid,
                                        alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            nlry_sum = self.add_on_config.get_deck_state(did=did, key="nlry_sum")
            all_nlry_count += int(nlry_sum)
            decks_grid_layout.addWidget(col_all_nlry.get_widget(nlry_sum), row, col_all_nlry.cid,
                                        alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            new_done_count = self.add_on_config.get_deck_state(did=did, key="new_done")
            all_new_done += int(new_done_count)
            decks_grid_layout.addWidget(col_new_done.get_widget(new_done_count), row, col_new_done.cid,
                                        alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            status_text = self.add_on_config.get_deck_state(did=did, key="status")
            decks_grid_layout.addWidget(col_status.get_widget(status_text), row, col_status.cid,
                                        alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            last_100_nlry_retention_str = self.add_on_config.get_deck_state(did=did,
                                                                            key="last_100_nlry_reviews_retention")
            last_100_nlry_retention_per = round(float(last_100_nlry_retention_str) * 100)
            last_100_nlry_retention = str(last_100_nlry_retention_per) + "%"
            decks_grid_layout.addWidget(col_last_100.get_widget(last_100_nlry_retention), row, col_last_100.cid,
                                        alignment=Qt.AlignmentFlag.AlignCenter)
            ####################################################################################################
            row += 1
        # ADD SUMMARY LINE #################################################################################
        decks_grid_layout.addWidget(QLabel("TOTAL"), row, col_name.cid,
                                    alignment=Qt.AlignmentFlag.AlignLeft)
        decks_grid_layout.addWidget(QLabel(str(today_nlry_sum)), row, col_today_nlry.cid,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel(str(today_nlry_max_sum)), row, col_today_nlry_max.cid,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel(str(all_nlry_count)), row, col_all_nlry.cid,
                                    alignment=Qt.AlignmentFlag.AlignCenter)
        decks_grid_layout.addWidget(QLabel(str(all_new_done)), row, col_new_done.cid,
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
