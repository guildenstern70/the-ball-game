#
# THE BALL GAME - Welcome, Team Selection, & Home Screen Module
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

import math
import os
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsOpacityEffect,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QStackedWidget, QDialog, QListWidget, QListWidgetItem,
    QApplication
)
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from loguru import logger
from database import (
    Session, Team, Player, Position, GameStatus,
    get_save_files, get_most_recent_save, get_engine,
    get_teams_template_data, get_active_game_status
)


def get_team_logo_path(team_name: str) -> str:
    """Return the filesystem path for a team's logo image if it exists."""
    filename = team_name.lower().replace(" ", "_") + ".png"
    filepath = os.path.join("data", "logos", filename)
    if os.path.exists(filepath):
        return filepath
    return ""


class BaseballDiamondWidget(QWidget):
    """Custom QWidget that renders a styled baseball field with animations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 360)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Animation state variables
        self.tick = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)  # ~33 FPS
        
        # Dimensions and center point
        self.cx = 180
        self.cy = 200
        self.r = 90
        
        # Base coordinates
        self.home_plate = QPointF(self.cx, self.cy + self.r)
        self.first_base = QPointF(self.cx + self.r, self.cy)
        self.second_base = QPointF(self.cx, self.cy - self.r)
        self.third_base = QPointF(self.cx - self.r, self.cy)
        self.pitcher_mound = QPointF(self.cx, self.cy + 18)

    def update_animation(self) -> None:
        self.tick = (self.tick + 1) % 120
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Solid black background
        painter.fillRect(self.rect(), QColor("#000000"))
        
        # Outfield Grass Arc
        R = 220
        outfield_rect = QRectF(self.home_plate.x() - R, self.home_plate.y() - R, 2 * R, 2 * R)
        painter.setBrush(QBrush(QColor("#1e3f20")))
        painter.drawPie(outfield_rect, 45 * 16, 90 * 16)
        
        # Dirt Infield Track
        painter.setBrush(QBrush(QColor("#8c6239")))
        painter.drawEllipse(QPointF(self.cx, self.cy), 100, 100)
        
        # Infield Grass Diamond
        infield_grass = QPolygonF([
            self.home_plate,
            self.first_base,
            self.second_base,
            self.third_base
        ])
        painter.setBrush(QBrush(QColor("#2d6a4f")))
        painter.drawPolygon(infield_grass)
        
        # Foul lines & Baselines
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawLine(self.home_plate, QPointF(self.home_plate.x() - 150, self.home_plate.y() - 150))
        painter.drawLine(self.home_plate, QPointF(self.home_plate.x() + 150, self.home_plate.y() - 150))
        
        painter.setPen(QPen(QColor("#ffffff"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(self.home_plate, self.first_base)
        painter.drawLine(self.first_base, self.second_base)
        painter.drawLine(self.second_base, self.third_base)
        painter.drawLine(self.third_base, self.home_plate)
        
        # Pitcher's Mound
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#a67c52")))
        painter.drawEllipse(self.pitcher_mound, 12, 12)
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawLine(
            QPointF(self.pitcher_mound.x() - 4, self.pitcher_mound.y()),
            QPointF(self.pitcher_mound.x() + 4, self.pitcher_mound.y())
        )
        
        # Bases
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(QBrush(QColor("#ffffff")))
        
        for base in [self.first_base, self.second_base, self.third_base]:
            painter.save()
            painter.translate(base)
            painter.rotate(45)
            painter.drawRect(-4, -4, 8, 8)
            painter.restore()
            
        hp_poly = QPolygonF([
            QPointF(self.home_plate.x(), self.home_plate.y()),
            QPointF(self.home_plate.x() - 5, self.home_plate.y() - 5),
            QPointF(self.home_plate.x() - 5, self.home_plate.y() - 10),
            QPointF(self.home_plate.x() + 5, self.home_plate.y() - 10),
            QPointF(self.home_plate.x() + 5, self.home_plate.y() - 5),
        ])
        painter.drawPolygon(hp_poly)
        
        # Animation States
        ball_pos = None
        ball_size = 5.0
        draw_bat = False
        bat_angle = 0.0
        draw_hit_flash = False
        
        if 0 <= self.tick < 20:
            ball_pos = self.pitcher_mound
            ball_size = 5.0
            
        elif 20 <= self.tick < 50:
            t = (self.tick - 20) / 30.0
            x = self.pitcher_mound.x()
            contact_y = self.home_plate.y() - 8
            y = self.pitcher_mound.y() + (contact_y - self.pitcher_mound.y()) * t
            ball_pos = QPointF(x, y)
            ball_size = 5.0
            
        elif 50 <= self.tick < 60:
            draw_bat = True
            t_bat = (self.tick - 50) / 10.0
            bat_angle = 140.0 + 180.0 * t_bat
            ball_pos = QPointF(self.home_plate.x(), self.home_plate.y() - 8)
            ball_size = 5.0
            draw_hit_flash = True
            
        elif 60 <= self.tick < 95:
            t = (self.tick - 60) / 35.0
            target_x = self.cx + 120
            target_y = self.cy - 100
            
            start_x = self.home_plate.x()
            start_y = self.home_plate.y() - 8
            
            x = start_x + (target_x - start_x) * t
            y = start_y + (target_y - start_y) * t
            ball_pos = QPointF(x, y)
            
            height_factor = 4.0 * t * (1.0 - t)
            ball_size = 5.0 + 9.0 * height_factor
            
        if draw_bat:
            painter.save()
            painter.translate(self.home_plate.x(), self.home_plate.y() - 8)
            painter.rotate(bat_angle)
            painter.setPen(QPen(QColor("#d9a05b"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(0, 0, 22, 0)
            painter.restore()
            
        if draw_hit_flash:
            flash_opacity = 1.0 - ((self.tick - 50) / 10.0)
            painter.setBrush(QBrush(QColor(255, 255, 150, int(255 * flash_opacity))))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(self.home_plate.x(), self.home_plate.y() - 8), 16, 16)
            
            painter.setPen(QPen(QColor(255, 225, 100, int(255 * flash_opacity))))
            font = QFont("Impact", 12)
            painter.setFont(font)
            painter.drawText(int(self.home_plate.x()) - 22, int(self.home_plate.y()) - 20, "CRACK!")
            
        if ball_pos is not None:
            painter.setPen(QPen(QColor("#b5b5b5"), 1))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(ball_pos, ball_size / 2.0, ball_size / 2.0)
            
            if ball_size > 7:
                painter.setPen(QPen(QColor("#cc0000"), 1))
                r_ball = ball_size / 2.0
                rect = QRectF(ball_pos.x() - r_ball, ball_pos.y() - r_ball, ball_size, ball_size)
                painter.drawArc(rect, 45 * 16, 90 * 16)
                painter.drawArc(rect, 225 * 16, 90 * 16)


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


# --- Settings Dialog ---

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


# Maintain placeholder GameScreen for legacy views if needed
class TeamBrowserView(QWidget):
    team_selected = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)

class TeamDetailView(QWidget):
    back_requested = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)

class GameScreen(QWidget):
    back_to_menu = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
