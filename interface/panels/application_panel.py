
import os
import re
import winreg

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QTextEdit,
    QFrame,
    QMessageBox,
)


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


class ApplicationPanel(QDialog):

    REGISTRY_PATHS = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            winreg.KEY_WOW64_64KEY,
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            winreg.KEY_WOW64_32KEY,
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            0,
        ),
    ]

    def __init__(self, parent=None):

        super().__init__(parent)

        self.applications = []
        self.visible_applications = []
        self.selected_application = None

        self.setWindowTitle(
            "JARVIS | Application Management"
        )

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

            QLineEdit, QListWidget, QTextEdit {{
                background-color: {PANEL};
                color: {TEXT};
                border: 1px solid #343D4D;
                border-radius: 6px;
                padding: 8px;
            }}

            QListWidget::item {{
                padding: 9px;
                border-radius: 5px;
            }}

            QListWidget::item:selected {{
                background-color: #343D4D;
                color: {GOLD};
            }}

            QListWidget::item:hover {{
                background-color: #252D3B;
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

            QPushButton:disabled {{
                background-color: #252D3B;
                color: #707887;
                border-color: #303949;
            }}

            QPushButton#goldButton {{
                background-color: {GOLD};
                color: {BG};
                border: none;
            }}

            QPushButton#goldButton:hover {{
                background-color: #E7BD70;
            }}

            QTextEdit {{
                font-size: 12px;
            }}
        """)

        self.build_ui()
        self.load_applications()

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

    # =====================================================
    # MAIN UI
    # =====================================================

    def build_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            20, 18, 20, 18
        )

        main_layout.setSpacing(12)

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        heading = QLabel(
            "APPLICATION MANAGEMENT"
        )

        heading.setStyleSheet(f"""
            color: {GOLD};
            font-size: 21px;
            font-weight: bold;
        """)

        description = QLabel(
            "View, search and launch applications installed on Windows."
        )

        description.setStyleSheet(
            f"color: {MUTED}; font-size: 11px;"
        )

        main_layout.addWidget(heading)
        main_layout.addWidget(description)

        # -------------------------------------------------
        # SEARCH BAR
        # -------------------------------------------------

        search_layout = QHBoxLayout()
        search_layout.setSpacing(9)

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search applications by name..."
        )

        self.search_button = QPushButton(
            "SEARCH"
        )

        self.refresh_button = QPushButton(
            "REFRESH"
        )

        search_layout.addWidget(
            self.search_input, 1
        )

        search_layout.addWidget(
            self.search_button
        )

        search_layout.addWidget(
            self.refresh_button
        )

        main_layout.addLayout(search_layout)

        # -------------------------------------------------
        # CONTENT
        # -------------------------------------------------

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # Application list
        list_panel = QFrame()
        list_panel.setObjectName("panel")

        list_layout = QVBoxLayout(list_panel)

        list_layout.setContentsMargins(
            14, 12, 14, 12
        )

        list_layout.setSpacing(9)

        list_heading = self.create_section_title(
            "INSTALLED APPLICATIONS"
        )

        self.application_count = QLabel(
            "0 applications"
        )

        self.application_count.setStyleSheet(
            f"color: {MUTED}; font-size: 10px;"
        )

        self.application_list = QListWidget()

        list_layout.addWidget(list_heading)
        list_layout.addWidget(self.application_count)
        list_layout.addWidget(
            self.application_list, 1
        )

        # Details panel
        details_panel = QFrame()
        details_panel.setObjectName("panel")

        details_layout = QVBoxLayout(details_panel)

        details_layout.setContentsMargins(
            14, 12, 14, 12
        )

        details_layout.setSpacing(9)

        details_heading = self.create_section_title(
            "APPLICATION DETAILS"
        )

        self.details_output = QTextEdit()

        self.details_output.setReadOnly(True)

        self.details_output.setPlaceholderText(
            "Select an application to view its details."
        )

        self.launch_button = QPushButton(
            "LAUNCH APPLICATION"
        )

        self.launch_button.setObjectName(
            "goldButton"
        )

        self.launch_button.setEnabled(False)

        details_layout.addWidget(details_heading)
        details_layout.addWidget(
            self.details_output, 1
        )

        details_layout.addWidget(
            self.launch_button
        )

        content_layout.addWidget(
            list_panel, 3
        )

        content_layout.addWidget(
            details_panel, 2
        )

        main_layout.addLayout(
            content_layout, 1
        )

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        footer = QHBoxLayout()

        self.status_label = QLabel(
            "Initialising..."
        )

        self.status_label.setStyleSheet(
            f"color: {GREEN};"
        )

        self.close_button = QPushButton(
            "CLOSE"
        )

        footer.addWidget(
            self.status_label, 1
        )

        footer.addWidget(
            self.close_button
        )

        main_layout.addLayout(footer)

        # -------------------------------------------------
        # CONNECTIONS
        # -------------------------------------------------

        self.search_button.clicked.connect(
            self.search_applications
        )

        self.search_input.textChanged.connect(
            self.search_applications
        )

        self.search_input.returnPressed.connect(
            self.search_applications
        )

        self.refresh_button.clicked.connect(
            self.load_applications
        )

        self.application_list.currentRowChanged.connect(
            self.select_application
        )

        self.launch_button.clicked.connect(
            self.launch_application
        )

        self.close_button.clicked.connect(
            self.close
        )

    # =====================================================
    # REGISTRY READING
    # =====================================================

    def read_registry_value(
        self,
        key,
        value_name
    ):

        try:

            value, _ = winreg.QueryValueEx(
                key,
                value_name
            )

            return str(value).strip()

        except OSError:

            return ""

    def load_applications(self):

        self.refresh_button.setEnabled(False)
        self.search_button.setEnabled(False)

        self.applications = []
        self.visible_applications = []
        self.selected_application = None

        self.application_list.clear()
        self.details_output.clear()

        self.launch_button.setEnabled(False)

        seen_names = set()

        try:

            for root, registry_path, access_flag in self.REGISTRY_PATHS:

                access = (
                    winreg.KEY_READ | access_flag
                )

                try:

                    with winreg.OpenKey(
                        root,
                        registry_path,
                        0,
                        access
                    ) as registry_key:

                        index = 0

                        while True:

                            try:

                                subkey_name = winreg.EnumKey(
                                    registry_key,
                                    index
                                )

                                index += 1

                            except OSError:

                                break

                            try:

                                with winreg.OpenKey(
                                    registry_key,
                                    subkey_name,
                                    0,
                                    winreg.KEY_READ
                                ) as app_key:

                                    name = self.read_registry_value(
                                        app_key,
                                        "DisplayName"
                                    )

                                    if not name:
                                        continue

                                    normalised_name = (
                                        name.strip().lower()
                                    )

                                    if normalised_name in seen_names:
                                        continue

                                    seen_names.add(
                                        normalised_name
                                    )

                                    application = {
                                        "name": name,

                                        "version": self.read_registry_value(
                                            app_key,
                                            "DisplayVersion"
                                        ),

                                        "publisher": self.read_registry_value(
                                            app_key,
                                            "Publisher"
                                        ),

                                        "install_location": self.read_registry_value(
                                            app_key,
                                            "InstallLocation"
                                        ),

                                        "uninstall_string": self.read_registry_value(
                                            app_key,
                                            "UninstallString"
                                        ),

                                        "display_icon": self.read_registry_value(
                                            app_key,
                                            "DisplayIcon"
                                        ),

                                        "registry_key": subkey_name,
                                    }

                                    application["executable"] = (
                                        self.find_registered_executable(
                                            application
                                        )
                                    )

                                    self.applications.append(
                                        application
                                    )

                            except OSError:

                                continue

                except OSError:

                    continue

            self.applications.sort(
                key=lambda item: item["name"].lower()
            )

            self.search_input.clear()
            self.search_applications()

            self.status_label.setText(
                f"Found {len(self.applications)} registered application(s)."
            )

        except Exception as error:

            self.status_label.setText(
                "Unable to load applications."
            )

            QMessageBox.warning(
                self,
                "Application Management Error",
                str(error)
            )

        finally:

            self.refresh_button.setEnabled(True)
            self.search_button.setEnabled(True)

    # =====================================================
    # SAFE EXECUTABLE IDENTIFICATION
    # =====================================================

    def find_registered_executable(self, application):

        """
        Only use an executable explicitly registered
        in the application's DisplayIcon value.

        Do not search installation folders for the
        first EXE because it may be an updater,
        helper, or uninstaller.
        """

        display_icon = application.get(
            "display_icon", ""
        )

        if not display_icon:
            return None

        candidate = display_icon.strip()

        # Remove an optional icon index, such as:
        # "C:\\Program Files\\App\\app.exe",0
        if candidate.startswith('"'):

            closing_quote = candidate.find(
                '"', 1
            )

            if closing_quote == -1:
                return None

            candidate = candidate[1:closing_quote]

        else:

            candidate = re.sub(
                r",\s*-?\d+\s*$",
                "",
                candidate
            ).strip()

        candidate = os.path.expandvars(
            candidate
        )

        if not candidate.lower().endswith(".exe"):
            return None

        if not os.path.isfile(candidate):
            return None

        return os.path.abspath(candidate)

    # =====================================================
    # DISPLAY AND SEARCH
    # =====================================================

    def search_applications(self):

        query = (
            self.search_input.text()
            .strip()
            .lower()
        )

        if not query:

            filtered = self.applications.copy()

        else:

            filtered = [
                application
                for application in self.applications
                if query in application["name"].lower()
            ]

        self.display_applications(filtered)

    def display_applications(self, applications):

        self.application_list.clear()

        self.visible_applications = applications

        self.selected_application = None

        self.details_output.clear()

        self.launch_button.setEnabled(False)

        for application in applications:

            self.application_list.addItem(
                application["name"]
            )

        self.application_count.setText(
            f"{len(applications)} application(s) displayed"
        )

        if applications:

            self.status_label.setText(
                f"Displaying {len(applications)} application(s)."
            )

        else:

            self.status_label.setText(
                "No matching applications found."
            )

    # =====================================================
    # APPLICATION SELECTION
    # =====================================================

    def select_application(self, row):

        if row < 0 or row >= len(self.visible_applications):

            self.selected_application = None

            self.details_output.clear()

            self.launch_button.setEnabled(False)

            return

        application = self.visible_applications[row]

        self.selected_application = application

        executable = application.get(
            "executable"
        )

        if executable:

            launch_status = "Available"

        else:

            launch_status = (
                "Not identified - manual launch may be required"
            )

        details = (
            f"APPLICATION INFORMATION\n"
            f"{'=' * 35}\n\n"

            f"Name: {application['name']}\n\n"

            f"Version: "
            f"{application['version'] or 'Not available'}\n\n"

            f"Publisher: "
            f"{application['publisher'] or 'Not available'}\n\n"

            f"Installation Location:\n"
            f"{application['install_location'] or 'Not available'}\n\n"

            f"LAUNCH INFORMATION\n"
            f"{'=' * 35}\n\n"

            f"Launch Availability: {launch_status}\n\n"

            f"Executable:\n"
            f"{executable or 'Not identified'}\n\n"

            f"Uninstall Information: "
            f"{'Registered' if application['uninstall_string'] else 'Not available'}"
        )

        self.details_output.setPlainText(
            details
        )

        self.launch_button.setEnabled(
            bool(executable)
        )

        self.status_label.setText(
            f"Selected: {application['name']}"
        )

    # =====================================================
    # APPLICATION LAUNCH
    # =====================================================

    def launch_application(self):

        application = self.selected_application

        if not application:
            return

        executable = application.get(
            "executable"
        )

        if not executable:

            QMessageBox.information(
                self,
                "Launch Information",
                (
                    "JARVIS could not identify a registered "
                    "application executable.\n\n"
                    "Please launch this application through "
                    "the Windows Start menu."
                )
            )

            return

        # Recheck the executable before launching.
        if not os.path.isfile(executable):

            QMessageBox.warning(
                self,
                "Launch Error",
                "The registered executable no longer exists."
            )

            self.launch_button.setEnabled(False)

            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Launch",

            (
                f"Launch this application?\n\n"
                f"{application['name']}\n\n"
                f"{executable}"
            ),

            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,

            QMessageBox.StandardButton.No
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:

            os.startfile(executable)

            self.status_label.setText(
                f"Launch requested: {application['name']}"
            )

            self.status_label.setStyleSheet(
                f"color: {GREEN};"
            )

        except OSError as error:

            QMessageBox.warning(
                self,
                "Launch Error",
                str(error)
            )

            self.status_label.setText(
                "Application launch failed."
            )

            self.status_label.setStyleSheet(
                f"color: {RED};"
            )

    # =====================================================
    # CLEANUP
    # =====================================================

    def closeEvent(self, event):

        self.selected_application = None

        event.accept()
