
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QFrame,
)

from modules.system_diagnostics import get_system_diagnostics

from modules.temp_file_cleaner import (
    scan_temp_files,
    clean_temp_files,
)

from modules.recycle_bin_manager import (
    get_recycle_bin_info,
    empty_recycle_bin,
)

from modules.network_diagnostics import get_network_diagnostics


# =========================================================
# THEME
# =========================================================

BG = "#10141C"
PANEL = "#191F2B"
GOLD = "#D6A84F"
TEXT = "#E8EAF0"
GREEN = "#45D69A"
RED = "#E57373"
MUTED = "#AAB2C0"


class RepairPanel(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("JARVIS | Troubleshooting & Repair")
        self.resize(1150, 720)
        self.setMinimumSize(1000, 620)

        self.last_scan = None

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG};
                color: {TEXT};
            }}

            QLabel {{
                color: {TEXT};
                background: transparent;
                font-size: 12px;
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
                padding: 9px 12px;
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

        self.run_diagnostics()
        self.refresh_recycle_bin()

    # =====================================================
    # UI HELPERS
    # =====================================================

    def create_section_title(self, text):

        label = QLabel(text)

        label.setStyleSheet(f"""
            color: {GOLD};
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 5px;
        """)

        return label

    def create_section_frame(self):

        frame = QFrame()

        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {PANEL};
                border: 1px solid #303949;
                border-radius: 9px;
            }}
        """)

        return frame

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

        heading = QLabel(
            "SYSTEM TROUBLESHOOTING & REPAIR"
        )

        heading.setStyleSheet(f"""
            color: {GOLD};
            font-size: 21px;
            font-weight: bold;
        """)

        description = QLabel(
            "Monitor system health, manage temporary storage, "
            "inspect the Recycle Bin, and test network connectivity."
        )

        description.setStyleSheet(
            f"color: {MUTED}; font-size: 11px;"
        )

        description.setWordWrap(True)

        main_layout.addWidget(heading)
        main_layout.addWidget(description)

        # -------------------------------------------------
        # TWO-COLUMN LANDSCAPE AREA
        # -------------------------------------------------

        columns = QHBoxLayout()
        columns.setSpacing(14)

        left_column = QVBoxLayout()
        right_column = QVBoxLayout()

        left_column.setSpacing(12)
        right_column.setSpacing(12)

        # =================================================
        # LEFT: SYSTEM DIAGNOSTICS
        # =================================================

        diagnostics_frame = self.create_section_frame()

        diagnostics_layout = QVBoxLayout(diagnostics_frame)
        diagnostics_layout.setContentsMargins(14, 12, 14, 12)
        diagnostics_layout.setSpacing(8)

        diagnostics_heading = self.create_section_title(
            "SYSTEM DIAGNOSTICS"
        )

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(260)

        self.status_label = QLabel(
            "Waiting for diagnostics..."
        )

        self.status_label.setStyleSheet(
            f"color: {MUTED};"
        )

        self.refresh_button = QPushButton(
            "RUN DIAGNOSTICS AGAIN"
        )

        diagnostics_layout.addWidget(diagnostics_heading)
        diagnostics_layout.addWidget(self.output, 1)
        diagnostics_layout.addWidget(self.status_label)
        diagnostics_layout.addWidget(self.refresh_button)

        # =================================================
        # LEFT: TEMPORARY FILE MANAGEMENT
        # =================================================

        temp_frame = self.create_section_frame()

        temp_layout = QVBoxLayout(temp_frame)
        temp_layout.setContentsMargins(14, 12, 14, 12)
        temp_layout.setSpacing(8)

        temp_heading = self.create_section_title(
            "TEMPORARY FILE MANAGEMENT"
        )

        temp_description = QLabel(
            "Scan your Windows temporary directory and review "
            "eligible files before requesting cleanup."
        )

        temp_description.setWordWrap(True)
        temp_description.setStyleSheet(
            f"color: {MUTED};"
        )

        self.scan_button = QPushButton(
            "SCAN TEMP FILES"
        )

        self.clean_button = QPushButton(
            "CLEAN TEMP FILES"
        )

        self.clean_button.setEnabled(False)

        temp_buttons = QHBoxLayout()
        temp_buttons.setSpacing(8)
        temp_buttons.addWidget(self.scan_button)
        temp_buttons.addWidget(self.clean_button)

        temp_layout.addWidget(temp_heading)
        temp_layout.addWidget(temp_description)
        temp_layout.addLayout(temp_buttons)

        # =================================================
        # RIGHT: RECYCLE BIN MANAGEMENT
        # =================================================

        recycle_frame = self.create_section_frame()

        recycle_layout = QVBoxLayout(recycle_frame)
        recycle_layout.setContentsMargins(14, 12, 14, 12)
        recycle_layout.setSpacing(8)

        recycle_heading = self.create_section_title(
            "WINDOWS RECYCLE BIN"
        )

        self.recycle_info_label = QLabel(
            "Loading Recycle Bin information..."
        )

        self.recycle_info_label.setWordWrap(True)

        self.recycle_status_label = QLabel(
            "Recycle Bin status: Checking..."
        )

        self.recycle_status_label.setStyleSheet(
            f"color: {MUTED};"
        )

        self.recycle_refresh_button = QPushButton(
            "REFRESH RECYCLE BIN"
        )

        self.recycle_empty_button = QPushButton(
            "EMPTY RECYCLE BIN"
        )

        self.recycle_empty_button.setStyleSheet("""
            QPushButton {
                background-color: #B84C4C;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #D65C5C;
            }

            QPushButton:disabled {
                background-color: #555B66;
                color: #AEB3BC;
            }
        """)

        self.recycle_empty_button.setEnabled(False)

        recycle_buttons = QHBoxLayout()
        recycle_buttons.setSpacing(8)
        recycle_buttons.addWidget(self.recycle_refresh_button)
        recycle_buttons.addWidget(self.recycle_empty_button)

        recycle_layout.addWidget(recycle_heading)
        recycle_layout.addWidget(self.recycle_info_label)
        recycle_layout.addWidget(self.recycle_status_label)
        recycle_layout.addLayout(recycle_buttons)

        # =================================================
        # RIGHT: NETWORK DIAGNOSTICS
        # =================================================

        network_frame = self.create_section_frame()

        network_layout = QVBoxLayout(network_frame)
        network_layout.setContentsMargins(14, 12, 14, 12)
        network_layout.setSpacing(8)

        network_heading = self.create_section_title(
            "NETWORK DIAGNOSTICS"
        )

        network_description = QLabel(
            "Check internet connectivity, local IP information, "
            "connection response time, and DNS resolution."
        )

        network_description.setWordWrap(True)
        network_description.setStyleSheet(
            f"color: {MUTED};"
        )

        self.network_info_label = QLabel(
            "Network information has not been checked."
        )

        self.network_info_label.setWordWrap(True)
        self.network_info_label.setTextInteractionFlags(
            self.network_info_label.textInteractionFlags()
        )

        self.network_status_label = QLabel(
            "Network status: Not checked"
        )

        self.network_status_label.setStyleSheet(
            f"color: {MUTED}; font-weight: bold;"
        )

        self.network_test_button = QPushButton(
            "RUN NETWORK TEST"
        )

        network_layout.addWidget(network_heading)
        network_layout.addWidget(network_description)
        network_layout.addWidget(self.network_info_label, 1)
        network_layout.addWidget(self.network_status_label)
        network_layout.addWidget(self.network_test_button)

        # -------------------------------------------------
        # ADD SECTIONS TO COLUMNS
        # -------------------------------------------------

        left_column.addWidget(diagnostics_frame, 1)
        left_column.addWidget(temp_frame)

        right_column.addWidget(recycle_frame)
        right_column.addWidget(network_frame, 1)

        columns.addLayout(left_column, 1)
        columns.addLayout(right_column, 1)

        main_layout.addLayout(columns, 1)

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        footer = QHBoxLayout()

        footer_note = QLabel(
            "JARVIS SYSTEM MANAGEMENT"
        )

        footer_note.setStyleSheet(
            f"color: {MUTED}; font-size: 10px;"
        )

        self.close_button = QPushButton("CLOSE")
        self.close_button.setFixedWidth(120)

        footer.addWidget(footer_note)
        footer.addStretch()
        footer.addWidget(self.close_button)

        main_layout.addLayout(footer)

        # -------------------------------------------------
        # BUTTON CONNECTIONS
        # -------------------------------------------------

        self.refresh_button.clicked.connect(
            self.run_diagnostics
        )

        self.scan_button.clicked.connect(
            self.scan_temporary_files
        )

        self.clean_button.clicked.connect(
            self.clean_temporary_files
        )

        self.recycle_refresh_button.clicked.connect(
            self.refresh_recycle_bin
        )

        self.recycle_empty_button.clicked.connect(
            self.empty_windows_recycle_bin
        )

        self.network_test_button.clicked.connect(
            self.run_network_test
        )

        self.close_button.clicked.connect(
            self.close
        )

    # =====================================================
    # SYSTEM DIAGNOSTICS
    # =====================================================

    def run_diagnostics(self):

        self.status_label.setText(
            "Running system diagnostics..."
        )

        self.refresh_button.setEnabled(False)

        try:

            results = get_system_diagnostics()

            self.output.setPlainText(
                self.format_results(results)
            )

            self.status_label.setText(
                "Diagnostics completed successfully."
            )

        except Exception as error:

            self.output.setPlainText(
                f"Unable to complete system diagnostics.\n\nError: {error}"
            )

            self.status_label.setText(
                "Diagnostics failed."
            )

            QMessageBox.warning(
                self,
                "Diagnostic Error",
                str(error)
            )

        finally:

            self.refresh_button.setEnabled(True)

    # =====================================================
    # TEMPORARY FILE SCANNING
    # =====================================================

    def scan_temporary_files(self):

        self.status_label.setText(
            "Scanning temporary files..."
        )

        self.scan_button.setEnabled(False)
        self.clean_button.setEnabled(False)

        try:

            results = scan_temp_files()

            if not results.get("success"):

                self.last_scan = None

                self.output.setPlainText(
                    "TEMPORARY FILE SCAN FAILED\n\n"
                    + results.get(
                        "message",
                        "Unable to scan temporary files."
                    )
                )

                self.status_label.setText(
                    "Temporary-file scan failed."
                )

                return

            self.last_scan = results

            files = results.get("files", [])

            report = [
                "TEMPORARY FILE SCAN",
                "=" * 50,
                "",
                f"Location: {results.get('directory', 'Unknown')}",
                f"Eligible files: {results.get('total_files', 0)}",
                f"Estimated storage: {self.format_size(results.get('total_bytes', 0))}",
                f"Skipped entries: {results.get('skipped', 0)}",
                f"Scanned at: {results.get('checked_at', 'Unknown')}",
                "",
                "ELIGIBLE FILES",
                "-" * 50,
                ""
            ]

            for index, item in enumerate(files, start=1):

                report.append(
                    f"{index}. {item.get('name', 'Unknown')}"
                )

                report.append(
                    f"   Size: {self.format_size(item.get('size_bytes', 0))}"
                )

            if not files:

                report.append(
                    "No eligible temporary files were found."
                )

            report.extend([
                "",
                "No files have been deleted.",
                "Use CLEAN TEMP FILES to request approval."
            ])

            self.output.setPlainText(
                "\n".join(report)
            )

            if files:

                self.clean_button.setEnabled(True)

                self.status_label.setText(
                    "Scan completed. Files are ready for review."
                )

            else:

                self.status_label.setText(
                    "Scan completed. No eligible files found."
                )

        except Exception as error:

            self.last_scan = None

            self.output.setPlainText(
                f"Unable to scan temporary files.\n\nError: {error}"
            )

            self.status_label.setText(
                "Temporary-file scan failed."
            )

            QMessageBox.warning(
                self,
                "Temporary File Scan Error",
                str(error)
            )

        finally:

            self.scan_button.setEnabled(True)

    # =====================================================
    # TEMPORARY FILE CLEANUP
    # =====================================================

    def clean_temporary_files(self):

        if not self.last_scan:

            QMessageBox.warning(
                self,
                "Scan Required",
                "Please scan temporary files before cleanup."
            )

            return

        if not self.last_scan.get("files"):

            QMessageBox.information(
                self,
                "No Files Found",
                "There are no eligible temporary files."
            )

            return

        self.clean_button.setEnabled(False)
        self.scan_button.setEnabled(False)

        self.status_label.setText(
            "Waiting for cleanup authorization..."
        )

        try:

            results = clean_temp_files(parent=self)

            deleted_files = results.get("deleted_files", 0)
            deleted_bytes = results.get("deleted_bytes", 0)
            skipped_files = results.get("skipped_files", 0)

            report = [
                "TEMPORARY FILE CLEANUP REPORT",
                "=" * 50,
                "",
                f"Status: {results.get('status', 'NOT COMPLETED')}",
                f"Deleted files: {deleted_files}",
                f"Storage released: {self.format_size(deleted_bytes)}",
                f"Skipped files: {skipped_files}",
                "",
                results.get(
                    "message",
                    "Cleanup operation finished."
                )
            ]

            self.output.setPlainText(
                "\n".join(report)
            )

            if results.get("status") == "REJECTED":

                self.status_label.setText(
                    "Cleanup rejected. No files were deleted."
                )

            elif not results.get("success"):

                self.status_label.setText(
                    "Cleanup was not completed."
                )

            else:

                self.status_label.setText(
                    "Temporary-file cleanup completed."
                )

                if deleted_files:

                    QMessageBox.information(
                        self,
                        "Cleanup Completed",
                        (
                            f"Deleted files: {deleted_files}\n"
                            f"Storage released: {self.format_size(deleted_bytes)}\n"
                            f"Skipped files: {skipped_files}"
                        )
                    )

            self.last_scan = None

        except Exception as error:

            self.output.setPlainText(
                f"Temporary-file cleanup failed.\n\nError: {error}"
            )

            self.status_label.setText(
                "Cleanup failed."
            )

            QMessageBox.warning(
                self,
                "Cleanup Error",
                str(error)
            )

            self.last_scan = None

        finally:

            self.clean_button.setEnabled(False)
            self.scan_button.setEnabled(True)

    # =====================================================
    # RECYCLE BIN INFORMATION
    # =====================================================

    def refresh_recycle_bin(self):

        self.recycle_refresh_button.setEnabled(False)
        self.recycle_empty_button.setEnabled(False)

        self.recycle_status_label.setText(
            "Reading Windows Recycle Bin..."
        )

        try:

            results = get_recycle_bin_info()

            if not results.get("success"):

                self.recycle_info_label.setText(
                    "Unable to retrieve Recycle Bin information."
                )

                self.recycle_status_label.setText(
                    results.get(
                        "message",
                        "Recycle Bin query failed."
                    )
                )

                return

            total_items = results.get("total_items", 0)
            total_bytes = results.get("total_bytes", 0)

            self.recycle_info_label.setText(
                f"Items: {total_items}     |     "
                f"Storage occupied: {self.format_size(total_bytes)}"
            )

            if total_items == 0:

                self.recycle_status_label.setText(
                    "Recycle Bin is empty."
                )

                self.recycle_empty_button.setEnabled(False)

            else:

                self.recycle_status_label.setText(
                    "Recycle Bin contains items."
                )

                self.recycle_empty_button.setEnabled(True)

        except Exception as error:

            self.recycle_info_label.setText(
                "Unable to retrieve Recycle Bin information."
            )

            self.recycle_status_label.setText(
                f"Error: {error}"
            )

            QMessageBox.warning(
                self,
                "Recycle Bin Error",
                str(error)
            )

        finally:

            self.recycle_refresh_button.setEnabled(True)

    # =====================================================
    # EMPTY RECYCLE BIN
    # =====================================================

    def empty_windows_recycle_bin(self):

        self.recycle_empty_button.setEnabled(False)
        self.recycle_refresh_button.setEnabled(False)

        self.recycle_status_label.setText(
            "Waiting for Recycle Bin authorization..."
        )

        try:

            results = empty_recycle_bin(parent=self)

            status = results.get("status", "FAILED")
            deleted_items = results.get("deleted_items", 0)
            freed_bytes = results.get("freed_bytes", 0)

            message = results.get(
                "message",
                "Recycle Bin operation finished."
            )

            if status == "REJECTED":

                self.recycle_status_label.setText(
                    "Operation rejected. Recycle Bin unchanged."
                )

                QMessageBox.information(
                    self,
                    "Operation Rejected",
                    message
                )

            elif status == "EMPTY":

                self.recycle_status_label.setText(
                    "Recycle Bin is already empty."
                )

                QMessageBox.information(
                    self,
                    "Recycle Bin",
                    message
                )

            elif results.get("success"):

                self.recycle_status_label.setText(
                    "Recycle Bin emptied successfully."
                )

                QMessageBox.information(
                    self,
                    "Recycle Bin Cleanup Completed",
                    (
                        f"Deleted items: {deleted_items}\n"
                        f"Reported storage released: {self.format_size(freed_bytes)}\n\n"
                        f"{message}"
                    )
                )

            else:

                self.recycle_status_label.setText(
                    "Recycle Bin cleanup failed."
                )

                QMessageBox.warning(
                    self,
                    "Recycle Bin Cleanup Failed",
                    message
                )

        except Exception as error:

            self.recycle_status_label.setText(
                "Recycle Bin cleanup failed."
            )

            QMessageBox.warning(
                self,
                "Recycle Bin Error",
                str(error)
            )

        finally:

            self.recycle_refresh_button.setEnabled(True)
            self.refresh_recycle_bin()

    # =====================================================
    # NETWORK DIAGNOSTICS
    # =====================================================

    def run_network_test(self):

        self.network_test_button.setEnabled(False)

        self.network_status_label.setText(
            "Network status: Testing..."
        )

        self.network_status_label.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.network_info_label.setText(
            "Testing internet connection and DNS resolution..."
        )

        try:

            results = get_network_diagnostics()

            if not results.get("success"):

                self.network_info_label.setText(
                    str(results)
                )

                self.network_status_label.setText(
                    "Network status: TEST FAILED"
                )

                self.network_status_label.setStyleSheet(
                    f"color: {RED}; font-weight: bold;"
                )

                return

            network = results.get("network_connection", {})
            dns = results.get("dns_resolution", {})

            local_ip = results.get("local_ip") or "Unavailable"

            connection_time = network.get("response_time_ms")
            dns_time = dns.get("response_time_ms")

            dns_addresses = dns.get("ip_addresses", [])

            connection_time_text = (
                f"{connection_time:.2f} ms"
                if isinstance(connection_time, (int, float))
                else "Unavailable"
            )

            dns_time_text = (
                f"{dns_time:.2f} ms"
                if isinstance(dns_time, (int, float))
                else "Unavailable"
            )

            report = [
                f"Local IP address: {local_ip}",
                "",
                "INTERNET CONNECTION",
                f"Host: {network.get('host', 'Unknown')}",
                f"Port: {network.get('port', 'Unknown')}",
                f"Result: {network.get('message', 'Unknown')}",
                f"Response time: {connection_time_text}",
                "",
                "DNS RESOLUTION",
                f"Hostname: {dns.get('hostname', 'Unknown')}",
                f"Result: {dns.get('message', 'Unknown')}",
                f"Response time: {dns_time_text}",
                "Resolved addresses:"
            ]

            if dns_addresses:

                report.extend(
                    f"  • {address}"
                    for address in dns_addresses
                )

            else:

                report.append("  No addresses returned.")

            report.extend([
                "",
                f"Checked: {results.get('checked_at', 'Unknown')}",
                "",
                "Network settings were not modified."
            ])

            self.network_info_label.setText(
                "\n".join(report)
            )

            status = results.get(
                "overall_status",
                "UNKNOWN"
            )

            self.network_status_label.setText(
                f"Network status: {status}"
            )

            if status == "CONNECTED":

                color = GREEN

            elif status == "LIMITED":

                color = GOLD

            else:

                color = RED

            self.network_status_label.setStyleSheet(
                f"color: {color}; font-weight: bold;"
            )

        except Exception as error:

            self.network_info_label.setText(
                f"Network diagnostics failed.\n\nError: {error}"
            )

            self.network_status_label.setText(
                "Network status: TEST FAILED"
            )

            self.network_status_label.setStyleSheet(
                f"color: {RED}; font-weight: bold;"
            )

            QMessageBox.warning(
                self,
                "Network Diagnostics Error",
                str(error)
            )

        finally:

            self.network_test_button.setEnabled(True)

    # =====================================================
    # FORMATTING
    # =====================================================

    def format_size(self, size_bytes):

        if size_bytes < 1024:
            return f"{size_bytes} B"

        if size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.2f} KB"

        if size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.2f} MB"

        return f"{size_bytes / (1024 ** 3):.2f} GB"

    def format_results(self, results):

        if isinstance(results, dict):

            lines = []

            for key, value in results.items():

                heading = str(key).replace(
                    "_", " "
                ).upper()

                lines.append(heading)
                lines.append("-" * len(heading))

                if isinstance(value, dict):

                    for sub_key, sub_value in value.items():

                        lines.append(
                            f"{str(sub_key).replace('_', ' ').title()}: "
                            f"{sub_value}"
                        )

                elif isinstance(value, (list, tuple)):

                    for item in value:
                        lines.append(str(item))

                else:

                    lines.append(str(value))

                lines.append("")

            return "\n".join(lines)

        if isinstance(results, (list, tuple)):

            return "\n\n".join(
                str(item) for item in results
            )

        return str(results)
