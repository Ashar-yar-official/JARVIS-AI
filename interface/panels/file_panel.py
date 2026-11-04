
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QComboBox,
    QTextEdit,
    QMessageBox,
    QFileDialog,
)

from modules.file_manager import (
    get_available_drives,
    get_file_information,
    get_folder_size,
    search_files,
    copy_item,
    move_item,
    delete_item,
)


BG = "#10141C"
PANEL = "#191F2B"
GOLD = "#D6A84F"
TEXT = "#E8EAF0"
MUTED = "#929BAA"
GREEN = "#45D69A"
RED = "#E56B6F"


class FileStorageDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "JARVIS | File & Storage Management"
        )

        self.resize(1250, 760)
        self.setMinimumSize(950, 620)

        self.current_folder = os.path.expanduser(
            "~/Documents"
        )

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG};
                color: {TEXT};
            }}

            QLabel {{
                color: {TEXT};
                background: transparent;
            }}

            QLineEdit, QComboBox, QTextEdit {{
                background-color: {PANEL};
                color: {TEXT};
                border: 1px solid #343D4D;
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {GOLD};
                selection-color: #10141C;
            }}

            QPushButton {{
                background-color: #252D3B;
                color: {TEXT};
                border: 1px solid #3A4557;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: #343F51;
                border-color: {GOLD};
            }}

            QPushButton#goldButton {{
                background-color: {GOLD};
                color: #10141C;
                border: none;
            }}

            QPushButton#dangerButton {{
                background-color: #632E35;
                color: white;
                border: 1px solid #91434B;
            }}

            QFrame#panel {{
                background-color: {PANEL};
                border: 1px solid #303949;
                border-radius: 9px;
            }}
        """)

        self.build_ui()
        self.load_drives()

    # =================================================
    # USER INTERFACE
    # =================================================

    def build_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            18, 15, 18, 13
        )

        main_layout.setSpacing(10)

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        header = QHBoxLayout()

        heading_layout = QVBoxLayout()

        heading = QLabel(
            "FILE & STORAGE MANAGEMENT"
        )

        heading.setStyleSheet(
            f"color: {GOLD}; font-size: 20px; "
            "font-weight: bold;"
        )

        subtitle = QLabel(
            "Inspect, organize and manage your computer storage."
        )

        subtitle.setStyleSheet(
            f"color: {MUTED};"
        )

        heading_layout.addWidget(heading)
        heading_layout.addWidget(subtitle)

        header.addLayout(heading_layout)
        header.addStretch()

        self.refresh_button = QPushButton(
            "REFRESH DRIVES"
        )

        self.refresh_button.clicked.connect(
            self.load_drives
        )

        header.addWidget(self.refresh_button)

        main_layout.addLayout(header)

        # -------------------------------------------------
        # DRIVE SELECTION
        # -------------------------------------------------

        drive_panel = QFrame()
        drive_panel.setObjectName("panel")

        drive_layout = QHBoxLayout(drive_panel)

        drive_layout.addWidget(
            QLabel("AVAILABLE DRIVES")
        )

        self.drive_combo = QComboBox()

        self.drive_combo.setMinimumWidth(180)

        self.drive_combo.currentTextChanged.connect(
            self.change_drive
        )

        drive_layout.addWidget(
            self.drive_combo
        )

        drive_layout.addStretch()

        self.drive_status = QLabel(
            "Select a drive or enter a folder path."
        )

        self.drive_status.setStyleSheet(
            f"color: {MUTED};"
        )

        drive_layout.addWidget(
            self.drive_status
        )

        main_layout.addWidget(drive_panel)

        # -------------------------------------------------
        # MAIN TWO-COLUMN AREA
        # -------------------------------------------------

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # =================================================
        # LEFT COLUMN: INSPECTION AND SEARCH
        # =================================================

        left_panel = QFrame()
        left_panel.setObjectName("panel")

        left_layout = QVBoxLayout(left_panel)

        left_layout.setContentsMargins(
            13, 12, 13, 12
        )

        left_layout.setSpacing(9)

        left_title = QLabel(
            "FOLDER INSPECTION"
        )

        left_title.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        left_layout.addWidget(left_title)

        # Folder path

        self.folder_input = QLineEdit()

        self.folder_input.setText(
            self.current_folder
        )

        self.folder_input.setPlaceholderText(
            "Enter folder path..."
        )

        left_layout.addWidget(
            QLabel("FOLDER PATH")
        )

        left_layout.addWidget(
            self.folder_input
        )

        # Folder action buttons

        folder_buttons = QHBoxLayout()

        self.inspect_button = QPushButton(
            "INSPECT FOLDER"
        )

        self.size_button = QPushButton(
            "CALCULATE SIZE"
        )

        self.inspect_button.clicked.connect(
            self.inspect_folder
        )

        self.size_button.clicked.connect(
            self.calculate_folder_size
        )

        folder_buttons.addWidget(
            self.inspect_button
        )

        folder_buttons.addWidget(
            self.size_button
        )

        left_layout.addLayout(
            folder_buttons
        )

        # Search section

        search_title = QLabel(
            "FILE AND FOLDER SEARCH"
        )

        search_title.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        left_layout.addWidget(search_title)

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Enter a filename or folder name..."
        )

        left_layout.addWidget(
            self.search_input
        )

        search_buttons = QHBoxLayout()

        self.search_button = QPushButton(
            "SEARCH"
        )

        self.clear_search_button = QPushButton(
            "CLEAR SEARCH"
        )

        self.search_button.clicked.connect(
            self.search_files_and_folders
        )

        self.clear_search_button.clicked.connect(
            self.clear_search
        )

        search_buttons.addWidget(
            self.search_button
        )

        search_buttons.addWidget(
            self.clear_search_button
        )

        left_layout.addLayout(
            search_buttons
        )

        left_layout.addWidget(
            QLabel("SEARCH RESULTS")
        )

        self.search_results = QTextEdit()

        self.search_results.setReadOnly(True)

        left_layout.addWidget(
            self.search_results,
            1
        )

        content_layout.addWidget(
            left_panel,
            3
        )

        # =================================================
        # RIGHT COLUMN: FILE ORGANIZATION
        # =================================================

        right_panel = QFrame()
        right_panel.setObjectName("panel")

        right_layout = QVBoxLayout(right_panel)

        right_layout.setContentsMargins(
            13, 12, 13, 12
        )

        right_layout.setSpacing(9)

        right_title = QLabel(
            "FILE ORGANIZATION"
        )

        right_title.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        right_layout.addWidget(
            right_title
        )

        # Source

        right_layout.addWidget(
            QLabel("SOURCE FILE / FOLDER")
        )

        source_layout = QHBoxLayout()

        self.source_input = QLineEdit()

        self.source_input.setPlaceholderText(
            "Select source file or folder..."
        )

        self.source_browse_button = QPushButton(
            "BROWSE"
        )

        self.source_browse_button.clicked.connect(
            self.browse_source
        )

        source_layout.addWidget(
            self.source_input,
            1
        )

        source_layout.addWidget(
            self.source_browse_button
        )

        right_layout.addLayout(
            source_layout
        )

        # Destination

        right_layout.addWidget(
            QLabel("DESTINATION FOLDER")
        )

        destination_layout = QHBoxLayout()

        self.destination_input = QLineEdit()

        self.destination_input.setPlaceholderText(
            "Select destination folder..."
        )

        self.destination_browse_button = QPushButton(
            "BROWSE"
        )

        self.destination_browse_button.clicked.connect(
            self.browse_destination
        )

        destination_layout.addWidget(
            self.destination_input,
            1
        )

        destination_layout.addWidget(
            self.destination_browse_button
        )

        right_layout.addLayout(
            destination_layout
        )

        # Copy and move

        self.copy_button = QPushButton(
            "COPY ITEM"
        )

        self.copy_button.setObjectName(
            "goldButton"
        )

        self.move_button = QPushButton(
            "MOVE ITEM"
        )

        self.copy_button.clicked.connect(
            self.copy_item_operation
        )

        self.move_button.clicked.connect(
            self.move_item_operation
        )

        right_layout.addWidget(
            self.copy_button
        )

        right_layout.addWidget(
            self.move_button
        )

        # Delete

        right_layout.addSpacing(8)

        delete_title = QLabel(
            "PERMANENT DELETION"
        )

        delete_title.setStyleSheet(
            f"color: {RED}; font-weight: bold;"
        )

        right_layout.addWidget(
            delete_title
        )

        self.delete_button = QPushButton(
            "PERMANENTLY DELETE SOURCE"
        )

        self.delete_button.setObjectName(
            "dangerButton"
        )

        self.delete_button.clicked.connect(
            self.delete_source
        )

        right_layout.addWidget(
            self.delete_button
        )

        right_layout.addStretch()

        content_layout.addWidget(
            right_panel,
            2
        )

        main_layout.addLayout(
            content_layout,
            3
        )

        # -------------------------------------------------
        # RESULTS PANEL
        # -------------------------------------------------

        results_panel = QFrame()
        results_panel.setObjectName("panel")

        results_layout = QVBoxLayout(results_panel)

        results_layout.setContentsMargins(
            12, 9, 12, 9
        )

        results_title = QLabel(
            "OPERATION RESULTS"
        )

        results_title.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.results_output = QTextEdit()

        self.results_output.setReadOnly(True)
        self.results_output.setMinimumHeight(95)
        self.results_output.setMaximumHeight(145)

        results_layout.addWidget(
            results_title
        )

        results_layout.addWidget(
            self.results_output
        )

        main_layout.addWidget(
            results_panel
        )

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        footer = QHBoxLayout()

        self.status_label = QLabel(
            "SYSTEM READY"
        )

        self.status_label.setStyleSheet(
            f"color: {GREEN};"
        )

        self.close_button = QPushButton(
            "CLOSE"
        )

        self.close_button.setMinimumWidth(100)

        self.close_button.clicked.connect(
            self.close
        )

        footer.addWidget(
            self.status_label,
            1
        )

        footer.addWidget(
            self.close_button
        )

        main_layout.addLayout(
            footer
        )

    # =================================================
    # DRIVE MANAGEMENT
    # =================================================

    def load_drives(self):

        self.drive_combo.blockSignals(True)

        self.drive_combo.clear()

        try:

            drives = get_available_drives()

            for drive in drives:

                self.drive_combo.addItem(
                    str(drive)
                )

            if not drives:

                self.drive_status.setText(
                    "No drives detected."
                )

            else:

                self.drive_status.setText(
                    f"{len(drives)} drive(s) detected."
                )

        except Exception as error:

            self.show_error(
                "Drive Error",
                error
            )

        finally:

            self.drive_combo.blockSignals(False)

        if self.drive_combo.count() > 0:

            self.change_drive(
                self.drive_combo.currentText()
            )

    def change_drive(self, drive):

        if not drive:
            return

        if os.path.isdir(drive):

            self.folder_input.setText(drive)

            self.current_folder = drive

            self.set_status(
                f"Selected drive: {drive}"
            )

    # =================================================
    # FOLDER INSPECTION
    # =================================================

    def inspect_folder(self):

        path = self.folder_input.text().strip()

        if not path:

            self.show_error(
                "Folder Inspection",
                "Enter a folder path first."
            )

            return

        if not os.path.isdir(path):

            self.show_error(
                "Invalid Folder",
                "The selected folder does not exist."
            )

            return

        try:

            self.current_folder = os.path.abspath(path)

            information = get_file_information(
                self.current_folder
            )

            self.display_result(
                "FOLDER INSPECTION",
                information
            )

            self.set_status(
                "Folder inspection completed."
            )

        except Exception as error:

            self.show_error(
                "Inspection Error",
                error
            )

    def calculate_folder_size(self):

        path = self.folder_input.text().strip()

        if not path:

            self.show_error(
                "Folder Size",
                "Enter a folder path first."
            )

            return

        if not os.path.isdir(path):

            self.show_error(
                "Invalid Folder",
                "Select an existing folder."
            )

            return

        try:

            size = get_folder_size(path)

            self.display_result(
                "FOLDER SIZE",
                size
            )

            self.set_status(
                "Folder size calculation completed."
            )

        except Exception as error:

            self.show_error(
                "Folder Size Error",
                error
            )

    # =================================================
    # FILE SEARCH
    # =================================================

    def search_files_and_folders(self):

        root = self.folder_input.text().strip()

        query = self.search_input.text().strip()

        if not root or not os.path.isdir(root):

            self.show_error(
                "Search",
                "Enter a valid folder path before searching."
            )

            return

        if not query:

            self.show_error(
                "Search",
                "Enter a filename or folder name."
            )

            return

        self.search_results.clear()

        try:

            results = search_files(
                root,
                query
            )

            if not results:

                self.search_results.setPlainText(
                    "No matching files or folders found."
                )

            else:

                self.search_results.setPlainText(
                    "\n".join(
                        str(result)
                        for result in results
                    )
                )

            self.set_status(
                f"Search completed: {len(results)} result(s)."
            )

        except Exception as error:

            self.show_error(
                "Search Error",
                error
            )

    def clear_search(self):

        self.search_input.clear()
        self.search_results.clear()

        self.set_status(
            "Search results cleared."
        )

    # =================================================
    # SOURCE AND DESTINATION BROWSING
    # =================================================

    def browse_source(self):

        path = QFileDialog.getOpenFileName(
            self,
            "Select Source File"
        )[0]

        if path:

            self.source_input.setText(path)

            self.set_status(
                "Source file selected."
            )

    def browse_destination(self):

        path = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Folder"
        )

        if path:

            self.destination_input.setText(path)

            self.set_status(
                "Destination folder selected."
            )

    # =================================================
    # VALIDATE OPERATION PATHS
    # =================================================

    def get_operation_paths(self):

        source = self.source_input.text().strip()

        destination = self.destination_input.text().strip()

        if not source:

            self.show_error(
                "Missing Source",
                "Select a source file or folder."
            )

            return None

        if not os.path.exists(source):

            self.show_error(
                "Invalid Source",
                "The selected source does not exist."
            )

            return None

        if not destination:

            self.show_error(
                "Missing Destination",
                "Select a destination folder."
            )

            return None

        if not os.path.isdir(destination):

            self.show_error(
                "Invalid Destination",
                "The destination folder does not exist."
            )

            return None

        if os.path.normcase(
            os.path.abspath(source)
        ) == os.path.normcase(
            os.path.abspath(destination)
        ):

            self.show_error(
                "Invalid Destination",
                "Source and destination cannot be the same."
            )

            return None

        return source, destination

    # =================================================
    # COPY OPERATION
    # =================================================

    def copy_item_operation(self):

        paths = self.get_operation_paths()

        if not paths:
            return

        source, destination = paths

        answer = QMessageBox.question(
            self,
            "Confirm Copy",
            (
                "Copy this item?\n\n"
                f"SOURCE:\n{source}\n\n"
                f"DESTINATION:\n{destination}"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            result = copy_item(
                source,
                destination
            )

            self.display_result(
                "COPY OPERATION",
                result
            )

            self.set_status(
                "Copy operation completed."
            )

        except Exception as error:

            self.show_error(
                "Copy Error",
                error
            )

    # =================================================
    # MOVE OPERATION
    # =================================================

    def move_item_operation(self):

        paths = self.get_operation_paths()

        if not paths:
            return

        source, destination = paths

        answer = QMessageBox.question(
            self,
            "Confirm Move",
            (
                "Move this item?\n\n"
                f"SOURCE:\n{source}\n\n"
                f"DESTINATION:\n{destination}\n\n"
                "The source will no longer remain in its "
                "original location."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            result = move_item(
                source,
                destination
            )

            self.display_result(
                "MOVE OPERATION",
                result
            )

            self.set_status(
                "Move operation completed."
            )

            self.source_input.clear()

        except Exception as error:

            self.show_error(
                "Move Error",
                error
            )

    # =================================================
    # PERMANENT DELETION
    # =================================================

    def delete_source(self):

        source = self.source_input.text().strip()

        if not source:

            self.show_error(
                "Deletion",
                "Select a source file or folder first."
            )

            return

        if not os.path.exists(source):

            self.show_error(
                "Invalid Source",
                "The selected source does not exist."
            )

            return

        first_confirmation = QMessageBox.warning(
            self,
            "Permanent Deletion",
            (
                "You are about to permanently delete:\n\n"
                f"{source}\n\n"
                "This action cannot be undone.\n"
                "Continue?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if first_confirmation != QMessageBox.StandardButton.Yes:
            return

        second_confirmation = QMessageBox.warning(
            self,
            "Final Confirmation",
            (
                "FINAL CONFIRMATION\n\n"
                "Permanently delete the selected item?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if second_confirmation != QMessageBox.StandardButton.Yes:
            return

        try:

            result = delete_item(source)

            self.display_result(
                "PERMANENT DELETION",
                result
            )

            self.set_status(
                "Deletion operation completed."
            )

            self.source_input.clear()

        except Exception as error:

            self.show_error(
                "Deletion Error",
                error
            )

    # =================================================
    # RESULTS AND STATUS
    # =================================================

    def display_result(self, title, information):

        self.results_output.append(
            f"\n{'=' * 65}\n"
            f"{title}\n"
            f"{'=' * 65}"
        )

        if isinstance(information, dict):

            for key, value in information.items():

                self.results_output.append(
                    f"{key}: {value}"
                )

        elif isinstance(information, (list, tuple)):

            for item in information:

                self.results_output.append(
                    str(item)
                )

        else:

            self.results_output.append(
                str(information)
            )

        self.results_output.append("")

    def set_status(self, message):

        self.status_label.setText(
            str(message)
        )

    def show_error(self, title, message):

        QMessageBox.warning(
            self,
            title,
            str(message)
        )

        self.set_status(
            f"{title}: operation not completed."
        )
