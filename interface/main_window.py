import math
import os
from datetime import datetime

from shiboken6 import isValid

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QFont,
    QRadialGradient,
    QFontDatabase,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QMessageBox,
    QGraphicsDropShadowEffect,
)

# =========================================================
# OPTIONAL SYSTEM MONITOR
# =========================================================

try:
    from modules.system_monitor import get_system_information
except Exception:
    get_system_information = None


# =========================================================
# DEPARTMENT IMPORTS
# =========================================================

from interface.panels.file_panel import FileStorageDialog
from interface.panels.repair_panel import RepairPanel
from interface.panels.monitor_panel import MonitorPanel
from interface.panels.application_panel import ApplicationPanel
from interface.panels.voice_panel import VoicePanel
from interface.panels.automation_panel import AutomationPanel
from interface.panels.memory_panel import MemoryPanel
from interface.panels.security_panel import SecurityPanel
from interface.panels.embedded_browser import EmbeddedBrowser


# =========================================================
# OBSIDIAN REACTOR THEME
# =========================================================

BG = "#080D12"
BG_SECONDARY = "#0B131B"
PANEL = "#101B25"
PANEL_LIGHT = "#142431"

CYAN = "#36D9F5"
CYAN_LIGHT = "#A4F4FF"
CYAN_DARK = "#167C96"

AMBER = "#E7A84B"
AMBER_LIGHT = "#FFD58B"

GREEN = "#4BE0A1"
RED = "#F06464"
VIOLET = "#A88BFF"

TEXT = "#E5F0F5"
MUTED = "#7F96A5"
DIM = "#526775"

BORDER = "#203744"
BORDER_BRIGHT = "#276174"


# =========================================================
# DASHBOARD SPACING
# =========================================================

ROOT_MARGIN_LEFT = 28
ROOT_MARGIN_TOP = 18
ROOT_MARGIN_RIGHT = 28
ROOT_MARGIN_BOTTOM = 12

ROOT_SECTION_GAP = 12
BODY_COLUMN_GAP = 20

PANEL_MARGIN_HORIZONTAL = 16
PANEL_MARGIN_VERTICAL = 14
PANEL_CONTENT_GAP = 11

DEPARTMENT_BUTTON_SIZE = 58
COMMAND_INPUT_HEIGHT = 36


# =========================================================
# FONT SYSTEM
# =========================================================

FONT_FILES = {
    "Cardot": "Cardot-lxq6q",
}

FONT_EXTENSIONS = (
    ".ttf",
    ".otf",
    ".TTF",
    ".OTF",
)

DEFAULT_FONT = "Segoe UI"

FONT_FALLBACKS = {
    "Cardot": DEFAULT_FONT,
}

LOADED_FONTS = {}


def load_project_fonts():

    font_directory = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets",
        "fonts"
    )

    loaded = {}

    for family, filename in FONT_FILES.items():

        font_path = None

        for extension in FONT_EXTENSIONS:

            candidate = os.path.join(
                font_directory,
                filename + extension
            )

            if os.path.exists(candidate):
                font_path = candidate
                break

        if font_path is None:

            print(
                f"Font not found: {family} "
                f"({filename}.ttf / {filename}.otf)"
            )

            continue

        try:

            font_id = QFontDatabase.addApplicationFont(
                font_path
            )

            if font_id >= 0:

                families = QFontDatabase.applicationFontFamilies(
                    font_id
                )

                if families:

                    loaded[family] = families[0]

                    print(
                        f"Font loaded: {family} -> {families[0]}"
                    )

                else:

                    print(
                        f"Font family unavailable: {family}"
                    )

            else:

                print(
                    f"Could not register font: {family}"
                )

        except Exception as error:

            print(
                f"Font loading error ({family}):",
                error
            )

    if "Cardot" not in loaded:

        print(
            "WARNING: Cardot font is unavailable. "
            "Using Segoe UI as fallback."
        )

    return loaded


def get_ui_font_family():
    return DEFAULT_FONT


def get_font(
    family,
    size=10,
    weight=QFont.Weight.Normal,
    letter_spacing=0
):

    if family == "Cardot":
        actual_family = LOADED_FONTS.get("Cardot", DEFAULT_FONT)
    else:
        actual_family = DEFAULT_FONT

    font = QFont(actual_family, size, weight)

    if letter_spacing:
        font.setLetterSpacing(
            QFont.SpacingType.AbsoluteSpacing,
            letter_spacing
        )

    return font


# =========================================================
# LABEL FACTORIES
# =========================================================

def make_label(
    text,
    size=10,
    color=TEXT,
    bold=False,
    font="Segoe UI",
    letter_spacing=0
):

    weight = (
        QFont.Weight.Bold
        if bold
        else QFont.Weight.Normal
    )

    label = QLabel(str(text))

    label.setFont(
        get_font(
            font,
            size,
            weight,
            letter_spacing
        )
    )

    label.setStyleSheet(
        f"color: {color}; background: transparent;"
    )

    return label


def make_telemetry_label(
    text,
    color=MUTED,
    size=10,
    bold=True,
    alignment=Qt.AlignmentFlag.AlignLeft
):

    label = make_label(
        text,
        size,
        color,
        bold,
        "Segoe UI"
    )

    label.setAlignment(alignment)
    label.setMinimumHeight(20)

    return label


# =========================================================
# STATUS COLORS
# =========================================================

def get_status_color(status):

    status = str(status).upper()

    if status in ("CRITICAL", "ERROR", "FAILED"):
        return RED

    if status in ("WARNING", "CAUTION"):
        return AMBER

    if status in ("NOMINAL", "NORMAL", "HEALTHY"):
        return GREEN

    return MUTED


# =========================================================
# GLOW EFFECT
# =========================================================

def add_glow(widget, color=CYAN, blur=18, opacity=0.35):

    effect = QGraphicsDropShadowEffect(widget)

    effect.setBlurRadius(blur)
    effect.setOffset(0, 0)

    glow_color = QColor(color)
    glow_color.setAlphaF(opacity)

    effect.setColor(glow_color)
    widget.setGraphicsEffect(effect)


# =========================================================
# SEPARATOR
# =========================================================

class HUDSeparator(QFrame):

    def __init__(self, vertical=False, parent=None):

        super().__init__(parent)

        if vertical:

            self.setFixedWidth(1)

            self.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Expanding
            )

        else:

            self.setFixedHeight(1)

            self.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed
            )

        self.setStyleSheet(
            f"background-color: {BORDER}; border: none;"
        )


# =========================================================
# HUD PANEL
# =========================================================

class HUDPanel(QFrame):

    def __init__(self, title="", parent=None):

        super().__init__(parent)

        self.setObjectName("HUDPanel")

        self.setStyleSheet("""
            QFrame#HUDPanel {
                background-color: #101B25;
                border: 1px solid #203744;
                border-radius: 12px;
            }
        """)

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(
            PANEL_MARGIN_HORIZONTAL,
            PANEL_MARGIN_VERTICAL,
            PANEL_MARGIN_HORIZONTAL,
            PANEL_MARGIN_VERTICAL
        )

        self.layout.setSpacing(PANEL_CONTENT_GAP)

        if title:

            title_label = make_label(
                title.upper(),
                10,
                CYAN_LIGHT,
                True,
                "Segoe UI"
            )

            self.layout.addWidget(title_label)


# =========================================================
# DEPARTMENT BUTTONS
# =========================================================

class GradientDepartmentButton(QPushButton):

    ICON_COLORS = {
        "FILE": CYAN,
        "REPAIR": AMBER,
        "MONITOR": CYAN,
        "APPLICATIONS": VIOLET,
        "VOICE": GREEN,
        "AUTOMATION": AMBER,
        "MEMORY": VIOLET,
        "SECURITY": CYAN,
    }

    ICON_SYMBOLS = {
        "FILE": "▤",
        "REPAIR": "⚒",
        "MONITOR": "⌁",
        "APPLICATIONS": "▦",
        "VOICE": "♫",
        "AUTOMATION": "⚙",
        "MEMORY": "◈",
        "SECURITY": "⬡",
    }

    def __init__(self, department, parent=None):

        super().__init__(parent)

        self.department = department
        self.hovered = False
        self.selected = False

        self.setFixedSize(
            DEPARTMENT_BUTTON_SIZE,
            DEPARTMENT_BUTTON_SIZE
        )

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(department)

        self.setAccessibleName(
            f"{department} department"
        )

        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)

    def enterEvent(self, event):

        self.hovered = True
        self.update()

        super().enterEvent(event)

    def leaveEvent(self, event):

        self.hovered = False
        self.update()

        super().leaveEvent(event)

    def set_selected(self, selected):

        self.selected = selected
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        try:

            rect = QRectF(4, 4, 50, 50)

            gradient = QRadialGradient(rect.center(), 36)

            if self.selected:

                gradient.setColorAt(0, QColor("#1A5263"))
                gradient.setColorAt(0.7, QColor("#102A37"))
                gradient.setColorAt(1, QColor(BG))

            elif self.hovered:

                gradient.setColorAt(0, QColor("#194052"))
                gradient.setColorAt(0.7, QColor("#142631"))
                gradient.setColorAt(1, QColor(BG))

            else:

                gradient.setColorAt(0, QColor("#152631"))
                gradient.setColorAt(0.7, QColor("#101A22"))
                gradient.setColorAt(1, QColor(BG))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawEllipse(rect)

            border_color = (
                CYAN_LIGHT
                if self.selected or self.hovered
                else BORDER_BRIGHT
            )

            painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.setPen(
                QPen(
                    QColor(border_color),
                    1.7 if self.hovered or self.selected else 1.0
                )
            )

            painter.drawEllipse(rect)

            if self.selected or self.hovered:

                painter.setPen(
                    QPen(QColor(54, 217, 245, 65), 1)
                )

                painter.drawEllipse(
                    QRectF(8, 8, 42, 42)
                )

            icon_color = self.ICON_COLORS.get(
                self.department,
                CYAN
            )

            symbol = self.ICON_SYMBOLS.get(
                self.department,
                "•"
            )

            painter.setPen(QColor(icon_color))

            painter.setFont(
                get_font(
                    "Segoe UI",
                    23,
                    QFont.Weight.Bold
                )
            )

            painter.drawText(
                QRectF(5, 5, 48, 48),
                Qt.AlignmentFlag.AlignCenter,
                symbol
            )

            if self.selected:

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(CYAN_LIGHT))

                painter.drawEllipse(
                    QRectF(48, 6, 5, 5)
                )

        finally:
            painter.end()


# =========================================================
# RESOURCE METRIC CARD
# =========================================================

class MetricCard(QFrame):

    def __init__(self, title, color=CYAN, parent=None):

        super().__init__(parent)

        self.title = title.upper()
        self.color = QColor(color)

        self.value = 0.0
        self.available = True

        self.setMinimumHeight(92)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.setObjectName("MetricCard")

        self.setStyleSheet("""
            QFrame#MetricCard {
                background-color: #0C1720;
                border: 1px solid #203744;
                border-radius: 11px;
            }
        """)

    def update_value(self, value):

        if value is None:

            self.available = False
            self.update()

            return

        try:
            numeric_value = float(value)

        except (TypeError, ValueError):

            self.available = False
            self.update()

            return

        self.available = True

        self.value = max(
            0.0,
            min(100.0, numeric_value)
        )

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        try:

            rect = QRectF(self.rect()).adjusted(
                1, 1, -1, -1
            )

            painter.setPen(
                QPen(QColor(BORDER), 1)
            )

            painter.setBrush(QColor("#0C1720"))

            painter.drawRoundedRect(
                rect,
                11,
                11
            )

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.color)

            painter.drawRoundedRect(
                QRectF(
                    rect.left() + 1,
                    rect.top() + 12,
                    3,
                    rect.height() - 24
                ),
                1.5,
                1.5
            )

            title_rect = QRectF(
                rect.left() + 16,
                rect.top() + 11,
                rect.width() - 32,
                22
            )

            painter.setPen(QColor(CYAN_LIGHT))

            painter.setFont(
                get_font(
                    "Segoe UI",
                    10,
                    QFont.Weight.Bold
                )
            )

            painter.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignLeft |
                Qt.AlignmentFlag.AlignVCenter,
                self.title
            )

            value_rect = QRectF(
                rect.left() + 16,
                rect.top() + 31,
                rect.width() - 32,
                30
            )

            painter.setPen(
                QColor(TEXT if self.available else MUTED)
            )

            painter.setFont(
                get_font(
                    "Segoe UI",
                    19,
                    QFont.Weight.Bold
                )
            )

            value_text = (
                f"{self.value:.0f}%"
                if self.available
                else "N/A"
            )

            painter.drawText(
                value_rect,
                Qt.AlignmentFlag.AlignLeft |
                Qt.AlignmentFlag.AlignVCenter,
                value_text
            )

            bar_rect = QRectF(
                rect.left() + 16,
                rect.bottom() - 18,
                rect.width() - 32,
                5
            )

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#263A47"))

            painter.drawRoundedRect(
                bar_rect,
                2.5,
                2.5
            )

            if self.available and self.value > 0:

                progress_width = (
                    bar_rect.width() *
                    self.value / 100.0
                )

                progress_rect = QRectF(
                    bar_rect.left(),
                    bar_rect.top(),
                    progress_width,
                    bar_rect.height()
                )

                painter.setBrush(self.color)

                painter.drawRoundedRect(
                    progress_rect,
                    2.5,
                    2.5
                )

        finally:
            painter.end()


# =========================================================
# ARC REACTOR
# =========================================================

class ReactorWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.angle = 0
        self.pulse = 0.0
        self.state = "IDLE"

        self.setMinimumSize(300, 300)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(33)

    def animate(self):

        self.angle = (self.angle + 1) % 360
        self.pulse += 0.045

        self.update()

    def set_state(self, state):

        self.state = str(state).upper()
        self.update()

    def get_state_color(self):

        if self.state == "LISTENING":
            return GREEN

        if self.state == "THINKING":
            return VIOLET

        if self.state == "EXECUTING":
            return AMBER

        if self.state == "ERROR":
            return RED

        return CYAN

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        try:

            cx = self.width() / 2
            cy = self.height() / 2

            radius = min(
                self.width(),
                self.height()
            ) * 0.39

            state_color = QColor(
                self.get_state_color()
            )

            if self.state == "LISTENING":

                glow = (
                    1.0 +
                    0.13 * math.sin(self.pulse * 3)
                )

            elif self.state == "THINKING":

                glow = (
                    1.0 +
                    0.10 * math.sin(self.pulse * 5)
                )

            elif self.state == "EXECUTING":

                glow = 1.12

            else:

                glow = (
                    1.0 +
                    0.035 * math.sin(self.pulse)
                )

            glow_gradient = QRadialGradient(
                QPointF(cx, cy),
                radius * 1.5
            )

            glow_color = QColor(state_color)
            glow_color.setAlpha(35)

            glow_gradient.setColorAt(0, glow_color)

            middle_color = QColor(state_color)
            middle_color.setAlpha(12)

            glow_gradient.setColorAt(0.65, middle_color)
            glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_gradient)

            painter.drawEllipse(
                QRectF(
                    cx - radius * 1.5,
                    cy - radius * 1.5,
                    radius * 3,
                    radius * 3
                )
            )

            painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.setPen(
                QPen(QColor("#294452"), 1.5)
            )

            painter.drawEllipse(
                QRectF(
                    cx - radius * 1.08,
                    cy - radius * 1.08,
                    radius * 2.16,
                    radius * 2.16
                )
            )

            ring_factors = [1.0, 0.87, 0.72, 0.57]

            for index, factor in enumerate(ring_factors):

                ring_radius = radius * factor

                color = (
                    QColor(state_color)
                    if index % 2 == 0
                    else QColor(AMBER)
                )

                color.setAlpha(
                    210 if index < 2 else 150
                )

                painter.setPen(
                    QPen(
                        color,
                        2 if index < 2 else 1.2
                    )
                )

                painter.save()
                painter.translate(cx, cy)

                direction = (
                    1 if index % 2 == 0 else -1
                )

                painter.rotate(
                    self.angle * direction * (index + 1)
                )

                ring_rect = QRectF(
                    -ring_radius,
                    -ring_radius,
                    ring_radius * 2,
                    ring_radius * 2
                )

                painter.drawArc(
                    ring_rect,
                    15 * 16,
                    290 * 16
                )

                marker_count = (
                    12 if index < 2 else 8
                )

                painter.setPen(
                    QPen(QColor(CYAN_LIGHT), 2)
                )

                for marker in range(marker_count):

                    painter.save()

                    painter.rotate(
                        marker * (360 / marker_count)
                    )

                    painter.drawLine(
                        QPointF(ring_radius - 4, 0),
                        QPointF(ring_radius + 5, 0)
                    )

                    painter.restore()

                painter.restore()

            painter.setPen(
                QPen(QColor(BORDER_BRIGHT), 1.5)
            )

            painter.setBrush(QColor("#101D27"))

            painter.drawEllipse(
                QRectF(
                    cx - radius * 0.48,
                    cy - radius * 0.48,
                    radius * 0.96,
                    radius * 0.96
                )
            )

            core_radius = radius * 0.34 * glow

            core_gradient = QRadialGradient(
                QPointF(
                    cx - core_radius * 0.2,
                    cy - core_radius * 0.2
                ),
                core_radius * 1.5
            )

            core_gradient.setColorAt(0, QColor("#E9FFFF"))
            core_gradient.setColorAt(0.28, QColor("#70E9FF"))
            core_gradient.setColorAt(0.58, QColor("#2099C0"))
            core_gradient.setColorAt(0.82, QColor("#12485F"))
            core_gradient.setColorAt(1, QColor("#07151F"))

            painter.setPen(
                QPen(QColor(CYAN_LIGHT), 1.5)
            )

            painter.setBrush(core_gradient)

            painter.drawEllipse(
                QRectF(
                    cx - core_radius,
                    cy - core_radius,
                    core_radius * 2,
                    core_radius * 2
                )
            )

            painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.setPen(
                QPen(QColor(AMBER_LIGHT), 1.2)
            )

            painter.drawEllipse(
                QRectF(
                    cx - core_radius * 0.58,
                    cy - core_radius * 0.58,
                    core_radius * 1.16,
                    core_radius * 1.16
                )
            )

            painter.setPen(Qt.PenStyle.NoPen)

            central_gradient = QRadialGradient(
                QPointF(cx, cy),
                core_radius * 0.5
            )

            central_gradient.setColorAt(0, QColor("#FFFFFF"))
            central_gradient.setColorAt(0.45, QColor(CYAN_LIGHT))
            central_gradient.setColorAt(1, QColor(AMBER))

            painter.setBrush(central_gradient)

            painter.drawEllipse(
                QRectF(
                    cx - core_radius * 0.18,
                    cy - core_radius * 0.18,
                    core_radius * 0.36,
                    core_radius * 0.36
                )
            )

        finally:
            painter.end()


# =========================================================
# MAIN WINDOW
# =========================================================

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        global LOADED_FONTS

        LOADED_FONTS = load_project_fonts()

        self.setWindowTitle(
            "J.A.R.V.I.S. | APEX COMMAND SYSTEM"
        )

        self.setMinimumSize(1150, 760)
        self.resize(1920, 1080)

        self.setWindowState(
            Qt.WindowState.WindowMaximized
        )

        self.department_dialogs = {}
        self.department_buttons = {}
        self.selected_department = None

        self.browser_is_open = False

        self.left_resource_wrapper = None
        self.right_resource_wrapper = None

        self.department_names = {
            "FILE": "File & Storage Management",
            "REPAIR": "Troubleshooting & Repair",
            "MONITOR": "System Monitoring",
            "APPLICATIONS": "Application Management",
            "VOICE": "Voice & Communication",
            "AUTOMATION": "Desktop Automation",
            "MEMORY": "Memory & Intelligence",
            "SECURITY": "Security & Privacy Assistance"
        }

        self.department_classes = {
            "FILE": FileStorageDialog,
            "REPAIR": RepairPanel,
            "MONITOR": MonitorPanel,
            "APPLICATIONS": ApplicationPanel,
            "VOICE": VoicePanel,
            "AUTOMATION": AutomationPanel,
            "MEMORY": MemoryPanel,
            "SECURITY": SecurityPanel
        }

        self.department_descriptions = {
            "FILE": (
                "Inspect drives, browse folders, search files, "
                "calculate storage usage and perform controlled "
                "copy, move and deletion operations."
            ),

            "REPAIR": (
                "Inspect system diagnostics, review detected "
                "problems and examine troubleshooting information."
            ),

            "MONITOR": (
                "View live system resource information, including "
                "processor, memory, storage and battery activity."
            ),

            "APPLICATIONS": (
                "Inspect installed applications and access "
                "approved application-management operations."
            ),

            "VOICE": (
                "Configure voice preferences, push-to-talk and "
                "the planned JARVIS wake-word interface."
            ),

            "AUTOMATION": (
                "Review available desktop automation tasks, "
                "approval controls and activity information."
            ),

            "MEMORY": (
                "Manage information and preferences that you "
                "explicitly approve JARVIS to remember."
            ),

            "SECURITY": (
                "Review Windows security information, privacy "
                "recommendations and security activity."
            )
        }

        self.apply_theme()
        self.init_ui()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_system)
        self.refresh_timer.start(2500)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.refresh_system()
        self.update_clock()

    # =====================================================
    # APPLICATION THEME
    # =====================================================

    def apply_theme(self):

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BG};
            }}

            QWidget {{
                color: {TEXT};
                font-family: "{DEFAULT_FONT}";
            }}

            QLineEdit {{
                background-color: #0C151D;
                color: {CYAN_LIGHT};
                border: 1px solid {BORDER};
                border-radius: 7px;
                padding: 6px 12px;
                selection-background-color: {CYAN_DARK};
                font-family: "{DEFAULT_FONT}";
                font-size: 10pt;
            }}

            QLineEdit:focus {{
                border: 1px solid {CYAN};
                background-color: #0E1C26;
            }}

            QPushButton {{
                background-color: #14232E;
                color: {CYAN_LIGHT};
                border: 1px solid {BORDER};
                border-radius: 7px;
                padding: 7px 12px;
                font-family: "{DEFAULT_FONT}";
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: #193441;
                border: 1px solid {CYAN};
            }}

            QPushButton:pressed {{
                background-color: #102631;
            }}

            QPushButton:disabled {{
                color: {DIM};
                border-color: #1A2932;
                background-color: #0C1319;
            }}

            QScrollBar:vertical {{
                background: {BG};
                width: 8px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background: #294958;
                border-radius: 4px;
                min-height: 25px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {CYAN_DARK};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    # =====================================================
    # MAIN UI
    # =====================================================

    def init_ui(self):

        central = QWidget()
        central.setObjectName("MainCentral")

        self.setCentralWidget(central)

        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        content = QWidget()
        content.setObjectName("DashboardContent")

        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        outer_layout.addWidget(content)

        root = QVBoxLayout(content)

        root.setContentsMargins(
            ROOT_MARGIN_LEFT,
            ROOT_MARGIN_TOP,
            ROOT_MARGIN_RIGHT,
            ROOT_MARGIN_BOTTOM
        )

        root.setSpacing(ROOT_SECTION_GAP)

        # =================================================
        # HEADER
        # =================================================

        header = QHBoxLayout()
        header.setSpacing(22)

        identity = QVBoxLayout()
        identity.setSpacing(3)

        self.identity_label = make_label(
            "J.A.R.V.I.S.",
            25,
            CYAN_LIGHT,
            True,
            "Cardot"
        )

        identity.addWidget(self.identity_label)

        identity.addWidget(
            make_label(
                "APEX  /  PERSONAL INTELLIGENCE SYSTEM",
                9,
                MUTED,
                True,
                "Segoe UI"
            )
        )

        header.addLayout(identity)
        header.addSpacing(16)
        header.addWidget(HUDSeparator(vertical=True))

        status_column = QVBoxLayout()
        status_column.setSpacing(5)

        self.system_status = QPushButton("● INITIALIZING")

        self.system_status.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.system_status.clicked.connect(
            lambda: self.open_department("MONITOR")
        )

        self.system_status.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {AMBER};
                text-align: left;
                font-family: "{DEFAULT_FONT}";
                font-size: 11pt;
                font-weight: bold;
                padding: 0px;
            }}
        """)

        self.ai_status = make_label(
            "● AI OFFLINE",
            9,
            AMBER,
            True,
            "Segoe UI"
        )

        self.security_status = make_label(
            "● SECURITY ACTIVE",
            9,
            GREEN,
            True,
            "Segoe UI"
        )

        status_column.addWidget(self.system_status)
        status_column.addWidget(self.ai_status)
        status_column.addWidget(self.security_status)

        header.addLayout(status_column)
        header.addStretch()

        clock_layout = QVBoxLayout()
        clock_layout.setSpacing(3)

        self.clock_label = make_label(
            "-- : -- : --",
            21,
            CYAN_LIGHT,
            True,
            "Cardot"
        )

        self.clock_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        self.date_label = make_label(
            "LOADING DATE",
            9,
            MUTED,
            True,
            "Segoe UI"
        )

        self.date_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        clock_layout.addWidget(self.clock_label)
        clock_layout.addWidget(self.date_label)

        header.addLayout(clock_layout)

        root.addLayout(header)
        root.addWidget(HUDSeparator())

        # =================================================
        # MAIN DASHBOARD BODY
        # =================================================

        body = QHBoxLayout()
        body.setSpacing(BODY_COLUMN_GAP)

        # =================================================
        # LEFT DEPARTMENT COLUMN
        # =================================================

        department_column = QVBoxLayout()
        department_column.setSpacing(13)

        department_heading = make_label(
            "MODULES",
            9,
            MUTED,
            True,
            "Segoe UI"
        )

        department_heading.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        department_column.addWidget(department_heading)

        departments = [
            "FILE",
            "REPAIR",
            "MONITOR",
            "APPLICATIONS",
            "VOICE",
            "AUTOMATION",
            "MEMORY",
            "SECURITY"
        ]

        for key in departments:

            button = GradientDepartmentButton(key)

            button.clicked.connect(
                lambda checked=False, k=key:
                self.open_department(k)
            )

            self.department_buttons[key] = button

            department_column.addWidget(
                button,
                alignment=Qt.AlignmentFlag.AlignHCenter
            )

        department_column.addStretch()

        department_wrapper = QWidget()
        department_wrapper.setLayout(department_column)
        department_wrapper.setFixedWidth(70)

        body.addWidget(department_wrapper, 0)
        body.addWidget(HUDSeparator(vertical=True))

        # =================================================
        # CENTRAL DASHBOARD
        # =================================================

        dashboard = QVBoxLayout()
        dashboard.setSpacing(14)

        dashboard_header = QHBoxLayout()

        dashboard_header.addWidget(
            make_label(
                "SYSTEM INTELLIGENCE",
                12,
                TEXT,
                True,
                "Cardot"
            )
        )

        dashboard_header.addStretch()

        dashboard_header.addWidget(
            make_label(
                "LIVE TELEMETRY  /  APEX CORE",
                9,
                CYAN,
                True,
                "Segoe UI"
            )
        )

        dashboard.addLayout(dashboard_header)

        # =================================================
        # THREE-COLUMN ARRANGEMENT
        # =================================================

        core_layout = QHBoxLayout()
        core_layout.setSpacing(22)

        # =================================================
        # LEFT RESOURCE COLUMN
        # =================================================

        left_resources = QVBoxLayout()
        left_resources.setSpacing(17)
        left_resources.addStretch(1)

        left_resources.addWidget(
            make_label(
                "PROCESSING",
                9,
                MUTED,
                True,
                "Segoe UI"
            )
        )

        self.cpu_card = MetricCard("CPU USAGE", CYAN)
        self.ram_card = MetricCard("MEMORY USAGE", VIOLET)

        left_resources.addWidget(self.cpu_card)
        left_resources.addWidget(self.ram_card)
        left_resources.addSpacing(8)

        self.process_value = make_telemetry_label(
            "PROCESSES  /  --",
            CYAN_LIGHT,
            10
        )

        left_resources.addWidget(self.process_value)
        left_resources.addStretch(1)

        left_wrapper = QWidget()
        left_wrapper.setLayout(left_resources)

        self.left_resource_wrapper = left_wrapper

        core_layout.addWidget(left_wrapper, 2)

        # =================================================
        # CENTRAL REACTOR / BROWSER COLUMN
        # =================================================

        reactor_column = QVBoxLayout()
        reactor_column.setSpacing(10)
        reactor_column.addStretch(1)

        self.reactor_header = make_label(
            "INTELLIGENCE CORE",
            13,
            TEXT,
            True,
            "Cardot"
        )

        self.reactor_header.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        reactor_column.addWidget(self.reactor_header)

        self.reactor_separator = HUDSeparator()
        reactor_column.addWidget(self.reactor_separator)

        self.reactor = ReactorWidget()

        reactor_column.addWidget(
            self.reactor,
            1
        )

        self.embedded_browser = EmbeddedBrowser()

        self.embedded_browser.setMinimumSize(760, 500)

        self.embedded_browser.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.embedded_browser.close_requested.connect(
            self.close_embedded_browser
        )

        reactor_column.addWidget(
            self.embedded_browser,
            1
        )

        self.embedded_browser.hide()

        self.core_state_label = make_label(
            "REACTOR  /  STANDBY",
            10,
            CYAN,
            True,
            "Segoe UI"
        )

        self.core_state_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        reactor_column.addWidget(self.core_state_label)

        self.core_footer_label = make_label(
            "APEX ENERGY SYSTEM  /  ACTIVE MONITORING",
            8,
            DIM,
            True,
            "Segoe UI"
        )

        self.core_footer_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        reactor_column.addWidget(self.core_footer_label)
        reactor_column.addStretch(1)

        reactor_wrapper = QWidget()
        reactor_wrapper.setLayout(reactor_column)

        core_layout.addWidget(reactor_wrapper, 5)

        # =================================================
        # RIGHT RESOURCE COLUMN
        # =================================================

        right_resources = QVBoxLayout()
        right_resources.setSpacing(17)
        right_resources.addStretch(1)

        right_resources.addWidget(
            make_label(
                "SYSTEM RESOURCES",
                9,
                MUTED,
                True,
                "Segoe UI"
            )
        )

        self.disk_card = MetricCard("DISK USAGE", GREEN)
        self.battery_card = MetricCard("BATTERY LEVEL", AMBER)

        right_resources.addWidget(self.disk_card)
        right_resources.addWidget(self.battery_card)
        right_resources.addSpacing(8)

        self.network_title = make_telemetry_label(
            "NETWORK",
            CYAN_LIGHT,
            10
        )

        self.network_sent = make_telemetry_label(
            "↑ -- KB/s",
            GREEN,
            9
        )

        self.network_received = make_telemetry_label(
            "↓ -- KB/s",
            CYAN,
            9
        )

        right_resources.addWidget(self.network_title)

        network_row = QHBoxLayout()
        network_row.setSpacing(8)

        network_row.addWidget(self.network_sent)
        network_row.addWidget(self.network_received)

        right_resources.addLayout(network_row)
        right_resources.addStretch(1)

        right_wrapper = QWidget()
        right_wrapper.setLayout(right_resources)

        self.right_resource_wrapper = right_wrapper

        core_layout.addWidget(right_wrapper, 2)

        dashboard.addLayout(core_layout, 1)

        # =================================================
        # OPERATIONAL STATUS STRIP
        # =================================================

        operation_panel = HUDPanel()

        operation_panel.layout.setContentsMargins(
            14,
            9,
            14,
            9
        )

        operation_panel.layout.setSpacing(7)

        operation_row = QHBoxLayout()
        operation_row.setSpacing(16)

        self.reactor_state = make_label(
            "CORE STATUS  /  IDLE",
            10,
            GREEN,
            True,
            "Segoe UI"
        )

        operation_row.addWidget(self.reactor_state)
        operation_row.addWidget(HUDSeparator(vertical=True))

        self.task_status = make_label(
            "NO ACTIVE TASKS",
            10,
            CYAN_LIGHT,
            True,
            "Segoe UI"
        )

        operation_row.addWidget(self.task_status)
        operation_row.addStretch()

        self.task_description = make_label(
            "Waiting for an approved operation.",
            9,
            MUTED,
            False,
            "Segoe UI"
        )

        self.task_description.setMaximumWidth(420)

        operation_row.addWidget(self.task_description)

        self.automation_button = QPushButton("AUTOMATION  →")
        self.automation_button.setFixedHeight(32)

        self.automation_button.clicked.connect(
            lambda: self.open_department("AUTOMATION")
        )

        operation_row.addWidget(self.automation_button)

        operation_panel.layout.addLayout(operation_row)
        dashboard.addWidget(operation_panel)

        body.addLayout(dashboard, 1)

        # =================================================
        # IMPORTANT: ADD THE DASHBOARD BODY TO ROOT
        # =================================================
        # This was missing in the previous file.
        # Without this line, the modules, resource cards,
        # and central reactor are created but never displayed.

        root.addLayout(body, 1)

        # =================================================
        # DEPARTMENT INFORMATION PANEL
        # =================================================

        self.department_panel = HUDPanel(
            "DEPARTMENT INTELLIGENCE"
        )

        self.department_panel.layout.setContentsMargins(
            14,
            9,
            14,
            9
        )

        self.department_panel.layout.setSpacing(6)

        department_header = QHBoxLayout()
        department_header.setSpacing(12)

        self.department_title = make_label(
            "SELECT A DEPARTMENT",
            10,
            CYAN_LIGHT,
            True,
            "Cardot"
        )

        department_header.addWidget(self.department_title)
        department_header.addStretch()

        self.department_open_button = QPushButton("OPEN MODULE")

        self.department_open_button.setFixedSize(125, 30)

        self.department_open_button.clicked.connect(
            self.open_selected_department
        )

        close_button = QPushButton("✕")
        close_button.setFixedSize(32, 30)

        close_button.clicked.connect(self.close_department)

        department_header.addWidget(self.department_open_button)
        department_header.addWidget(close_button)

        self.department_panel.layout.addLayout(department_header)

        self.department_description = make_label(
            "Select a module to inspect its capabilities.",
            9,
            MUTED,
            False,
            "Segoe UI"
        )

        self.department_description.setWordWrap(True)

        self.department_panel.layout.addWidget(
            self.department_description
        )

        self.department_panel.hide()

        root.addWidget(self.department_panel)

        # =================================================
        # COMMAND INTERFACE
        # =================================================

        root.addWidget(HUDSeparator())

        command_header = QHBoxLayout()
        command_header.setSpacing(10)

        command_header.addWidget(
            make_label(
                "COMMAND INTERFACE",
                9,
                MUTED,
                True,
                "Segoe UI"
            )
        )

        command_header.addStretch()

        command_header.addWidget(
            make_label(
                "NATURAL LANGUAGE INPUT",
                8,
                DIM,
                True,
                "Segoe UI"
            )
        )

        root.addLayout(command_header)

        command_layout = QHBoxLayout()
        command_layout.setSpacing(10)

        command_prompt = make_label(
            "J.A.R.V.I.S.  >",
            10,
            CYAN,
            True,
            "Cardot"
        )

        command_layout.addWidget(command_prompt)

        self.command_input = QLineEdit()
        self.command_input.setFixedHeight(COMMAND_INPUT_HEIGHT)

        self.command_input.setPlaceholderText(
            "Enter a command or ask JARVIS..."
        )

        self.command_input.returnPressed.connect(
            self.send_command
        )

        self.mic_button = QPushButton("MIC")

        self.mic_button.setFixedSize(
            65,
            COMMAND_INPUT_HEIGHT
        )

        self.mic_button.clicked.connect(
            lambda: self.open_department("VOICE")
        )

        self.send_button = QPushButton("TRANSMIT  →")

        self.send_button.setFixedSize(
            125,
            COMMAND_INPUT_HEIGHT
        )

        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #123B49;
                color: {CYAN_LIGHT};
                border: 1px solid {CYAN_DARK};
                border-radius: 7px;
                padding: 5px 10px;
                font-family: "{DEFAULT_FONT}";
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: #185469;
                border: 1px solid {CYAN};
            }}
        """)

        self.send_button.clicked.connect(self.send_command)

        command_layout.addWidget(self.command_input, 1)
        command_layout.addWidget(self.mic_button)
        command_layout.addWidget(self.send_button)

        root.addLayout(command_layout)

        # =================================================
        # FOOTER
        # =================================================

        footer = QHBoxLayout()
        footer.setSpacing(10)

        footer.addWidget(
            make_label(
                "J.A.R.V.I.S.  /  APEX INTELLIGENCE",
                8,
                DIM,
                True,
                "Segoe UI"
            )
        )

        footer.addStretch()

        footer.addWidget(
            make_label(
                "LOCAL OPERATIONS",
                8,
                DIM,
                True,
                "Segoe UI"
            )
        )

        footer.addSpacing(14)

        self.footer_status = make_label(
            "● ONLINE",
            8,
            GREEN,
            True,
            "Segoe UI"
        )

        footer.addWidget(self.footer_status)

        root.addLayout(footer)

    # =====================================================
    # EMBEDDED BROWSER
    # =====================================================

    def show_embedded_browser(
        self,
        query=None,
        browser_type="google"
    ):

        try:

            self.browser_is_open = True

            if self.left_resource_wrapper is not None:
                self.left_resource_wrapper.hide()

            if self.right_resource_wrapper is not None:
                self.right_resource_wrapper.hide()

            self.reactor.hide()
            self.core_state_label.hide()
            self.core_footer_label.hide()

            self.embedded_browser.show()
            self.embedded_browser.raise_()

            self.reactor_header.setText(
                "JARVIS WEB INTERFACE"
            )

            self.reactor_header.show()
            self.reactor_separator.show()

            if browser_type == "google":

                self.embedded_browser.open_google_search(query)

                status_message = (
                    f"Searching the web for: {query}"
                )

            elif browser_type == "youtube":

                self.embedded_browser.open_youtube_search(query)

                status_message = (
                    f"Searching YouTube for: {query}"
                )

            elif browser_type == "url":

                self.embedded_browser.open_url(query)

                status_message = (
                    "Opening requested website."
                )

            else:

                self.close_embedded_browser()
                return False

            self.update_command_status(
                "BROWSER ACTIVE",
                status_message
            )

            self.reactor_state.setText(
                "CORE STATUS  /  WEB INTERFACE ACTIVE"
            )

            self.reactor_state.setStyleSheet(
                f"color: {CYAN}; background: transparent;"
            )

            return True

        except Exception as error:

            self.close_embedded_browser()

            print(
                "Embedded browser error:",
                error
            )

            self.update_command_status(
                "BROWSER ERROR",
                str(error)
            )

            return False

    def close_embedded_browser(self):

        if not self.browser_is_open:
            return

        self.browser_is_open = False

        self.embedded_browser.hide()

        if self.left_resource_wrapper is not None:
            self.left_resource_wrapper.show()

        if self.right_resource_wrapper is not None:
            self.right_resource_wrapper.show()

        self.reactor.show()
        self.core_state_label.show()
        self.core_footer_label.show()

        self.reactor_header.setText("INTELLIGENCE CORE")
        self.reactor_header.show()
        self.reactor_separator.show()

        self.set_core_status(
            "IDLE",
            "Reactor display restored."
        )

        self.update_command_status(
            "NO ACTIVE TASKS",
            "Waiting for an approved operation."
        )

    # =====================================================
    # OPEN DEPARTMENT
    # =====================================================

    def open_department(self, key):

        if key not in self.department_classes:

            QMessageBox.warning(
                self,
                "Department Not Found",
                f"Unknown department: {key}"
            )

            return

        panel_class = self.department_classes[key]

        existing_dialog = self.department_dialogs.get(key)

        try:

            if (
                existing_dialog is not None
                and isValid(existing_dialog)
                and existing_dialog.isVisible()
            ):

                existing_dialog.raise_()
                existing_dialog.activateWindow()

                return

        except RuntimeError:
            self.department_dialogs.pop(key, None)

        try:

            dialog = panel_class(self)

            self.department_dialogs[key] = dialog

            dialog.finished.connect(
                lambda result, k=key:
                self.clear_department_reference(k)
            )

            dialog.show()
            dialog.raise_()
            dialog.activateWindow()

        except Exception as error:

            self.department_dialogs.pop(key, None)

            QMessageBox.critical(
                self,
                "Department Error",
                (
                    f"Could not open {self.department_names[key]}.\n\n"
                    f"Details: {error}"
                )
            )

    # =====================================================
    # CLEAR DEPARTMENT REFERENCE
    # =====================================================

    def clear_department_reference(self, key):

        self.department_dialogs.pop(key, None)

    # =====================================================
    # DEPARTMENT INFORMATION
    # =====================================================

    def show_department(self, key):

        if key not in self.department_names:
            return

        self.selected_department = key

        for department_key, button in self.department_buttons.items():

            button.set_selected(
                department_key == key
            )

        self.department_panel.show()

        self.department_title.setText(
            self.department_names[key].upper()
        )

        self.department_description.setText(
            self.department_descriptions[key]
        )

    def open_selected_department(self):

        if self.selected_department:
            self.open_department(self.selected_department)

    def close_department(self):

        self.department_panel.hide()
        self.selected_department = None

        for button in self.department_buttons.values():
            button.set_selected(False)

    # =====================================================
    # CLOCK
    # =====================================================

    def update_clock(self):

        now = datetime.now()

        self.clock_label.setText(
            now.strftime("%H : %M : %S")
        )

        self.date_label.setText(
            now.strftime("%A  /  %d %B %Y").upper()
        )

    # =====================================================
    # SYSTEM MONITORING
    # =====================================================

    def refresh_system(self):

        if get_system_information is None:

            self.show_monitoring_error(
                "System monitoring module unavailable."
            )

            return

        try:

            info = get_system_information()

            cpu = info.get("cpu_usage")
            ram = info.get("ram_percent")
            disk = info.get("disk_percent")
            battery = info.get("battery_percent")

            self.cpu_card.update_value(cpu)
            self.ram_card.update_value(ram)
            self.disk_card.update_value(disk)
            self.battery_card.update_value(battery)

            self.process_value.setText(
                f"PROCESSES  /  "
                f"{info.get('running_processes', '--')}"
            )

            sent_speed = info.get(
                "network_sent_speed_kbps",
                0
            )

            received_speed = info.get(
                "network_received_speed_kbps",
                0
            )

            self.network_sent.setText(
                f"↑ {sent_speed:.1f} KB/s"
            )

            self.network_received.setText(
                f"↓ {received_speed:.1f} KB/s"
            )

            status = str(
                info.get("system_status", "UNKNOWN")
            ).upper()

            status_color = get_status_color(status)

            self.system_status.setText(
                f"● {status}"
            )

            self.system_status.setStyleSheet(f"""
                QPushButton {{
                    color: {status_color};
                    background: transparent;
                    border: none;
                    text-align: left;
                    font-family: "{DEFAULT_FONT}";
                    font-size: 11pt;
                    font-weight: bold;
                    padding: 0px;
                }}

                QPushButton:hover {{
                    color: {CYAN_LIGHT};
                }}
            """)

            self.hardware_status_update(
                status,
                status_color
            )

            self.footer_status.setText("● OPERATIONAL")

            self.footer_status.setStyleSheet(
                f"color: {GREEN}; background: transparent;"
            )

        except Exception as error:

            self.show_monitoring_error(str(error))

    # =====================================================
    # HARDWARE STATUS UPDATE
    # =====================================================

    def hardware_status_update(
        self,
        status,
        status_color
    ):

        self.system_status.setToolTip(
            f"System status: {status}"
        )

        self.footer_status.setToolTip(
            f"System status: {status}"
        )

    # =====================================================
    # MONITORING ERROR
    # =====================================================

    def show_monitoring_error(self, message):

        self.system_status.setText("● MONITOR ERROR")

        self.system_status.setStyleSheet(f"""
            QPushButton {{
                color: {RED};
                background: transparent;
                border: none;
                font-family: "{DEFAULT_FONT}";
            }}
        """)

        self.footer_status.setText("● MONITOR ERROR")

        self.footer_status.setStyleSheet(
            f"color: {RED}; background: transparent;"
        )

        print("System monitoring error:", message)

    # =====================================================
    # DASHBOARD COMMAND BAR
    # =====================================================

    def send_command(self):

        command = self.command_input.text().strip()

        if not command:
            return

        self.task_status.setText("COMMAND RECEIVED")

        self.task_description.setText(
            "Preparing AI request..."
        )

        self.command_input.clear()

        self.reactor.set_state("THINKING")

        self.reactor_state.setText(
            "CORE STATUS  /  PROCESSING REQUEST"
        )

        self.reactor_state.setStyleSheet(
            f"color: {VIOLET}; background: transparent;"
        )

        self.core_state_label.setText(
            "REACTOR  /  ANALYSING"
        )

        self.core_state_label.setStyleSheet(
            f"color: {VIOLET}; background: transparent;"
        )

    # =====================================================
    # COMMAND STATUS INTEGRATION
    # =====================================================

    def update_command_status(
        self,
        title,
        description
    ):

        self.task_status.setText(str(title))
        self.task_description.setText(str(description))

    # =====================================================
    # VOICE STATUS PLACEHOLDER
    # =====================================================

    def voice_placeholder(self):

        self.reactor.set_state("LISTENING")

        self.reactor_state.setText(
            "CORE STATUS  /  VOICE MODULE PENDING"
        )

        self.reactor_state.setStyleSheet(
            f"color: {AMBER}; background: transparent;"
        )

        self.core_state_label.setText(
            "REACTOR  /  LISTENING"
        )

        self.core_state_label.setStyleSheet(
            f"color: {GREEN}; background: transparent;"
        )

    # =====================================================
    # PUBLIC CORE STATUS UPDATE
    # =====================================================

    def set_core_status(
        self,
        state,
        message=None
    ):

        state = str(state).upper()

        self.reactor.set_state(state)

        self.core_state_label.setText(
            f"REACTOR  /  {state}"
        )

        color = self.reactor.get_state_color()

        self.core_state_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

        self.reactor_state.setText(
            f"CORE STATUS  /  {state}"
        )

        self.reactor_state.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

        if message:
            self.task_description.setText(str(message))

    # =====================================================
    # SAFE WINDOW CLOSING
    # =====================================================

    def closeEvent(self, event):

        # Stop dashboard timers safely.

        for timer_name in (
            "refresh_timer",
            "clock_timer"
        ):

            timer = getattr(
                self,
                timer_name,
                None
            )

            try:

                if timer is not None and isValid(timer):
                    timer.stop()

            except RuntimeError:
                pass

        # Stop reactor animation timer safely.

        reactor = getattr(
            self,
            "reactor",
            None
        )

        try:

            if reactor is not None and isValid(reactor):

                reactor_timer = getattr(
                    reactor,
                    "timer",
                    None
                )

                if (
                    reactor_timer is not None
                    and isValid(reactor_timer)
                ):

                    reactor_timer.stop()

        except RuntimeError:
            pass

        # Close department dialogs safely.

        for dialog in list(
            self.department_dialogs.values()
        ):

            try:

                if dialog is not None and isValid(dialog):
                    dialog.close()

            except RuntimeError as error:

                print(
                    "Department close error:",
                    error
                )

        event.accept()