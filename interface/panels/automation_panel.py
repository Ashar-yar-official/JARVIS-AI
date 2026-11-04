
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QListWidget,
    QTextEdit,
    QCheckBox,
)


BG = "#10141C"
PANEL = "#191F2B"
GOLD = "#D6A84F"
TEXT = "#E8EAF0"
MUTED = "#929BAA"
GREEN = "#45D69A"
AMBER = "#E9AD45"


class AutomationPanel(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.automation_enabled = False
        self.selected_task = None

        self.setWindowTitle("JARVIS | Desktop Automation")
        self.resize(1000, 700)
        self.setMinimumSize(750, 550)

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

            QListWidget, QTextEdit {{
                background-color: {PANEL};
                color: {TEXT};
                border: 1px solid #343D4D;
                border-radius: 6px;
                padding: 8px;
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

            QPushButton#dangerButton {{
                background-color: #632E35;
                color: white;
                border: 1px solid #91434B;
            }}

            QCheckBox {{
                color: {TEXT};
                spacing: 8px;
            }}
        """)

        self.build_ui()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------

    def build_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        heading = QLabel("DESKTOP AUTOMATION")
        heading.setStyleSheet(
            f"color: {GOLD}; font-size: 21px; font-weight: bold;"
        )

        description = QLabel(
            "Manage approved desktop tasks and automation workflows."
        )
        description.setStyleSheet(f"color: {MUTED};")

        main_layout.addWidget(heading)
        main_layout.addWidget(description)

        # Automation status
        status_panel = QFrame()
        status_panel.setObjectName("panel")

        status_layout = QVBoxLayout(status_panel)

        status_heading = QLabel("AUTOMATION STATUS")
        status_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.status_label = QLabel(
            "AUTOMATION ENGINE NOT CONNECTED"
        )
        self.status_label.setStyleSheet(
            f"color: {AMBER}; font-weight: bold; font-size: 15px;"
        )

        self.status_description = QLabel(
            "The automation interface is ready. "
            "No desktop actions are currently being executed."
        )
        self.status_description.setWordWrap(True)
        self.status_description.setStyleSheet(f"color: {MUTED};")

        status_layout.addWidget(status_heading)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.status_description)

        main_layout.addWidget(status_panel)

        # Task selection
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        task_panel = QFrame()
        task_panel.setObjectName("panel")

        task_layout = QVBoxLayout(task_panel)

        task_heading = QLabel("AVAILABLE AUTOMATION TASKS")
        task_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.task_list = QListWidget()

        self.tasks = [
            {
                "name": "Open an application",
                "description": (
                    "Launch an application selected from the approved "
                    "application list."
                ),
                "risk": "Low, after application validation.",
            },
            {
                "name": "Open a folder",
                "description": (
                    "Open a selected folder in Windows File Explorer."
                ),
                "risk": "Low, after path validation.",
            },
            {
                "name": "Organise files",
                "description": (
                    "Move or copy selected files into approved folders."
                ),
                "risk": "Confirmation required before changes.",
            },
            {
                "name": "Window management",
                "description": (
                    "Manage application windows and their positions."
                ),
                "risk": "Low, subject to application compatibility.",
            },
            {
                "name": "Create a reminder",
                "description": (
                    "Prepare a local reminder for a specified time."
                ),
                "risk": "Requires reminder scheduling integration.",
            },
            {
                "name": "Multi-step workflow",
                "description": (
                    "Prepare a sequence of approved desktop actions."
                ),
                "risk": "Each sensitive action requires validation.",
            },
        ]

        for task in self.tasks:
            self.task_list.addItem(task["name"])

        task_layout.addWidget(task_heading)
        task_layout.addWidget(self.task_list)

        details_panel = QFrame()
        details_panel.setObjectName("panel")

        details_layout = QVBoxLayout(details_panel)

        details_heading = QLabel("TASK DETAILS")
        details_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.details_output = QTextEdit()
        self.details_output.setReadOnly(True)
        self.details_output.setPlaceholderText(
            "Select a task to view its details."
        )

        self.prepare_button = QPushButton("PREPARE TASK")
        self.prepare_button.setObjectName("goldButton")
        self.prepare_button.setEnabled(False)

        details_layout.addWidget(details_heading)
        details_layout.addWidget(self.details_output, 1)
        details_layout.addWidget(self.prepare_button)

        content_layout.addWidget(task_panel, 1)
        content_layout.addWidget(details_panel, 1)

        main_layout.addLayout(content_layout, 1)

        # Safety settings
        safety_panel = QFrame()
        safety_panel.setObjectName("panel")

        safety_layout = QVBoxLayout(safety_panel)

        safety_heading = QLabel("AUTOMATION SAFETY")
        safety_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.confirm_actions_check = QCheckBox(
            "Require confirmation before executing actions"
        )
        self.confirm_actions_check.setChecked(True)

        self.protect_sensitive_check = QCheckBox(
            "Protect sensitive system locations"
        )
        self.protect_sensitive_check.setChecked(True)
        self.protect_sensitive_check.setEnabled(False)

        self.log_actions_check = QCheckBox(
            "Record automation activity"
        )
        self.log_actions_check.setChecked(True)

        safety_layout.addWidget(safety_heading)
        safety_layout.addWidget(self.confirm_actions_check)
        safety_layout.addWidget(self.protect_sensitive_check)
        safety_layout.addWidget(self.log_actions_check)

        main_layout.addWidget(safety_panel)

        # Activity log
        log_heading = QLabel("ACTIVITY LOG")
        log_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(100)
        self.activity_log.setPlainText(
            "JARVIS automation interface initialised.\n"
            "No automation actions have been executed."
        )

        main_layout.addWidget(log_heading)
        main_layout.addWidget(self.activity_log)

        # Footer
        footer = QHBoxLayout()

        self.status_footer = QLabel(
            "Automation engine integration pending."
        )
        self.status_footer.setStyleSheet(f"color: {MUTED};")

        self.clear_log_button = QPushButton("CLEAR LOG")
        self.close_button = QPushButton("CLOSE")

        footer.addWidget(self.status_footer, 1)
        footer.addWidget(self.clear_log_button)
        footer.addWidget(self.close_button)

        main_layout.addLayout(footer)

        # Connections
        self.task_list.currentRowChanged.connect(
            self.select_task
        )

        self.prepare_button.clicked.connect(
            self.prepare_task
        )

        self.clear_log_button.clicked.connect(
            self.clear_log
        )

        self.close_button.clicked.connect(self.close)

    # -------------------------------------------------
    # Task selection
    # -------------------------------------------------

    def select_task(self, index):

        if index < 0 or index >= len(self.tasks):
            return

        self.selected_task = self.tasks[index]

        task = self.selected_task

        details = (
            f"TASK: {task['name']}\n\n"
            f"DESCRIPTION:\n{task['description']}\n\n"
            f"SAFETY:\n{task['risk']}\n\n"
            "STATUS: Not connected to the automation engine."
        )

        self.details_output.setPlainText(details)
        self.prepare_button.setEnabled(True)

    # -------------------------------------------------
    # Task preparation
    # -------------------------------------------------

    def prepare_task(self):

        if not self.selected_task:
            return

        task_name = self.selected_task["name"]

        self.status_footer.setText(
            f"Selected task: {task_name}"
        )

        self.status_description.setText(
            f"'{task_name}' is selected. "
            "The automation engine must be connected before execution."
        )

        self.add_log(
            f"Task selected for preparation: {task_name}"
        )

    # -------------------------------------------------
    # Activity log
    # -------------------------------------------------

    def add_log(self, message):

        if not self.log_actions_check.isChecked():
            return

        current_text = self.activity_log.toPlainText()

        if current_text:
            current_text += "\n"

        self.activity_log.setPlainText(
            current_text + str(message)
        )

        self.activity_log.moveCursor(
            self.activity_log.textCursor().MoveOperation.End
        )

    def clear_log(self):

        self.activity_log.clear()
        self.add_log("Activity log cleared.")

    # -------------------------------------------------
    # Cleanup
    # -------------------------------------------------

    def closeEvent(self, event):

        event.accept()
