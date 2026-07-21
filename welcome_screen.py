#
# THE BALL GAME - Welcome & Game Screen Module
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

import math
import os
from typing import List, Dict, Any
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsOpacityEffect,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QStackedWidget
)
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from loguru import logger
from database import Session, engine, Team, Player, Position

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
        self.setFixedSize(400, 400)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Animation state variables
        self.tick = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)  # ~33 FPS (approx 3.6s cycle of 120 ticks)
        
        # Dimensions and center point
        self.cx = 200
        self.cy = 220
        self.r = 100
        
        # Base coordinates
        self.home_plate = QPointF(self.cx, self.cy + self.r)
        self.first_base = QPointF(self.cx + self.r, self.cy)
        self.second_base = QPointF(self.cx, self.cy - self.r)
        self.third_base = QPointF(self.cx - self.r, self.cy)
        self.pitcher_mound = QPointF(self.cx, self.cy + 20)

    def update_animation(self) -> None:
        self.tick = (self.tick + 1) % 120
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Solid black background fill for entire widget
        painter.fillRect(self.rect(), QColor("#000000"))
        
        # 2. Outfield Grass Arc (centered at Home Plate, radius = 240)
        R = 240
        outfield_rect = QRectF(self.home_plate.x() - R, self.home_plate.y() - R, 2 * R, 2 * R)
        painter.setBrush(QBrush(QColor("#1e3f20")))
        painter.drawPie(outfield_rect, 45 * 16, 90 * 16)
        
        # 3. Dirt Infield Track
        painter.setBrush(QBrush(QColor("#8c6239")))
        painter.drawEllipse(QPointF(self.cx, self.cy), 110, 110)
        
        # 4. Infield Grass Diamond
        infield_grass = QPolygonF([
            self.home_plate,
            self.first_base,
            self.second_base,
            self.third_base
        ])
        painter.setBrush(QBrush(QColor("#2d6a4f")))
        painter.drawPolygon(infield_grass)
        
        # 5. Foul lines & Baselines
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawLine(self.home_plate, QPointF(self.home_plate.x() - 170, self.home_plate.y() - 170))
        painter.drawLine(self.home_plate, QPointF(self.home_plate.x() + 170, self.home_plate.y() - 170))
        
        painter.setPen(QPen(QColor("#ffffff"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(self.home_plate, self.first_base)
        painter.drawLine(self.first_base, self.second_base)
        painter.drawLine(self.second_base, self.third_base)
        painter.drawLine(self.third_base, self.home_plate)
        
        # 6. Pitcher's Mound
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#a67c52")))
        painter.drawEllipse(self.pitcher_mound, 14, 14)
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawLine(
            QPointF(self.pitcher_mound.x() - 5, self.pitcher_mound.y()),
            QPointF(self.pitcher_mound.x() + 5, self.pitcher_mound.y())
        )
        
        # 7. Bases
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(QBrush(QColor("#ffffff")))
        
        for base in [self.first_base, self.second_base, self.third_base]:
            painter.save()
            painter.translate(base)
            painter.rotate(45)
            painter.drawRect(-5, -5, 10, 10)
            painter.restore()
            
        hp_poly = QPolygonF([
            QPointF(self.home_plate.x(), self.home_plate.y()),
            QPointF(self.home_plate.x() - 6, self.home_plate.y() - 6),
            QPointF(self.home_plate.x() - 6, self.home_plate.y() - 12),
            QPointF(self.home_plate.x() + 6, self.home_plate.y() - 12),
            QPointF(self.home_plate.x() + 6, self.home_plate.y() - 6),
        ])
        painter.drawPolygon(hp_poly)
        
        # 8. Animation States
        ball_pos = None
        ball_size = 6.0
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
            target_x = self.cx + 140
            target_y = self.cy - 120
            
            start_x = self.home_plate.x()
            start_y = self.home_plate.y() - 8
            
            x = start_x + (target_x - start_x) * t
            y = start_y + (target_y - start_y) * t
            ball_pos = QPointF(x, y)
            
            height_factor = 4.0 * t * (1.0 - t)
            ball_size = 5.0 + 10.0 * height_factor
            
        if draw_bat:
            painter.save()
            painter.translate(self.home_plate.x(), self.home_plate.y() - 8)
            painter.rotate(bat_angle)
            painter.setPen(QPen(QColor("#d9a05b"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(0, 0, 24, 0)
            painter.restore()
            
        if draw_hit_flash:
            flash_opacity = 1.0 - ((self.tick - 50) / 10.0)
            painter.setBrush(QBrush(QColor(255, 255, 150, int(255 * flash_opacity))))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(self.home_plate.x(), self.home_plate.y() - 8), 18, 18)
            
            painter.setPen(QPen(QColor(255, 225, 100, int(255 * flash_opacity))))
            font = QFont("Impact", 13)
            painter.setFont(font)
            painter.drawText(int(self.home_plate.x()) - 24, int(self.home_plate.y()) - 22, "CRACK!")
            
        if ball_pos is not None:
            painter.setPen(QPen(QColor("#b5b5b5"), 1))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(ball_pos, ball_size / 2.0, ball_size / 2.0)
            
            if ball_size > 8:
                painter.setPen(QPen(QColor("#cc0000"), 1))
                r_ball = ball_size / 2.0
                rect = QRectF(ball_pos.x() - r_ball, ball_pos.y() - r_ball, ball_size, ball_size)
                painter.drawArc(rect, 45 * 16, 90 * 16)
                painter.drawArc(rect, 225 * 16, 90 * 16)

class WelcomeScreen(QWidget):
    """Welcome screen widget containing title, subtitle, animated field, and pulsing prompt."""
    started = pyqtSignal()
    
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
                font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif;
                font-size: 46px;
                font-weight: 800;
                letter-spacing: 2px;
                qproperty-alignment: AlignCenter;
            }
            QLabel#SubtitleLabel {
                color: #81c784;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 18px;
                font-style: italic;
                letter-spacing: 1px;
                qproperty-alignment: AlignCenter;
            }
            QLabel#PromptLabel {
                color: #a5d6a7;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 16px;
                font-weight: 500;
                letter-spacing: 3px;
                qproperty-alignment: AlignCenter;
                margin-top: 15px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(10)
        
        main_layout.addStretch(1)
        
        self.title_label = QLabel("THE BALL GAME")
        self.title_label.setObjectName("TitleLabel")
        main_layout.addWidget(self.title_label)
        
        self.subtitle_label = QLabel("A tiny baseball simulator")
        self.subtitle_label.setObjectName("SubtitleLabel")
        main_layout.addWidget(self.subtitle_label)
        
        main_layout.addStretch(1)
        
        self.diamond_widget = BaseballDiamondWidget()
        diamond_container = QHBoxLayout()
        diamond_container.addStretch(1)
        diamond_container.addWidget(self.diamond_widget)
        diamond_container.addStretch(1)
        main_layout.addLayout(diamond_container)
        
        main_layout.addStretch(1)
        
        self.prompt_label = QLabel("HIT ANY KEY TO START")
        self.prompt_label.setObjectName("PromptLabel")
        main_layout.addWidget(self.prompt_label)
        
        self.opacity_effect = QGraphicsOpacityEffect(self.prompt_label)
        self.prompt_label.setGraphicsEffect(self.opacity_effect)
        
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_time = 0.0
        self.pulse_timer.start(50)
        
        main_layout.addStretch(1)
        
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        
    def update_pulse(self) -> None:
        self.pulse_time += 0.08
        opacity = 0.25 + 0.75 * abs(math.sin(self.pulse_time))
        self.opacity_effect.setOpacity(opacity)
        
    def keyPressEvent(self, event) -> None:
        if not event.isAutoRepeat():
            logger.info("Key press detected on welcome screen. Transitioning...")
            self.started.emit()
            event.accept()
            
    def mousePressEvent(self, event) -> None:
        logger.info("Mouse click detected on welcome screen. Transitioning...")
        self.started.emit()
        event.accept()


class TeamCardWidget(QFrame):
    """Clickable card displaying a team's logo, name, city, stadium, and roster badge."""
    clicked = pyqtSignal(int)
    
    def __init__(self, team: Team, parent=None):
        super().__init__(parent)
        self.team_id = team.id
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(220, 230)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.setStyleSheet("""
            TeamCardWidget {
                background-color: #111c15;
                border: 2px solid #1e3f20;
                border-radius: 12px;
            }
            TeamCardWidget:hover {
                background-color: #16261d;
                border: 2px solid #81c784;
            }
            QLabel {
                background-color: transparent;
            }
            QLabel#TeamNameLabel {
                color: #e8f5e9;
                font-family: 'Montserrat', Arial, sans-serif;
                font-size: 15px;
                font-weight: bold;
                qproperty-alignment: AlignCenter;
            }
            QLabel#TeamMetaLabel {
                color: #81c784;
                font-family: Arial, sans-serif;
                font-size: 13px;
                qproperty-alignment: AlignCenter;
            }
            QLabel#StadiumLabel {
                color: #a5d6a7;
                font-family: Arial, sans-serif;
                font-size: 11px;
                font-style: italic;
                qproperty-alignment: AlignCenter;
            }
            QLabel#RosterBadge {
                background-color: #1b2e24;
                border: 1px solid #2d6a4f;
                border-radius: 10px;
                color: #e8f5e9;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 10px;
                qproperty-alignment: AlignCenter;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(4)
        
        # Logo Label
        logo_label = QLabel()
        logo_label.setFixedSize(64, 64)
        logo_path = get_team_logo_path(team.name)
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
        
        layout.addSpacing(2)
        
        name_label = QLabel(team.name)
        name_label.setObjectName("TeamNameLabel")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        meta_label = QLabel(f"{team.city}, {team.nation}")
        meta_label.setObjectName("TeamMetaLabel")
        layout.addWidget(meta_label)
        
        stadium_label = QLabel(f"🏟 {team.stadium_name}")
        stadium_label.setObjectName("StadiumLabel")
        layout.addWidget(stadium_label)
        
        layout.addStretch(1)
        
        roster_badge = QLabel("26 PLAYERS")
        roster_badge.setObjectName("RosterBadge")
        badge_container = QHBoxLayout()
        badge_container.addStretch(1)
        badge_container.addWidget(roster_badge)
        badge_container.addStretch(1)
        layout.addLayout(badge_container)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.team_id)
            event.accept()
        else:
            super().mousePressEvent(event)


class TeamBrowserView(QWidget):
    """Grid browser view displaying cards for all teams in the league."""
    team_selected = pyqtSignal(int)
    
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
            QLabel#HeaderTitle {
                color: #e8f5e9;
                font-family: 'Montserrat', Arial, sans-serif;
                font-size: 28px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QLabel#HeaderSubtitle {
                color: #81c784;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(15)
        
        header_title = QLabel("LEAGUE TEAMS")
        header_title.setObjectName("HeaderTitle")
        main_layout.addWidget(header_title)
        
        header_subtitle = QLabel("Click on a team card to inspect its active 26-player roster and physical stats")
        header_subtitle.setObjectName("HeaderSubtitle")
        main_layout.addWidget(header_subtitle)
        
        grid_container = QHBoxLayout()
        grid_container.addStretch(1)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        try:
            with Session(engine) as session:
                teams = session.query(Team).all()
                for idx, team in enumerate(teams):
                    card = TeamCardWidget(team)
                    card.clicked.connect(self.team_selected.emit)
                    row = idx // 3
                    col = idx % 3
                    grid_layout.addWidget(card, row, col)
        except Exception as e:
            logger.error(f"Error querying teams for browser: {e}")
            
        grid_container.addLayout(grid_layout)
        grid_container.addStretch(1)
        
        main_layout.addLayout(grid_container)
        main_layout.addStretch(1)


class TeamDetailView(QWidget):
    """Detailed view showing team header banner and 26-player roster table."""
    back_requested = pyqtSignal()
    
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
            QLabel#TeamNameHeader {
                color: #e8f5e9;
                font-family: 'Montserrat', Arial, sans-serif;
                font-size: 30px;
                font-weight: 800;
            }
            QLabel#TeamSubHeader {
                color: #81c784;
                font-size: 14px;
            }
            QTableWidget {
                background-color: #111c15;
                border: 1px solid #1e3f20;
                border-radius: 8px;
                gridline-color: #1e3f20;
                color: #ffffff;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #1b2e24;
                color: #81c784;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #1e3f20;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(35, 20, 35, 20)
        self.main_layout.setSpacing(12)
        
        # Top Bar
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← Back to Teams")
        back_btn.setObjectName("BackButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_requested.emit)
        top_bar.addWidget(back_btn)
        top_bar.addStretch(1)
        self.main_layout.addLayout(top_bar)
        
        # Banner Container
        self.banner_layout = QHBoxLayout()
        self.banner_layout.setSpacing(20)
        
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(80, 80)
        self.banner_layout.addWidget(self.logo_label)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        self.name_label = QLabel()
        self.name_label.setObjectName("TeamNameHeader")
        info_layout.addWidget(self.name_label)
        
        self.meta_label = QLabel()
        self.meta_label.setObjectName("TeamSubHeader")
        info_layout.addWidget(self.meta_label)
        
        self.banner_layout.addLayout(info_layout)
        self.banner_layout.addStretch(1)
        
        self.main_layout.addLayout(self.banner_layout)
        
        # Roster Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Player Name", "Preferred Position(s)", "Height", "Weight", "Speed Rating", "Power Rating"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        self.main_layout.addWidget(self.table)
        
    def load_team(self, team_id: int) -> None:
        """Load and render full team details and 26-player roster into the table."""
        with Session(engine) as session:
            team = session.scalar(
                select(Team)
                .where(Team.id == team_id)
                .options(joinedload(Team.players).joinedload(Player.preferred_positions))
            )
            if not team:
                return
                
            self.name_label.setText(team.name)
            self.meta_label.setText(
                f"{team.city}, {team.nation}  |  Stadium: {team.stadium_name}  |  Roster Size: {len(team.players)} Players"
            )
            
            logo_path = get_team_logo_path(team.name)
            if logo_path:
                pix = QPixmap(logo_path).scaled(
                    80, 80, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_label.setPixmap(pix)
            else:
                self.logo_label.clear()
                
            # Sort players: Pitchers first, then Position Players, then by surname
            players = list(team.players)
            pitchers = [p for p in players if any(pos.name == "Pitcher" for pos in p.preferred_positions)]
            pos_players = [p for p in players if p not in pitchers]
            
            pitchers.sort(key=lambda p: (p.surname, p.name))
            pos_players.sort(key=lambda p: (p.surname, p.name))
            
            all_sorted = pitchers + pos_players
            
            self.table.setRowCount(len(all_sorted))
            
            for row, p in enumerate(all_sorted):
                # Name
                name_item = QTableWidgetItem(f"{p.name} {p.surname}")
                name_item.setForeground(QColor("#e8f5e9"))
                
                # Positions
                pos_names = ", ".join(pos.name for pos in p.preferred_positions)
                pos_item = QTableWidgetItem(pos_names)
                if "Pitcher" in pos_names:
                    pos_item.setForeground(QColor("#81c784"))
                else:
                    pos_item.setForeground(QColor("#a5d6a7"))
                    
                attrs = p.physical_attributes or {}
                h_item = QTableWidgetItem(f"{attrs.get('height_cm', '-')} cm")
                w_item = QTableWidgetItem(f"{attrs.get('weight_kg', '-')} kg")
                s_item = QTableWidgetItem(str(attrs.get('speed', '-')))
                p_item = QTableWidgetItem(str(attrs.get('power', '-')))
                
                for col_idx, item in enumerate([name_item, pos_item, h_item, w_item, s_item, p_item]):
                    align = (
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter 
                        if col_idx == 0 
                        else Qt.AlignmentFlag.AlignCenter
                    )
                    item.setTextAlignment(align)
                    self.table.setItem(row, col_idx, item)


class GameScreen(QWidget):
    """Main game screen managing internal navigation between Team Browser and Team Detail views."""
    back_to_menu = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        self.browser_view = TeamBrowserView()
        self.detail_view = TeamDetailView()
        
        self.stack.addWidget(self.browser_view)
        self.stack.addWidget(self.detail_view)
        
        self.browser_view.team_selected.connect(self.show_team_detail)
        self.detail_view.back_requested.connect(self.show_team_browser)
        
    def show_team_detail(self, team_id: int) -> None:
        self.detail_view.load_team(team_id)
        self.stack.setCurrentWidget(self.detail_view)
        logger.info(f"Loaded details for team_id {team_id}")
        
    def show_team_browser(self) -> None:
        self.stack.setCurrentWidget(self.browser_view)
        logger.info("Returned to team browser view")
        
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            if self.stack.currentWidget() == self.detail_view:
                self.show_team_browser()
                event.accept()
            else:
                logger.info("Escape key pressed on team browser. Returning to welcome screen...")
                self.back_to_menu.emit()
                event.accept()
        else:
            super().keyPressEvent(event)
