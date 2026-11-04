
import subprocess
import platform
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTextEdit,
)


BG = "#10141C"
PANEL = "#191F2B"
GOLD = "#D6A84F"
TEXT = "#E8EAF0"
MUTED = "#929BAA"
GREEN = "#45D69A"
AMBER = "#E9AD45"
RED = "#E56B6F"


class SecurityPanel(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("JARVIS | Security & Privacy")
        self.resize(950, 720)
        self.setMinimumSize(750, 550)

        self.security_results = {}

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

            QTextEdit {{
                background-color: {PANEL};
                color: {TEXT};
                border: 1px solid #343D4D;
                border-radius: 7px;
                padding: 9px;
            }}

            QPushButton {{
                background-color: #252D3B;
                color: {TEXT};
                border: 1px solid #3A4557;
                border-radius: 6px;
                padding: 9px 14px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                border-color: {GOLD};
            }}

            QPushButton#goldButton {{
                background-color: {GOLD};
                color: {BG};
                border: none;
            }}
        """)

        self.build_ui()
        self.run_security_check()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------

    def build_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        heading = QLabel("SECURITY & PRIVACY ASSISTANCE")
        heading.setStyleSheet(
            f"color: {GOLD}; font-size: 21px; font-weight: bold;"
        )

        description = QLabel(
            "Review Windows security information and privacy recommendations."
        )
        description.setStyleSheet(f"color: {MUTED};")

        main_layout.addWidget(heading)
        main_layout.addWidget(description)

        # Security status
        status_panel = QFrame()
        status_panel.setObjectName("panel")

        status_layout = QVBoxLayout(status_panel)

        status_heading = QLabel("SECURITY OVERVIEW")
        status_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.overall_status = QLabel("CHECK NOT STARTED")
        self.overall_status.setStyleSheet(
            f"color: {AMBER}; font-size: 16px; font-weight: bold;"
        )

        self.last_checked = QLabel("Last checked: Not yet checked")
        self.last_checked.setStyleSheet(f"color: {MUTED};")

        status_layout.addWidget(status_heading)
        status_layout.addWidget(self.overall_status)
        status_layout.addWidget(self.last_checked)

        main_layout.addWidget(status_panel)

        # Security checks
        checks_panel = QFrame()
        checks_panel.setObjectName("panel")

        checks_layout = QVBoxLayout(checks_panel)

        checks_heading = QLabel("WINDOWS SECURITY CHECKS")
        checks_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.firewall_status = QLabel("Firewall: Not checked")
        self.antivirus_status = QLabel("Antivirus: Not checked")
        self.update_status = QLabel("Windows Update: Not checked")
        self.system_status = QLabel("Operating System: Not checked")

        checks_layout.addWidget(checks_heading)
        checks_layout.addWidget(self.firewall_status)
        checks_layout.addWidget(self.antivirus_status)
        checks_layout.addWidget(self.update_status)
        checks_layout.addWidget(self.system_status)

        main_layout.addWidget(checks_panel)

        # Recommendations
        recommendations_heading = QLabel("SECURITY RECOMMENDATIONS")
        recommendations_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.recommendations_output = QTextEdit()
        self.recommendations_output.setReadOnly(True)
        self.recommendations_output.setMaximumHeight(140)

        main_layout.addWidget(recommendations_heading)
        main_layout.addWidget(self.recommendations_output)

        # Activity log
        activity_heading = QLabel("SECURITY ACTIVITY")
        activity_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.activity_output = QTextEdit()
        self.activity_output.setReadOnly(True)
        self.activity_output.setMaximumHeight(100)

        main_layout.addWidget(activity_heading)
        main_layout.addWidget(self.activity_output)

        # Footer
        footer = QHBoxLayout()

        self.status_label = QLabel("Security monitor ready.")
        self.status_label.setStyleSheet(f"color: {GREEN};")

        self.refresh_button = QPushButton("RUN SECURITY CHECK")
        self.refresh_button.setObjectName("goldButton")

        self.close_button = QPushButton("CLOSE")

        footer.addWidget(self.status_label, 1)
        footer.addWidget(self.refresh_button)
        footer.addWidget(self.close_button)

        main_layout.addLayout(footer)

        self.refresh_button.clicked.connect(
            self.run_security_check
        )

        self.close_button.clicked.connect(self.close)

    # -------------------------------------------------
    # Safe command execution
    # -------------------------------------------------

    def run_powershell(self, command):

        try:

            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command
                ],
                capture_output=True,
                text=True,
                timeout=12,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0
                ),
                check=False
            )

            if result.returncode != 0:
                return None

            return result.stdout.strip()

        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            OSError
        ):
            return None

    # -------------------------------------------------
    # Security checks
    # -------------------------------------------------

    def check_firewall(self):

        command = (
            "Get-NetFirewallProfile | "
            "Select-Object -Property Name, Enabled | "
            "ConvertTo-Json -Compress"
        )

        output = self.run_powershell(command)

        if not output:
            return "Unable to determine firewall status."

        import json

        try:

            data = json.loads(output)

            if isinstance(data, dict):
                data = [data]

            profiles = []

            for profile in data:

                name = profile.get("Name", "Unknown")
                enabled = profile.get("Enabled", False)

                profiles.append(
                    f"{name}: {'Enabled' if enabled else 'Disabled'}"
                )

            if not profiles:
                return "No firewall profiles returned."

            return "; ".join(profiles)

        except (json.JSONDecodeError, AttributeError):
            return "Firewall information could not be interpreted."

    def check_antivirus(self):

        command = (
            "Get-MpComputerStatus | "
            "Select-Object -Property "
            "AntivirusEnabled, RealTimeProtectionEnabled, "
            "AntivirusSignatureLastUpdated | "
            "ConvertTo-Json -Compress"
        )

        output = self.run_powershell(command)

        if not output:
            return (
                "Microsoft Defender status unavailable. "
                "Another antivirus product may be installed."
            )

        import json

        try:

            data = json.loads(output)

            antivirus = data.get("AntivirusEnabled", False)
            realtime = data.get("RealTimeProtectionEnabled", False)
            updated = data.get(
                "AntivirusSignatureLastUpdated",
                "Unknown"
            )

            return (
                f"Antivirus: {'Enabled' if antivirus else 'Disabled'}; "
                f"Real-time protection: "
                f"{'Enabled' if realtime else 'Disabled'}; "
                f"Last signature update: {updated}"
            )

        except (json.JSONDecodeError, AttributeError):
            return "Antivirus information could not be interpreted."

    def check_windows_update(self):

        command = (
            "Get-Service -Name wuauserv | "
            "Select-Object -Property Status, StartType | "
            "ConvertTo-Json -Compress"
        )

        output = self.run_powershell(command)

        if not output:
            return "Windows Update service status unavailable."

        import json

        try:

            data = json.loads(output)

            return (
                f"Service: {data.get('Status', 'Unknown')}; "
                f"Startup type: {data.get('StartType', 'Unknown')}"
            )

        except (json.JSONDecodeError, AttributeError):
            return "Windows Update information could not be interpreted."

    def check_operating_system(self):

        return (
            f"{platform.system()} {platform.release()} "
            f"({platform.machine()})"
        )

    # -------------------------------------------------
    # Run checks
    # -------------------------------------------------

    def run_security_check(self):

        self.refresh_button.setEnabled(False)
        self.status_label.setText("Running security checks...")

        self.log_activity("Security check started.")

        try:

            self.security_results = {
                "firewall": self.check_firewall(),
                "antivirus": self.check_antivirus(),
                "updates": self.check_windows_update(),
                "operating_system": self.check_operating_system(),
            }

            self.display_results()

            self.last_checked.setText(
                "Last checked: "
                + datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            )

            self.status_label.setText(
                "Security checks completed."
            )

            self.log_activity("Security check completed.")

        except Exception as error:

            self.status_label.setText("Security check failed.")

            self.log_activity(
                f"Security check error: {error}"
            )

        finally:

            self.refresh_button.setEnabled(True)

    # -------------------------------------------------
    # Display
    # -------------------------------------------------

    def display_results(self):

        firewall = self.security_results.get("firewall", "")
        antivirus = self.security_results.get("antivirus", "")
        updates = self.security_results.get("updates", "")
        operating_system = self.security_results.get(
            "operating_system",
            "Unknown"
        )

        self.firewall_status.setText(
            f"Firewall: {firewall}"
        )

        self.antivirus_status.setText(
            f"Antivirus: {antivirus}"
        )

        self.update_status.setText(
            f"Windows Update: {updates}"
        )

        self.system_status.setText(
            f"Operating System: {operating_system}"
        )

        recommendations = []

        if "Disabled" in firewall:
            recommendations.append(
                "Review firewall profiles reported as disabled."
            )

        if "Disabled" in antivirus:
            recommendations.append(
                "Review antivirus or real-time protection status."
            )

        if "unavailable" in antivirus.lower():
            recommendations.append(
                "Verify protection using Windows Security or your "
                "installed antivirus application."
            )

        if "unavailable" in updates.lower():
            recommendations.append(
                "Check Windows Update manually in Windows Settings."
            )

        if not recommendations:
            recommendations.append(
                "Review the reported information and keep Windows "
                "and security definitions up to date."
            )

        self.recommendations_output.setPlainText(
            "\n\n".join(recommendations)
        )

        if (
            "Disabled" in firewall
            or "Disabled" in antivirus
        ):

            self.overall_status.setText(
                "REVIEW RECOMMENDED"
            )

            self.overall_status.setStyleSheet(
                f"color: {RED}; font-size: 16px; font-weight: bold;"
            )

        else:

            self.overall_status.setText(
                "CHECK RESULTS AVAILABLE"
            )

            self.overall_status.setStyleSheet(
                f"color: {GREEN}; font-size: 16px; font-weight: bold;"
            )

    # -------------------------------------------------
    # Activity log
    # -------------------------------------------------

    def log_activity(self, message):

        current = self.activity_output.toPlainText()

        timestamp = datetime.now().strftime("%H:%M:%S")

        if current:
            current += "\n"

        self.activity_output.setPlainText(
            current + f"[{timestamp}] {message}"
        )

        self.activity_output.moveCursor(
            self.activity_output.textCursor().MoveOperation.End
        )

    # -------------------------------------------------
    # Cleanup
    # -------------------------------------------------

    def closeEvent(self, event):

        event.accept()
