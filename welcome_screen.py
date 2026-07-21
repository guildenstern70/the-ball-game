#
# THE BALL GAME - Welcome Screen Module
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

import math
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QHBoxLayout
from loguru import logger
from database import Session, engine, Team, Player

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
        self.pitcher_mound = QPointF(self.cx, self.cy + 20)  # Center fieldward of home plate

    def update_animation(self) -> None:
        self.tick = (self.tick + 1) % 120
        self.update()  # Request repaint

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Solid black background fill for entire widget
        painter.fillRect(self.rect(), QColor("#000000"))
        
        # 2. Outfield Grass Arc (centered at Home Plate, radius = 240)
        R = 240
        outfield_rect = QRectF(self.home_plate.x() - R, self.home_plate.y() - R, 2 * R, 2 * R)
        painter.setBrush(QBrush(QColor("#1e3f20")))  # Deep grass green
        # Draw arc matching the 90 degree fair zone (between 45 and 135 degrees)
        # QPainter.drawPie takes angles in 1/16ths of a degree.
        painter.drawPie(outfield_rect, 45 * 16, 90 * 16)
        
        # 3. Dirt Infield Track (Circle enclosing the bases)
        painter.setBrush(QBrush(QColor("#8c6239")))  # Earth clay brown
        painter.drawEllipse(QPointF(self.cx, self.cy), 110, 110)
        
        # 4. Infield Grass Diamond (Connecting bases)
        infield_grass = QPolygonF([
            self.home_plate,
            self.first_base,
            self.second_base,
            self.third_base
        ])
        painter.setBrush(QBrush(QColor("#2d6a4f")))  # Slightly brighter infield grass green
        painter.drawPolygon(infield_grass)
        
        # 5. Foul lines & Baselines
        painter.setPen(QPen(QColor("#ffffff"), 2))
        # Draw Left Foul Line (extends past 3rd base)
        painter.drawLine(self.home_plate, QPointF(self.home_plate.x() - 170, self.home_plate.y() - 170))
        # Draw Right Foul Line (extends past 1st base)
        painter.drawLine(self.home_plate, QPointF(self.home_plate.x() + 170, self.home_plate.y() - 170))
        
        # Inner white baseline paths (dashed lines on the dirt)
        painter.setPen(QPen(QColor("#ffffff"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(self.home_plate, self.first_base)
        painter.drawLine(self.first_base, self.second_base)
        painter.drawLine(self.second_base, self.third_base)
        painter.drawLine(self.third_base, self.home_plate)
        
        # 6. Pitcher's Mound
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#a67c52")))  # Clay center
        painter.drawEllipse(self.pitcher_mound, 14, 14)
        painter.setPen(QPen(QColor("#ffffff"), 2))
        # Pitcher's plate (rubber)
        painter.drawLine(QPointF(self.pitcher_mound.x() - 5, self.pitcher_mound.y()), QPointF(self.pitcher_mound.x() + 5, self.pitcher_mound.y()))
        
        # 7. Bases
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(QBrush(QColor("#ffffff")))
        
        # Draw First, Second, Third bases as squares rotated 45 degrees
        for base in [self.first_base, self.second_base, self.third_base]:
            painter.save()
            painter.translate(base)
            painter.rotate(45)
            painter.drawRect(-5, -5, 10, 10)
            painter.restore()
            
        # Draw Home Plate as a pentagon pointing down
        hp_poly = QPolygonF([
            QPointF(self.home_plate.x(), self.home_plate.y()),
            QPointF(self.home_plate.x() - 6, self.home_plate.y() - 6),
            QPointF(self.home_plate.x() - 6, self.home_plate.y() - 12),
            QPointF(self.home_plate.x() + 6, self.home_plate.y() - 12),
            QPointF(self.home_plate.x() + 6, self.home_plate.y() - 6),
        ])
        painter.drawPolygon(hp_poly)
        
        # 8. Animation States
        # Ticks 0-20: Pitcher holds ball
        # Ticks 20-50: Pitching (moves from pitcher's mound to home plate)
        # Ticks 50-60: Swing & Hit! (bat swings, hit effect shows)
        # Ticks 60-95: Fly ball into outfield (size scales to simulate height)
        # Ticks 95-120: Reset/pause
        
        ball_pos = None
        ball_size = 6.0
        draw_bat = False
        bat_angle = 0.0
        draw_hit_flash = False
        
        if 0 <= self.tick < 20:
            # Ball at pitcher's hand
            ball_pos = self.pitcher_mound
            ball_size = 5.0
            
        elif 20 <= self.tick < 50:
            # Ball pitched from pitcher's mound towards home plate
            t = (self.tick - 20) / 30.0
            x = self.pitcher_mound.x()
            # Stop slightly above home plate point for the contact zone
            contact_y = self.home_plate.y() - 8
            y = self.pitcher_mound.y() + (contact_y - self.pitcher_mound.y()) * t
            ball_pos = QPointF(x, y)
            ball_size = 5.0
            
        elif 50 <= self.tick < 60:
            # Swing & Hit
            draw_bat = True
            t_bat = (self.tick - 50) / 10.0
            # Swing angle arc (from 140 to 320 degrees)
            bat_angle = 140.0 + 180.0 * t_bat
            
            ball_pos = QPointF(self.home_plate.x(), self.home_plate.y() - 8)
            ball_size = 5.0
            draw_hit_flash = True
            
        elif 60 <= self.tick < 95:
            # Fly ball!
            t = (self.tick - 60) / 35.0
            # Target outfield location: deep right-center field
            target_x = self.cx + 140
            target_y = self.cy - 120
            
            start_x = self.home_plate.x()
            start_y = self.home_plate.y() - 8
            
            x = start_x + (target_x - start_x) * t
            y = start_y + (target_y - start_y) * t
            ball_pos = QPointF(x, y)
            
            # Height simulation via parabolic scaling of ball size
            # height_factor peaks at 1.0 when t=0.5
            height_factor = 4.0 * t * (1.0 - t)
            ball_size = 5.0 + 10.0 * height_factor
            
        # Draw Bat
        if draw_bat:
            painter.save()
            painter.translate(self.home_plate.x(), self.home_plate.y() - 8)
            painter.rotate(bat_angle)
            painter.setPen(QPen(QColor("#d9a05b"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            # Draw bat line starting at pivot
            painter.drawLine(0, 0, 24, 0)
            painter.restore()
            
        # Draw Hit Flash
        if draw_hit_flash:
            flash_opacity = 1.0 - ((self.tick - 50) / 10.0)
            painter.setBrush(QBrush(QColor(255, 255, 150, int(255 * flash_opacity))))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(self.home_plate.x(), self.home_plate.y() - 8), 18, 18)
            
            # Render "CRACK!" text
            painter.setPen(QPen(QColor(255, 225, 100, int(255 * flash_opacity))))
            font = QFont("Impact", 13)
            painter.setFont(font)
            painter.drawText(int(self.home_plate.x()) - 24, int(self.home_plate.y()) - 22, "CRACK!")
            
        # Draw Ball
        if ball_pos is not None:
            painter.setPen(QPen(QColor("#b5b5b5"), 1))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(ball_pos, ball_size / 2.0, ball_size / 2.0)
            
            # Draw tiny red seams if the ball is large enough
            if ball_size > 8:
                painter.setPen(QPen(QColor("#cc0000"), 1))
                r_ball = ball_size / 2.0
                rect = QRectF(ball_pos.x() - r_ball, ball_pos.y() - r_ball, ball_size, ball_size)
                painter.drawArc(rect, 45 * 16, 90 * 16)
                painter.drawArc(rect, 225 * 16, 90 * 16)

class WelcomeScreen(QWidget):
    """Welcome screen widget containing the title, subtitle, and diamond animation."""
    started = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Black theme styling
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
        
        # Title
        self.title_label = QLabel("THE BALL GAME")
        self.title_label.setObjectName("TitleLabel")
        main_layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel("A tiny baseball simulator")
        self.subtitle_label.setObjectName("SubtitleLabel")
        main_layout.addWidget(self.subtitle_label)
        
        main_layout.addStretch(1)
        
        # Centered Animation Widget
        self.diamond_widget = BaseballDiamondWidget()
        diamond_container = QHBoxLayout()
        diamond_container.addStretch(1)
        diamond_container.addWidget(self.diamond_widget)
        diamond_container.addStretch(1)
        main_layout.addLayout(diamond_container)
        
        main_layout.addStretch(1)
        
        # Prompt Label
        self.prompt_label = QLabel("HIT ANY KEY TO START")
        self.prompt_label.setObjectName("PromptLabel")
        main_layout.addWidget(self.prompt_label)
        
        # Setup Graphics Opacity Effect for pulsing
        self.opacity_effect = QGraphicsOpacityEffect(self.prompt_label)
        self.prompt_label.setGraphicsEffect(self.opacity_effect)
        
        # Opacity pulse timer
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_time = 0.0
        self.pulse_timer.start(50)  # ~20 ticks per second
        
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

class GameScreen(QWidget):
    """A simple placeholder game screen shown after transitioning."""
    back_to_menu = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel#HeaderLabel {
                color: #e8f5e9;
                font-family: 'Montserrat', Arial, sans-serif;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#InfoLabel {
                color: #a5d6a7;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QFrame#StatsCard {
                background-color: #111c15;
                border: 1px solid #1e3f20;
                border-radius: 12px;
                padding: 15px;
            }
            QLabel#CardTitle {
                color: #81c784;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#CardText {
                color: #ffffff;
                font-size: 14px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Header
        header = QLabel("THE BALL GAME - SIMULATOR LOADED")
        header.setObjectName("HeaderLabel")
        main_layout.addWidget(header)
        
        # Load stats from DB to show connection works
        team_count = 0
        player_count = 0
        try:
            with Session(engine) as session:
                team_count = session.query(Team).count()
                player_count = session.query(Player).count()
        except Exception as e:
            logger.error(f"Error loading DB stats: {e}")
            
        # Stats Card
        from PyQt6.QtWidgets import QFrame
        card = QFrame()
        card.setObjectName("StatsCard")
        card_layout = QVBoxLayout(card)
        
        card_title = QLabel("Database Statistics")
        card_title.setObjectName("CardTitle")
        card_layout.addWidget(card_title)
        card_layout.addSpacing(10)
        
        stats_text = f"Teams registered in league: {team_count}\nPlayers generated: {player_count}\n\nGame simulation logic initialized. Press ESC to return to Welcome Screen."
        card_text = QLabel(stats_text)
        card_text.setObjectName("CardText")
        card_layout.addWidget(card_text)
        
        main_layout.addWidget(card)
        
        # Instructions
        instructions = QLabel("Press ESC to return to the Welcome Screen.")
        instructions.setObjectName("InfoLabel")
        main_layout.addWidget(instructions)
        
        main_layout.addStretch(1)
        
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            logger.info("Escape key pressed. Returning to welcome screen...")
            self.back_to_menu.emit()
            event.accept()
        else:
            super().keyPressEvent(event)
