#
# THE BALL GAME - Application Screens
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

import os
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QDialog
)
from loguru import logger

from model import (
    get_save_files, get_teams_template_data, get_active_game_status
)
from ui.diamond import BaseballDiamondWidget
from ui.dialogs import SaveSelectorDialog, SettingsDialog


def get_team_logo_path(team_name: str) -> str:
    """Return the filesystem path for a team's logo image if it exists."""
    filename = team_name.lower().replace(" ", "_") + ".png"
    filepath = os.path.join("data", "logos", filename)
    if os.path.exists(filepath):
        return filepath
    return ""


# --- Welcome Screen ---

class WelcomeScreen(QWidget):
    """Welcome screen widget presenting game title, diamond animation, and New/Continue/Load menu."""
    new_game_requested = pyqtSignal()
    continue_requested = pyqtSignal()
    load_game_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel {
                background-color: transparent;
            }
            QLabel#TitleLabel {
                color: #e8f5e9;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 44px;
                font-weight: 800;
                letter-spacing: 2px;
                qproperty-alignment: AlignCenter;
            }
            QLabel#SubtitleLabel {
                color: #81c784;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 17px;
                font-style: italic;
                letter-spacing: 1px;
                qproperty-alignment: AlignCenter;
            }
            QPushButton.MenuBtn {
                background-color: #111c15;
                border: 2px solid #1e3f20;
                border-radius: 8px;
                color: #e8f5e9;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 12px 30px;
                min-width: 220px;
            }
            QPushButton.MenuBtn:hover {
                background-color: #1b3823;
                border: 2px solid #81c784;
                color: #ffffff;
            }
            QPushButton.MenuBtnPrimary {
                background-color: #1b4328;
                border: 2px solid #2d6a4f;
                color: #ffffff;
            }
            QPushButton.MenuBtnPrimary:hover {
                background-color: #2d6a4f;
                border: 2px solid #81c784;
            }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(50, 30, 50, 30)
        self.main_layout.setSpacing(10)

        self.main_layout.addStretch(1)

        self.title_label = QLabel("THE BALL GAME")
        self.title_label.setObjectName("TitleLabel")
        self.main_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("A tiny baseball simulator")
        self.subtitle_label.setObjectName("SubtitleLabel")
        self.main_layout.addWidget(self.subtitle_label)

        self.main_layout.addStretch(1)

        self.diamond_widget = BaseballDiamondWidget()
        diamond_container = QHBoxLayout()
        diamond_container.addStretch(1)
        diamond_container.addWidget(self.diamond_widget)
        diamond_container.addStretch(1)
        self.main_layout.addLayout(diamond_container)

        self.main_layout.addStretch(1)

        # Dynamic Menu Button Container
        self.menu_container = QVBoxLayout()
        self.menu_container.setSpacing(10)
        self.menu_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addLayout(self.menu_container)
        self.main_layout.addStretch(1)

        self.refresh_menu()

    def refresh_menu(self) -> None:
        """Clear and rebuild action menu buttons based on available save files."""
        while self.menu_container.count():
            item = self.menu_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        saves = get_save_files()

        if saves:
            latest_file = saves[0]["filename"]
            btn_continue = QPushButton(f"CONTINUE  ({latest_file})")
            btn_continue.setProperty("class", "MenuBtn MenuBtnPrimary")
            btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_continue.clicked.connect(self._on_continue_clicked)
            self.menu_container.addWidget(btn_continue, 0, Qt.AlignmentFlag.AlignCenter)

            btn_new = QPushButton("NEW GAME")
            btn_new.setProperty("class", "MenuBtn")
            btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_new.clicked.connect(self._on_new_game_clicked)
            self.menu_container.addWidget(btn_new, 0, Qt.AlignmentFlag.AlignCenter)

            btn_load = QPushButton("LOAD GAME...")
            btn_load.setProperty("class", "MenuBtn")
            btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_load.clicked.connect(self._on_load_game_clicked)
            self.menu_container.addWidget(btn_load, 0, Qt.AlignmentFlag.AlignCenter)
        else:
            btn_new = QPushButton("NEW GAME")
            btn_new.setProperty("class", "MenuBtn MenuBtnPrimary")
            btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_new.clicked.connect(self._on_new_game_clicked)
            self.menu_container.addWidget(btn_new, 0, Qt.AlignmentFlag.AlignCenter)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh_menu()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def _on_continue_clicked(self) -> None:
        logger.info("User selected CONTINUE game.")
        self.continue_requested.emit()

    def _on_new_game_clicked(self) -> None:
        logger.info("User selected NEW GAME.")
        self.new_game_requested.emit()

    def _on_load_game_clicked(self) -> None:
        saves = get_save_files()
        if not saves:
            return

        dialog = SaveSelectorDialog(saves, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_save_path:
            logger.info(f"User selected save file to load: {dialog.selected_save_path}")
            self.load_game_requested.emit(dialog.selected_save_path)


# --- Team Selection Screen ---

class TeamSelectCardWidget(QFrame):
    """Clickable and selectable card for picking a franchise in TeamSelectScreen."""
    selected_signal = pyqtSignal(str)

    def __init__(self, team_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.team_name = team_data["name"]
        self.is_selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(220, 220)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(6)

        logo_label = QLabel()
        logo_label.setFixedSize(64, 64)
        logo_path = get_team_logo_path(self.team_name)
        if logo_path:
            pix = QPixmap(logo_path).scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(pix)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_container = QHBoxLayout()
        logo_container.addStretch(1)
        logo_container.addWidget(logo_label)
        logo_container.addStretch(1)
        layout.addLayout(logo_container)

        name_label = QLabel(self.team_name)
        name_label.setObjectName("TeamName")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        meta_label = QLabel(f"{team_data['city']}, {team_data['nation']}")
        meta_label.setObjectName("TeamMeta")
        layout.addWidget(meta_label)

        stadium_label = QLabel(f"🏟 {team_data['stadium_name']}")
        stadium_label.setObjectName("TeamStadium")
        layout.addWidget(stadium_label)

        layout.addStretch(1)

    def set_selected(self, selected: bool) -> None:
        self.is_selected = selected
        self.update_style()

    def update_style(self) -> None:
        if self.is_selected:
            self.setStyleSheet("""
                TeamSelectCardWidget {
                    background-color: #1b3823;
                    border: 3px solid #81c784;
                    border-radius: 12px;
                }
                QLabel { background-color: transparent; }
                QLabel#TeamName { color: #ffffff; font-family: 'Helvetica Neue', Arial; font-size: 16px; font-weight: bold; qproperty-alignment: AlignCenter; }
                QLabel#TeamMeta { color: #a5d6a7; font-size: 13px; qproperty-alignment: AlignCenter; }
                QLabel#TeamStadium { color: #81c784; font-size: 11px; font-style: italic; qproperty-alignment: AlignCenter; }
            """)
        else:
            self.setStyleSheet("""
                TeamSelectCardWidget {
                    background-color: #111c15;
                    border: 2px solid #1e3f20;
                    border-radius: 12px;
                }
                TeamSelectCardWidget:hover {
                    background-color: #16261d;
                    border: 2px solid #81c784;
                }
                QLabel { background-color: transparent; }
                QLabel#TeamName { color: #e8f5e9; font-family: 'Helvetica Neue', Arial; font-size: 15px; font-weight: bold; qproperty-alignment: AlignCenter; }
                QLabel#TeamMeta { color: #81c784; font-size: 13px; qproperty-alignment: AlignCenter; }
                QLabel#TeamStadium { color: #a5d6a7; font-size: 11px; font-style: italic; qproperty-alignment: AlignCenter; }
            """)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected_signal.emit(self.team_name)
            event.accept()
        else:
            super().mousePressEvent(event)


class TeamSelectScreen(QWidget):
    """Screen presented when starting a new game, allowing the user to select their franchise team."""
    team_chosen = pyqtSignal(str)
    back_to_welcome = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.selected_team_name: Optional[str] = None
        self.cards: List[TeamSelectCardWidget] = []

        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel#HeaderTitle {
                color: #e8f5e9;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 28px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QLabel#HeaderSubtitle {
                color: #81c784;
                font-size: 14px;
            }
            QPushButton#BackButton {
                background-color: #111c15;
                border: 1px solid #2d6a4f;
                border-radius: 6px;
                color: #e8f5e9;
                padding: 8px 18px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#BackButton:hover {
                background-color: #1e3f20;
                border: 1px solid #81c784;
            }
            QPushButton#ConfirmButton {
                background-color: #1b4328;
                border: 2px solid #81c784;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 36px;
            }
            QPushButton#ConfirmButton:hover {
                background-color: #2d6a4f;
                border: 2px solid #a5d6a7;
            }
            QPushButton#ConfirmButton:disabled {
                background-color: #111c15;
                border: 1px solid #1e3f20;
                color: #555555;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 25, 40, 25)
        main_layout.setSpacing(15)

        # Top Bar
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← Back to Menu")
        back_btn.setObjectName("BackButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_to_welcome.emit)
        top_bar.addWidget(back_btn)
        top_bar.addStretch(1)
        main_layout.addLayout(top_bar)

        header_title = QLabel("CHOOSE YOUR TEAM")
        header_title.setObjectName("HeaderTitle")
        main_layout.addWidget(header_title)

        header_subtitle = QLabel("Select the franchise you will manage for your baseball career")
        header_subtitle.setObjectName("HeaderSubtitle")
        main_layout.addWidget(header_subtitle)

        # Grid of Team Cards
        grid_container = QHBoxLayout()
        grid_container.addStretch(1)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        teams_data = get_teams_template_data()
        for idx, team_info in enumerate(teams_data):
            card = TeamSelectCardWidget(team_info)
            card.selected_signal.connect(self.on_team_card_selected)
            self.cards.append(card)
            row = idx // 3
            col = idx % 3
            grid_layout.addWidget(card, row, col)

        grid_container.addLayout(grid_layout)
        grid_container.addStretch(1)

        main_layout.addLayout(grid_container)
        main_layout.addStretch(1)

        # Bottom Confirm Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch(1)

        self.confirm_btn = QPushButton("SELECT A TEAM ABOVE")
        self.confirm_btn.setObjectName("ConfirmButton")
        self.confirm_btn.setDisabled(True)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.clicked.connect(self.on_confirm_clicked)
        bottom_bar.addWidget(self.confirm_btn)

        bottom_bar.addStretch(1)
        main_layout.addLayout(bottom_bar)

    def on_team_card_selected(self, team_name: str) -> None:
        self.selected_team_name = team_name
        for card in self.cards:
            card.set_selected(card.team_name == team_name)

        self.confirm_btn.setEnabled(True)
        self.confirm_btn.setText(f"START CAREER WITH {team_name.upper()}")

    def on_confirm_clicked(self) -> None:
        if self.selected_team_name:
            logger.info(f"Team selected: '{self.selected_team_name}'. Emitting team_chosen.")
            self.team_chosen.emit(self.selected_team_name)


# --- Home Screen Dashboard ---

class ActionTileWidget(QFrame):
    """Interactive / Disabled tile on Home Screen representing major game functions."""
    clicked = pyqtSignal()

    def __init__(self, icon: str, title: str, subtitle: str, enabled: bool = True, parent=None):
        super().__init__(parent)
        self.is_tile_enabled = enabled
        self.setFixedSize(220, 160)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        if enabled:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setStyleSheet("""
                ActionTileWidget {
                    background-color: #111c15;
                    border: 2px solid #1e3f20;
                    border-radius: 12px;
                }
                ActionTileWidget:hover {
                    background-color: #16261d;
                    border: 2px solid #81c784;
                }
                QLabel { background-color: transparent; }
                QLabel#TileIcon { font-size: 32px; qproperty-alignment: AlignCenter; }
                QLabel#TileTitle { color: #e8f5e9; font-family: 'Helvetica Neue', Arial; font-size: 16px; font-weight: bold; qproperty-alignment: AlignCenter; }
                QLabel#TileSubtitle { color: #81c784; font-size: 12px; qproperty-alignment: AlignCenter; }
            """)
        else:
            self.setStyleSheet("""
                ActionTileWidget {
                    background-color: #0d140e;
                    border: 1px dashed #1a2e20;
                    border-radius: 12px;
                }
                QLabel { background-color: transparent; }
                QLabel#TileIcon { font-size: 30px; opacity: 0.4; qproperty-alignment: AlignCenter; }
                QLabel#TileTitle { color: #556b5b; font-family: 'Helvetica Neue', Arial; font-size: 15px; font-weight: bold; qproperty-alignment: AlignCenter; }
                QLabel#TileSubtitle { color: #3a4d3f; font-size: 11px; font-style: italic; qproperty-alignment: AlignCenter; }
                QLabel#Badge { background-color: #16261b; color: #556b5b; border-radius: 6px; font-size: 10px; font-weight: bold; padding: 2px 8px; qproperty-alignment: AlignCenter; }
            """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setObjectName("TileIcon")
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setObjectName("TileTitle")
        layout.addWidget(title_label)

        sub_label = QLabel(subtitle)
        sub_label.setObjectName("TileSubtitle")
        layout.addWidget(sub_label)

        if not enabled:
            badge = QLabel("COMING SOON")
            badge.setObjectName("Badge")
            badge_container = QHBoxLayout()
            badge_container.addStretch(1)
            badge_container.addWidget(badge)
            badge_container.addStretch(1)
            layout.addLayout(badge_container)

        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:
        if self.is_tile_enabled and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


class HomeScreen(QWidget):
    """Central home dashboard screen displaying user's team status and main navigation tiles."""
    back_to_menu_requested = pyqtSignal()
    quit_game_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel {
                background-color: transparent;
            }
            QFrame#Banner {
                background-color: #111c15;
                border: 2px solid #1e3f20;
                border-radius: 12px;
            }
            QLabel#TeamTitle {
                color: #e8f5e9;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 32px;
                font-weight: 800;
            }
            QLabel#TeamMeta {
                color: #81c784;
                font-size: 14px;
            }
            QLabel#StatusBadge {
                background-color: #1b3823;
                border: 1px solid #2d6a4f;
                border-radius: 8px;
                color: #e8f5e9;
                font-size: 13px;
                font-weight: bold;
                padding: 6px 14px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # Header Team Banner
        self.banner = QFrame()
        self.banner.setObjectName("Banner")
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(24, 20, 24, 20)
        banner_layout.setSpacing(20)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(80, 80)
        banner_layout.addWidget(self.logo_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.team_title = QLabel("MY TEAM")
        self.team_title.setObjectName("TeamTitle")
        info_layout.addWidget(self.team_title)

        self.team_meta = QLabel("City, Nation  |  Stadium")
        self.team_meta.setObjectName("TeamMeta")
        info_layout.addWidget(self.team_meta)

        banner_layout.addLayout(info_layout)
        banner_layout.addStretch(1)

        self.status_badge = QLabel("Season 2026  |  April 1, 2026")
        self.status_badge.setObjectName("StatusBadge")
        banner_layout.addWidget(self.status_badge)

        main_layout.addWidget(self.banner)

        # Action Tiles Grid
        grid_container = QHBoxLayout()
        grid_container.addStretch(1)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        # 1. View Calendar (Disabled)
        calendar_tile = ActionTileWidget("📅", "View Calendar", "Schedule & Games", enabled=False)
        grid_layout.addWidget(calendar_tile, 0, 0)

        # 2. View Team (Disabled)
        team_tile = ActionTileWidget("⚾", "View Team", "Roster & Statistics", enabled=False)
        grid_layout.addWidget(team_tile, 0, 1)

        # 3. Market (Disabled)
        market_tile = ActionTileWidget("🛒", "Market", "Trades & Free Agency", enabled=False)
        grid_layout.addWidget(market_tile, 1, 0)

        # 4. Settings (Active)
        settings_tile = ActionTileWidget("⚙️", "Settings", "Options & Menu", enabled=True)
        settings_tile.clicked.connect(self.open_settings)
        grid_layout.addWidget(settings_tile, 1, 1)

        grid_container.addLayout(grid_layout)
        grid_container.addStretch(1)

        main_layout.addLayout(grid_container)
        main_layout.addStretch(1)

        self.reload_data()

    def reload_data(self) -> None:
        """Fetch active game status and populate team header banner."""
        status_info = get_active_game_status()
        if not status_info:
            return

        team_name = status_info["team_name"]
        self.team_title.setText(team_name)
        self.team_meta.setText(
            f"{status_info['city']}, {status_info['nation']}   |   Stadium: {status_info['stadium_name']}"
        )
        self.status_badge.setText(
            f"Season {status_info['season']}   |   {status_info['current_date']}"
        )

        logo_path = get_team_logo_path(team_name)
        if logo_path:
            pix = QPixmap(logo_path).scaled(
                80, 80,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.clear()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.main_menu_requested.connect(self.back_to_menu_requested.emit)
        dialog.exit_game_requested.connect(self.quit_game_requested.emit)
        dialog.exec()
