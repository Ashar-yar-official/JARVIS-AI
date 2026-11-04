
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame
)


class ConfirmationDialog(QDialog):

    def __init__(
        self,
        action,
        description,
        parent=None
    ):
        super().__init__(parent)

        self.approved = False

        self.setWindowTitle("JARVIS - Permission Required")
        self.setMinimumWidth(430)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background-color: #090909;
                color: #E8E0D3;
            }

            QLabel {
                background: transparent;
                color: #E8E0D3;
                font-family: Consolas;
            }

            QFrame#ConfirmationPanel {
                background-color: #151211;
                border: 1px solid #80552B;
                border-radius: 9px;
            }

            QPushButton {
                background-color: #171311;
                color: #FFD98A;
                border: 1px solid #80552B;
                border-radius: 6px;
                padding: 9px 18px;
                font-family: Consolas;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #352218;
                border: 1px solid #FFD98A;
            }

            QPushButton#RejectButton {
                color: #FF7770;
                border: 1px solid #A52B26;
            }

            QPushButton#RejectButton:hover {
                background-color: #351615;
                border: 1px solid #FF7770;
            }
        """)

        self.init_ui(action, description)

    def init_ui(self, action, description):

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        heading = QLabel("⚠  USER AUTHORIZATION REQUIRED")
        heading.setStyleSheet("""
            color: #E9AD45;
            font-size: 13px;
            font-weight: bold;
        """)

        root.addWidget(heading)

        panel = QFrame()
        panel.setObjectName("ConfirmationPanel")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(15, 15, 15, 15)
        panel_layout.setSpacing(10)

        action_label = QLabel("REQUESTED ACTION")
        action_label.setStyleSheet(
            "color: #8F8377; font-size: 9px;"
        )

        action_value = QLabel(str(action).upper())
        action_value.setStyleSheet("""
            color: #FFD98A;
            font-size: 15px;
            font-weight: bold;
        """)
        action_value.setWordWrap(True)

        description_label = QLabel("DESCRIPTION")
        description_label.setStyleSheet(
            "color: #8F8377; font-size: 9px;"
        )

        description_value = QLabel(str(description))
        description_value.setWordWrap(True)
        description_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        panel_layout.addWidget(action_label)
        panel_layout.addWidget(action_value)
        panel_layout.addSpacing(5)
        panel_layout.addWidget(description_label)
        panel_layout.addWidget(description_value)

        root.addWidget(panel)

        warning = QLabel(
            "JARVIS will not proceed unless you approve "
            "this operation."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "color: #E9AD45; font-size: 10px;"
        )

        root.addWidget(warning)

        buttons = QHBoxLayout()
        buttons.addStretch()

        reject_button = QPushButton("REJECT")
        reject_button.setObjectName("RejectButton")
        reject_button.clicked.connect(self.reject_action)

        approve_button = QPushButton("APPROVE")
        approve_button.clicked.connect(self.approve_action)

        buttons.addWidget(reject_button)
        buttons.addWidget(approve_button)

        root.addLayout(buttons)

    def approve_action(self):

        self.approved = True
        self.accept()

    def reject_action(self):

        self.approved = False
        self.reject()

    def closeEvent(self, event):

        self.approved = False
        super().closeEvent(event)

    @staticmethod
    def request_confirmation(
        action,
        description,
        parent=None
    ):

        dialog = ConfirmationDialog(
            action,
            description,
            parent
        )

        dialog.exec()

        return dialog.approved
