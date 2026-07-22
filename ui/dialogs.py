#
# THE BALL GAME - Modal Dialogs
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

from typing import List, Dict, Any, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem
)


class SaveSelectorDialog(QDialog):
    """Modal dialog displaying available SQLite save games for user selection."""

    def __init__(self, saves: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Save Game")
        self.setMinimumSize(480, 340)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.selected_save_path: Optional[str] = None

        self.setStyleSheet("""
            QDialog {
                background-color: #0b140e;
                border: 2px solid #1e3f20;
                border-radius: 10px;
            }
            QLabel#DialogTitle {
                color: #e8f5e9;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 20px;
                font-weight: bold;
            }
            QListWidget {
                background-color: #111c15;
                border: 1px solid #1e3f20;
                border-radius: 8px;
                color: #e8f5e9;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-bottom: 1px solid #182b1e;
            }
            QListWidget::item:selected {
                background-color: #1e3f20;
                color: #81c784;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #16261d;
            }
            QPushButton {
                background-color: #111c15;
                border: 1px solid #2d6a4f;
                border-radius: 6px;
                color: #e8f5e9;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e3f20;
                border: 1px solid #81c784;
            }
            QPushButton#PrimaryBtn {
                background-color: #2d6a4f;
                border: 1px solid #81c784;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #40916c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("SELECT A SAVE GAME")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.saves = saves

        for save_info in saves:
            filename = save_info["filename"]
            time_str = save_info["formatted_time"]
            item_text = f"💾  {filename}   ({time_str})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, save_info["filepath"])
            self.list_widget.addItem(item)

        if saves:
            self.list_widget.setCurrentRow(0)

        self.list_widget.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        load_btn = QPushButton("Load Save")
        load_btn.setObjectName("PrimaryBtn")
        load_btn.clicked.connect(self.accept_selection)
        btn_layout.addWidget(load_btn)

        layout.addLayout(btn_layout)

    def accept_selection(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.selected_save_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.accept()


class SettingsDialog(QDialog):
    """Settings modal dialog accessible from the Home Screen."""
    main_menu_requested = pyqtSignal()
    exit_game_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(380, 280)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet("""
            QDialog {
                background-color: #0b140e;
                border: 2px solid #1e3f20;
                border-radius: 10px;
            }
            QLabel#Title {
                color: #e8f5e9;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 22px;
                font-weight: bold;
                qproperty-alignment: AlignCenter;
            }
            QPushButton.SettingsBtn {
                background-color: #111c15;
                border: 2px solid #1e3f20;
                border-radius: 8px;
                color: #e8f5e9;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton.SettingsBtn:hover {
                background-color: #1e3f20;
                border: 2px solid #81c784;
            }
            QPushButton#ExitBtn {
                background-color: #2b1111;
                border: 2px solid #5c1e1e;
                color: #ff8a8a;
            }
            QPushButton#ExitBtn:hover {
                background-color: #421616;
                border: 2px solid #ff4d4d;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(12)

        title = QLabel("SETTINGS & OPTIONS")
        title.setObjectName("Title")
        layout.addWidget(title)

        layout.addStretch(1)

        menu_btn = QPushButton("🏠  Return to Main Menu")
        menu_btn.setProperty("class", "SettingsBtn")
        menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        menu_btn.clicked.connect(self._on_main_menu)
        layout.addWidget(menu_btn)

        exit_btn = QPushButton("🚪  Exit Game")
        exit_btn.setObjectName("ExitBtn")
        exit_btn.setProperty("class", "SettingsBtn")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.clicked.connect(self._on_exit_game)
        layout.addWidget(exit_btn)

        resume_btn = QPushButton("Close Settings")
        resume_btn.setProperty("class", "SettingsBtn")
        resume_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        resume_btn.clicked.connect(self.reject)
        layout.addWidget(resume_btn)

        layout.addStretch(1)

    def _on_main_menu(self):
        self.accept()
        self.main_menu_requested.emit()

    def _on_exit_game(self):
        self.accept()
        self.exit_game_requested.emit()
