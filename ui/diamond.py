#
# THE BALL GAME - Baseball Diamond Animation Widget
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
from PyQt6.QtWidgets import QWidget


class BaseballDiamondWidget(QWidget):
    """Custom QWidget that renders a styled baseball field with responsive vector scaling."""
    
    BASE_SIZE = 360.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 280)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Animation state variables
        self.tick = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)  # ~33 FPS
        
        # Base coordinates defined on 360x360 coordinate system
        self.cx = 180
        self.cy = 200
        self.r = 90
        
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
        
        # Solid black background fill
        painter.fillRect(self.rect(), QColor("#000000"))
        
        # Calculate dynamic scale factor based on widget width and height
        scale = min(self.width() / self.BASE_SIZE, self.height() / self.BASE_SIZE)
        
        # Center the coordinate system inside the widget bounding box
        tx = (self.width() - self.BASE_SIZE * scale) / 2.0
        ty = (self.height() - self.BASE_SIZE * scale) / 2.0
        
        painter.translate(tx, ty)
        painter.scale(scale, scale)
        
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
