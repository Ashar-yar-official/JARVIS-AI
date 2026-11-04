
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QProgressBar,
    QTextEdit,
)

from modules.system_monitor import get_system_information


# =========================================================
# THEME
# =========================================================

BG = "#10141C"
PANEL = "#191F2B"
GOLD = "#D6A84F"
TEXT = "#E8EAF0"
MUTED = "#929BAA"
GREEN = "#45D69A"
AMBER = "#E9AD45"
RED = "#E56B6F"


class MonitorPanel(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("JARVIS | System Monitoring")
        self.resize(1150, 720)
        self.setMinimumSize(1000, 620)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG};
                color: {TEXT};
            }}

            QLabel {{
                color: {TEXT};
                background: transparent;
            }}

            QFrame#panel {{
                background-color: {PANEL};
                border: 1px solid #303949;
                border-radius: 9px;
            }}

            QProgressBar {{
                background-color: #252D3B;
                border: none;
                border-radius: 5px;
                height: 10px;
                text-align: center;
            }}

            QProgressBar::chunk {{
                background-color: {GOLD};
                border-radius: 5px;
            }}

            QTextEdit {{
                background-color: {PANEL};
                color: {TEXT};
                border: 1px solid #343D4D;
                border-radius: 7px;
                padding: 10px;
                font-size: 12px;
            }}

            QPushButton {{
                background-color: {GOLD};
                color: {BG};
                border: none;
                border-radius: 6px;
                padding: 9px 15px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: #E7BD70;
            }}

            QPushButton:disabled {{
                background-color: #555B66;
                color: #AEB3BC;
            }}
        """)

        self.build_ui()

        # Automatic refresh every 2 seconds.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(2000)

        self.refresh_data()

    # =====================================================
    # UI HELPERS
    # =====================================================

    def create_section_title(self, text):

        label = QLabel(text)

        label.setStyleSheet(f"""
            color: {GOLD};
            font-size: 14px;
            font-weight: bold;
        """)

        return label

    def create_resource_card(self, title):

        card = QFrame()
        card.setObjectName("panel")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 13, 15, 13)
        layout.setSpacing(9)

        title_label = QLabel(title)

        title_label.setStyleSheet(f"""
            color: {MUTED};
            font-size: 11px;
            font-weight: bold;
        """)

        value_label = QLabel("--")

        value_label.setStyleSheet(f"""
            color: {GOLD};
            font-size: 27px;
            font-weight: bold;
        """)

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setTextVisible(False)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(progress)

        return card, value_label, progress

    # =====================================================
    # MAIN UI
    # =====================================================

    def build_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(12)

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        heading = QLabel("SYSTEM MONITORING")

        heading.setStyleSheet(f"""
            color: {GOLD};
            font-size: 21px;
            font-weight: bold;
        """)

        description = QLabel(
            "Live overview of your computer's hardware, "
            "resource consumption, and system activity."
        )

        description.setStyleSheet(
            f"color: {MUTED}; font-size: 11px;"
        )

        main_layout.addWidget(heading)
        main_layout.addWidget(description)

        # -------------------------------------------------
        # RESOURCE CARDS
        # -------------------------------------------------

        resource_grid = QGridLayout()
        resource_grid.setSpacing(12)

        self.cpu_card, self.cpu_value, self.cpu_bar = (
            self.create_resource_card("CPU USAGE")
        )

        self.ram_card, self.ram_value, self.ram_bar = (
            self.create_resource_card("MEMORY USAGE")
        )

        self.disk_card, self.disk_value, self.disk_bar = (
            self.create_resource_card("STORAGE USAGE")
        )

        self.battery_card, self.battery_value, self.battery_bar = (
            self.create_resource_card("BATTERY")
        )

        resource_grid.addWidget(self.cpu_card, 0, 0)
        resource_grid.addWidget(self.ram_card, 0, 1)
        resource_grid.addWidget(self.disk_card, 0, 2)
        resource_grid.addWidget(self.battery_card, 0, 3)

        main_layout.addLayout(resource_grid)

        # -------------------------------------------------
        # DETAILS AREA
        # -------------------------------------------------

        details_title = self.create_section_title(
            "LIVE SYSTEM INFORMATION"
        )

        main_layout.addWidget(details_title)

        details_layout = QHBoxLayout()
        details_layout.setSpacing(12)

        # System information
        system_frame = QFrame()
        system_frame.setObjectName("panel")

        system_layout = QVBoxLayout(system_frame)
        system_layout.setContentsMargins(14, 12, 14, 12)
        system_layout.setSpacing(8)

        system_heading = QLabel("HARDWARE & RESOURCE DETAILS")

        system_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.system_output = QTextEdit()
        self.system_output.setReadOnly(True)

        system_layout.addWidget(system_heading)
        system_layout.addWidget(self.system_output)

        # Network and process information
        activity_frame = QFrame()
        activity_frame.setObjectName("panel")

        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(14, 12, 14, 12)
        activity_layout.setSpacing(8)

        activity_heading = QLabel("NETWORK & SYSTEM ACTIVITY")

        activity_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.activity_output = QTextEdit()
        self.activity_output.setReadOnly(True)

        activity_layout.addWidget(activity_heading)
        activity_layout.addWidget(self.activity_output)

        details_layout.addWidget(system_frame, 1)
        details_layout.addWidget(activity_frame, 1)

        main_layout.addLayout(details_layout, 1)

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        footer = QHBoxLayout()

        self.status_label = QLabel(
            "● INITIALISING MONITOR"
        )

        self.status_label.setStyleSheet(
            f"color: {AMBER}; font-weight: bold;"
        )

        self.last_updated_label = QLabel(
            "Last updated: --"
        )

        self.last_updated_label.setStyleSheet(
            f"color: {MUTED}; font-size: 10px;"
        )

        self.refresh_button = QPushButton(
            "REFRESH NOW"
        )

        self.close_button = QPushButton(
            "CLOSE"
        )

        footer.addWidget(self.status_label)
        footer.addStretch()
        footer.addWidget(self.last_updated_label)
        footer.addWidget(self.refresh_button)
        footer.addWidget(self.close_button)

        main_layout.addLayout(footer)

        # -------------------------------------------------
        # BUTTON CONNECTIONS
        # -------------------------------------------------

        self.refresh_button.clicked.connect(
            self.refresh_data
        )

        self.close_button.clicked.connect(
            self.close
        )

    # =====================================================
    # DATA REFRESH
    # =====================================================

    def refresh_data(self):

        self.refresh_button.setEnabled(False)

        try:

            information = get_system_information()

            if not isinstance(information, dict):

                raise ValueError(
                    "System monitor returned an unexpected data format."
                )

            # ---------------------------------------------
            # CPU
            # ---------------------------------------------

            cpu = information.get("cpu_usage")

            self.update_resource(
                self.cpu_value,
                self.cpu_bar,
                cpu
            )

            # ---------------------------------------------
            # RAM
            # ---------------------------------------------

            ram = information.get("ram_percent")

            self.update_resource(
                self.ram_value,
                self.ram_bar,
                ram
            )

            # ---------------------------------------------
            # DISK
            # ---------------------------------------------

            disk = information.get("disk_percent")

            self.update_resource(
                self.disk_value,
                self.disk_bar,
                disk
            )

            # ---------------------------------------------
            # BATTERY
            # ---------------------------------------------

            battery = information.get("battery_percent")

            self.update_resource(
                self.battery_value,
                self.battery_bar,
                battery
            )

            # ---------------------------------------------
            # SYSTEM DETAILS
            # ---------------------------------------------

            self.system_output.setPlainText(
                self.format_system_details(information)
            )

            # ---------------------------------------------
            # NETWORK AND PROCESSES
            # ---------------------------------------------

            self.activity_output.setPlainText(
                self.format_activity_details(information)
            )

            # ---------------------------------------------
            # OVERALL STATUS
            # ---------------------------------------------

            self.update_system_status(
                information.get("system_status")
            )

            self.last_updated_label.setText(
                f"Last updated: {self.current_time()}"
            )

        except Exception as error:

            self.status_label.setText(
                "● MONITOR ERROR"
            )

            self.status_label.setStyleSheet(
                f"color: {RED}; font-weight: bold;"
            )

            self.system_output.setPlainText(
                "Unable to retrieve system information.\n\n"
                f"Error: {error}"
            )

        finally:

            self.refresh_button.setEnabled(True)

    # =====================================================
    # RESOURCE CARD UPDATE
    # =====================================================

    def update_resource(self, label, progress, value):

        if value is None:

            label.setText("N/A")
            progress.setValue(0)
            return

        try:

            numeric_value = float(value)

        except (TypeError, ValueError):

            label.setText("N/A")
            progress.setValue(0)
            return

        numeric_value = max(
            0.0,
            min(100.0, numeric_value)
        )

        label.setText(
            f"{numeric_value:.1f}%"
        )

        progress.setValue(
            int(numeric_value)
        )

        if numeric_value >= 90:

            color = RED

        elif numeric_value >= 75:

            color = AMBER

        else:

            color = GOLD

        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #252D3B;
                border: none;
                border-radius: 5px;
                height: 10px;
            }}

            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)

    # =====================================================
    # SYSTEM DETAILS FORMATTING
    # =====================================================

    def format_system_details(self, information):

        battery = information.get("battery_percent")
        battery_plugged = information.get("battery_plugged")

        if battery is None:

            battery_text = "Not available"

        else:

            battery_text = f"{battery}%"

        if battery_plugged is True:

            charging_text = "Connected to power"

        elif battery_plugged is False:

            charging_text = "Running on battery"

        else:

            charging_text = "Power status unavailable"

        lines = [
            "HARDWARE STATUS",
            "=" * 35,
            "",
            f"CPU Usage: {self.format_percentage(information.get('cpu_usage'))}",
            f"RAM Usage: {self.format_percentage(information.get('ram_percent'))}",
            f"Disk Usage: {self.format_percentage(information.get('disk_percent'))}",
            "",
            "BATTERY INFORMATION",
            "=" * 35,
            "",
            f"Battery Level: {battery_text}",
            f"Power Connection: {charging_text}",
        ]

        return "\n".join(lines)

    # =====================================================
    # NETWORK AND ACTIVITY FORMATTING
    # =====================================================

    def format_activity_details(self, information):

        sent_speed = information.get(
            "network_sent_speed_kbps"
        )

        received_speed = information.get(
            "network_received_speed_kbps"
        )

        processes = information.get(
            "running_processes"
        )

        lines = [
            "NETWORK ACTIVITY",
            "=" * 35,
            "",
            f"Upload Speed: {self.format_speed(sent_speed)}",
            f"Download Speed: {self.format_speed(received_speed)}",
            "",
            "PROCESS INFORMATION",
            "=" * 35,
            "",
            f"Running Processes: {processes if processes is not None else 'N/A'}",
            "",
            "MONITORING STATUS",
            "=" * 35,
            "",
            f"System Status: {information.get('system_status', 'UNKNOWN')}",
            "",
            "Monitoring updates automatically every 2 seconds."
        ]

        return "\n".join(lines)

    # =====================================================
    # VALUE FORMATTING
    # =====================================================

    def format_percentage(self, value):

        if value is None:
            return "N/A"

        try:
            return f"{float(value):.1f}%"

        except (TypeError, ValueError):
            return "N/A"

    def format_speed(self, value):

        if value is None:
            return "N/A"

        try:
            return f"{float(value):.2f} KB/s"

        except (TypeError, ValueError):
            return "N/A"

    # =====================================================
    # SYSTEM STATUS
    # =====================================================

    def update_system_status(self, status):

        if status is None:

            status = "UNKNOWN"

        status = str(status).upper()

        self.status_label.setText(
            f"● SYSTEM {status}"
        )

        if status in ("NORMAL", "HEALTHY", "GOOD"):

            color = GREEN

        elif status in ("WARNING", "MODERATE"):

            color = AMBER

        elif status in ("CRITICAL", "ERROR"):

            color = RED

        else:

            color = MUTED

        self.status_label.setStyleSheet(
            f"color: {color}; font-weight: bold;"
        )

    # =====================================================
    # TIME
    # =====================================================

    def current_time(self):

        from datetime import datetime

        return datetime.now().strftime(
            "%H:%M:%S"
        )

    # =====================================================
    # CLEANUP
    # =====================================================

    def closeEvent(self, event):

        if hasattr(self, "timer"):

            self.timer.stop()

        event.accept()
