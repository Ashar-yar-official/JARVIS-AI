
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QGroupBox,
    QMessageBox,
    QSizePolicy
)

from PySide6.QtCore import Qt, QThread, Signal

from modules.voice_engine import VoiceEngine


# =================================================
# BACKGROUND VOICE WORKER
# =================================================

class VoiceWorker(QThread):

    transcription_ready = Signal(str)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    finished_listening = Signal()

    def __init__(self, voice_engine, continuous=False, parent=None):

        super().__init__(parent)

        self.voice_engine = voice_engine
        self.continuous = continuous
        self.stop_requested = False

    def stop(self):

        self.stop_requested = True

    def run(self):

        try:

            while not self.stop_requested:

                self.status_changed.emit(
                    "Listening... Speak now."
                )

                result = self.voice_engine.listen(
                    duration=5,
                    device=1
                )

                if not result.get("success"):

                    message = result.get(
                        "message",
                        "Speech recognition failed."
                    )

                    self.error_occurred.emit(message)

                    if not self.continuous:
                        break

                    continue

                transcription = result.get(
                    "transcription",
                    ""
                ).strip()

                if transcription:

                    self.transcription_ready.emit(
                        transcription
                    )

                else:

                    self.status_changed.emit(
                        "No speech detected. Listening again..."
                    )

                if not self.continuous:
                    break

        except Exception as error:

            self.error_occurred.emit(str(error))

        finally:

            self.finished_listening.emit()


# =================================================
# VOICE TEST WORKER
# =================================================

class VoiceTestWorker(QThread):

    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, voice_engine, parent=None):

        super().__init__(parent)

        self.voice_engine = voice_engine

    def run(self):

        try:

            result = self.voice_engine.test_voice()

            if isinstance(result, dict):

                if result.get("success"):

                    self.completed.emit(
                        "Voice test completed successfully."
                    )

                else:

                    self.failed.emit(
                        result.get(
                            "message",
                            "Voice test failed."
                        )
                    )

            else:

                self.completed.emit(
                    "Voice test command completed."
                )

        except Exception as error:

            self.failed.emit(str(error))


# =================================================
# MAIN VOICE PANEL
# =================================================

class VoicePanel(QDialog):

    command_received = Signal(str)

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "J.A.R.V.I.S. | Voice & Communication"
        )

        self.setMinimumSize(1000, 620)
        self.resize(1150, 700)

        self.setModal(False)

        self.voice_engine = None
        self.voice_worker = None
        self.test_worker = None

        self.saved_preferences = {
            "listening_mode": "Push to Talk",
            "wake_word_enabled": False,
            "wake_word": "Hey JARVIS",
            "language": "English",
            "voice": "Professional British Male",
            "spoken_responses": True
        }

        self.setup_ui()
        self.load_preferences()
        self.connect_voice_engine()

    # =================================================
    # MAIN UI
    # =================================================

    def setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            24, 20, 24, 20
        )

        main_layout.setSpacing(15)

        # HEADER

        header = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            "VOICE & COMMUNICATION"
        )

        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Manage microphone input, speech recognition "
            "and JARVIS voice output."
        )

        subtitle.setObjectName("pageSubtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header.addLayout(title_layout)
        header.addStretch()

        self.header_status = QLabel(
            "● VOICE SYSTEM"
        )

        self.header_status.setObjectName(
            "headerStatus"
        )

        header.addWidget(self.header_status)

        main_layout.addLayout(header)

        main_layout.addWidget(
            self.create_separator()
        )

        # LANDSCAPE CONTENT

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        # LEFT COLUMN

        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        left_heading = QLabel(
            "CONFIGURATION"
        )

        left_heading.setObjectName(
            "sectionHeading"
        )

        left_column.addWidget(left_heading)

        # LISTENING CONFIGURATION

        listening_group = QGroupBox(
            "LISTENING CONFIGURATION"
        )

        listening_layout = QVBoxLayout(
            listening_group
        )

        listening_layout.setSpacing(10)

        listening_layout.addWidget(
            QLabel("Listening Mode")
        )

        self.listening_mode = QComboBox()

        self.listening_mode.addItems([
            "Push to Talk",
            "Continuous Listening"
        ])

        listening_layout.addWidget(
            self.listening_mode
        )

        self.wake_word_checkbox = QCheckBox(
            "Enable Wake Word Detection"
        )

        self.wake_word_checkbox.setToolTip(
            "Wake-word detection is not implemented yet."
        )

        listening_layout.addWidget(
            self.wake_word_checkbox
        )

        listening_layout.addWidget(
            QLabel("Wake Word")
        )

        self.wake_word_input = QLineEdit()

        self.wake_word_input.setPlaceholderText(
            "Enter wake word"
        )

        listening_layout.addWidget(
            self.wake_word_input
        )

        left_column.addWidget(
            listening_group
        )

        # VOICE OUTPUT CONFIGURATION

        output_group = QGroupBox(
            "VOICE OUTPUT CONFIGURATION"
        )

        output_layout = QVBoxLayout(
            output_group
        )

        output_layout.setSpacing(10)

        output_layout.addWidget(
            QLabel("Recognition Language")
        )

        self.language_combo = QComboBox()

        self.language_combo.addItems([
            "English"
        ])

        output_layout.addWidget(
            self.language_combo
        )

        output_layout.addWidget(
            QLabel("JARVIS Voice")
        )

        self.voice_combo = QComboBox()

        self.voice_combo.addItems([
            "Professional British Male",
            "Professional Female",
            "Natural Male",
            "Natural Female"
        ])

        output_layout.addWidget(
            self.voice_combo
        )

        self.spoken_response_checkbox = QCheckBox(
            "Enable Spoken AI Responses"
        )

        self.spoken_response_checkbox.setChecked(
            True
        )

        output_layout.addWidget(
            self.spoken_response_checkbox
        )

        left_column.addWidget(
            output_group
        )

        left_column.addStretch()

        content_layout.addLayout(
            left_column,
            4
        )

        # VERTICAL DIVIDER

        divider = QFrame()

        divider.setFrameShape(
            QFrame.Shape.VLine
        )

        divider.setStyleSheet(
            "color: #604322;"
        )

        content_layout.addWidget(divider)

        # RIGHT COLUMN

        right_column = QVBoxLayout()
        right_column.setSpacing(14)

        right_heading = QLabel(
            "VOICE OPERATIONS"
        )

        right_heading.setObjectName(
            "sectionHeading"
        )

        right_column.addWidget(right_heading)

        # STATUS CARDS

        status_layout = QGridLayout()

        status_layout.setSpacing(10)

        self.microphone_status = self.create_status_card(
            "MICROPHONE",
            "Not Connected",
            "microphoneStatus"
        )

        self.speech_status = self.create_status_card(
            "SPEECH OUTPUT",
            "Not Connected",
            "speechStatus"
        )

        self.engine_status = self.create_status_card(
            "VOICE ENGINE",
            "Waiting",
            "engineStatus"
        )

        status_layout.addWidget(
            self.microphone_status,
            0, 0
        )

        status_layout.addWidget(
            self.speech_status,
            0, 1
        )

        status_layout.addWidget(
            self.engine_status,
            0, 2
        )

        right_column.addLayout(status_layout)

        # RECOGNIZED SPEECH

        transcription_group = QGroupBox(
            "RECOGNIZED SPEECH"
        )

        transcription_layout = QVBoxLayout(
            transcription_group
        )

        self.transcription_label = QLabel(
            "Your recognized speech will appear here."
        )

        self.transcription_label.setWordWrap(True)

        self.transcription_label.setMinimumHeight(95)

        self.transcription_label.setAlignment(
            Qt.AlignmentFlag.AlignTop |
            Qt.AlignmentFlag.AlignLeft
        )

        self.transcription_label.setObjectName(
            "transcriptionDisplay"
        )

        transcription_layout.addWidget(
            self.transcription_label
        )

        right_column.addWidget(
            transcription_group,
            1
        )

        # ACTIVITY STATUS

        activity_group = QGroupBox(
            "VOICE ACTIVITY"
        )

        activity_layout = QVBoxLayout(
            activity_group
        )

        self.activity_label = QLabel(
            "Voice engine is waiting for connection."
        )

        self.activity_label.setWordWrap(True)

        self.activity_label.setObjectName(
            "activityLabel"
        )

        activity_layout.addWidget(
            self.activity_label
        )

        right_column.addWidget(activity_group)

        content_layout.addLayout(
            right_column,
            6
        )

        main_layout.addLayout(
            content_layout,
            1
        )

        main_layout.addWidget(
            self.create_separator()
        )

        # BOTTOM ACTION BAR

        action_layout = QHBoxLayout()

        action_layout.addWidget(
            QLabel("MICROPHONE CONTROLS")
        )

        action_layout.addStretch()

        self.start_button = QPushButton(
            "▶  START LISTENING"
        )

        self.start_button.setObjectName(
            "primaryButton"
        )

        self.start_button.clicked.connect(
            self.start_listening
        )

        self.stop_button = QPushButton(
            "■  STOP LISTENING"
        )

        self.stop_button.setObjectName(
            "secondaryButton"
        )

        self.stop_button.clicked.connect(
            self.stop_listening
        )

        self.stop_button.setEnabled(False)

        self.test_button = QPushButton(
            "♪  TEST VOICE"
        )

        self.test_button.setObjectName(
            "secondaryButton"
        )

        self.test_button.clicked.connect(
            self.test_voice
        )

        action_layout.addWidget(self.start_button)
        action_layout.addWidget(self.stop_button)
        action_layout.addWidget(self.test_button)

        main_layout.addLayout(action_layout)

        # STYLING

        self.setStyleSheet("""
            QDialog {
                background-color: #101713;
            }

            QLabel {
                color: #dce7df;
                font-size: 12px;
            }

            QLabel#pageTitle {
                color: #e8f5e9;
                font-size: 25px;
                font-weight: bold;
            }

            QLabel#pageSubtitle {
                color: #aab7b0;
                font-size: 12px;
            }

            QLabel#sectionHeading {
                color: #e9ad45;
                font-size: 13px;
                font-weight: bold;
            }

            QLabel#headerStatus {
                color: #b9f6ca;
                font-size: 11px;
                font-weight: bold;
                padding: 9px 14px;
                border: 1px solid #315c40;
                border-radius: 6px;
                background-color: #17251e;
            }

            QGroupBox {
                color: #b9f6ca;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #285c43;
                border-radius: 8px;
                margin-top: 12px;
                padding: 13px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }

            QComboBox, QLineEdit {
                background-color: #17251e;
                color: #e8f5e9;
                border: 1px solid #38634b;
                border-radius: 5px;
                padding: 9px;
                min-height: 20px;
            }

            QComboBox QAbstractItemView {
                background-color: #17251e;
                color: #e8f5e9;
                selection-background-color: #285c43;
            }

            QCheckBox {
                color: #dce7df;
                spacing: 8px;
            }

            QFrame#statusCard {
                background-color: #1b3024;
                border: 1px solid #315c40;
                border-radius: 8px;
            }

            QLabel#transcriptionDisplay {
                background-color: #17251e;
                color: #e8f5e9;
                border: 1px solid #315c40;
                border-radius: 6px;
                padding: 14px;
                font-size: 13px;
            }

            QLabel#activityLabel {
                color: #a8c9b2;
                padding: 10px;
                background-color: #17251e;
                border-radius: 6px;
            }

            QPushButton {
                padding: 11px 17px;
                border-radius: 6px;
                font-weight: bold;
                min-height: 22px;
            }

            QPushButton#primaryButton {
                background-color: #20a45a;
                color: white;
                border: none;
            }

            QPushButton#primaryButton:hover {
                background-color: #28bd6b;
            }

            QPushButton#secondaryButton {
                background-color: #263d30;
                color: #d9fbe5;
                border: 1px solid #39734f;
            }

            QPushButton#secondaryButton:hover {
                background-color: #345640;
            }

            QPushButton:disabled {
                background-color: #303a33;
                color: #78847b;
            }
        """)

    # =================================================
    # SEPARATOR
    # =================================================

    def create_separator(self):

        line = QFrame()

        line.setFrameShape(
            QFrame.Shape.HLine
        )

        line.setFixedHeight(1)

        line.setStyleSheet(
            "background-color: #604322; border: none;"
        )

        return line

    # =================================================
    # STATUS CARDS
    # =================================================

    def create_status_card(
        self,
        heading,
        status,
        object_name
    ):

        card = QFrame()

        card.setObjectName("statusCard")

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            12, 12, 12, 12
        )

        layout.setSpacing(8)

        heading_label = QLabel(heading)

        heading_label.setStyleSheet("""
            color: #91b49c;
            font-size: 10px;
            font-weight: bold;
        """)

        status_label = QLabel(status)

        status_label.setObjectName(object_name)

        status_label.setStyleSheet("""
            color: #e8f5e9;
            font-size: 14px;
            font-weight: bold;
        """)

        layout.addWidget(heading_label)
        layout.addWidget(status_label)

        return card

    # =================================================
    # CONNECT SHARED VOICE ENGINE
    # =================================================

    def connect_voice_engine(self):

        parent_window = self.parent()

        # ConnectedMainWindow owns the shared engine.
        # Reuse it instead of constructing another instance.

        if parent_window is not None and hasattr(
            parent_window,
            "voice_engine"
        ):

            self.voice_engine = parent_window.voice_engine

            self.voice_error = getattr(
                parent_window,
                "voice_error",
                None
            )

        else:

            # Standalone fallback for testing this panel
            # outside ConnectedMainWindow.
            try:

                self.voice_engine = VoiceEngine()
                self.voice_error = None

            except Exception as error:

                self.voice_engine = None
                self.voice_error = str(error)

        if self.voice_engine is not None:

            self.update_status(
                microphone="Ready",
                speech_output="Ready",
                engine="Shared Engine"
            )

            self.header_status.setText(
                "● SHARED VOICE ENGINE CONNECTED"
            )

            self.activity_label.setText(
                "Connected to the application's shared voice engine."
            )

        else:

            self.update_status(
                microphone="Unavailable",
                speech_output="Unavailable",
                engine="Error"
            )

            self.header_status.setText(
                "● VOICE ENGINE ERROR"
            )

            self.activity_label.setText(
                "Voice engine connection failed: "
                f"{self.voice_error or 'Unknown error'}"
            )

    # =================================================
    # PREFERENCES
    # =================================================

    def load_preferences(self):

        self.listening_mode.setCurrentText(
            self.saved_preferences["listening_mode"]
        )

        self.wake_word_checkbox.setChecked(
            self.saved_preferences["wake_word_enabled"]
        )

        self.wake_word_input.setText(
            self.saved_preferences["wake_word"]
        )

        self.language_combo.setCurrentText(
            self.saved_preferences["language"]
        )

        self.voice_combo.setCurrentText(
            self.saved_preferences["voice"]
        )

        self.spoken_response_checkbox.setChecked(
            self.saved_preferences["spoken_responses"]
        )

    def save_preferences(self):

        self.saved_preferences = {
            "listening_mode": self.listening_mode.currentText(),
            "wake_word_enabled": self.wake_word_checkbox.isChecked(),
            "wake_word": self.wake_word_input.text().strip(),
            "language": self.language_combo.currentText(),
            "voice": self.voice_combo.currentText(),
            "spoken_responses": self.spoken_response_checkbox.isChecked()
        }

    # =================================================
    # START LISTENING
    # =================================================

    def start_listening(self):

        if self.voice_engine is None:

            QMessageBox.warning(
                self,
                "Voice Engine",
                "The voice engine is not connected."
            )

            return

        if (
            self.voice_worker
            and self.voice_worker.isRunning()
        ):
            return

        self.save_preferences()

        continuous = (
            self.listening_mode.currentText()
            == "Continuous Listening"
        )

        if self.wake_word_checkbox.isChecked():

            self.activity_label.setText(
                "Wake-word detection is not implemented yet. "
                "Listening will begin without wake-word filtering."
            )

        self.voice_worker = VoiceWorker(
            self.voice_engine,
            continuous=continuous,
            parent=self
        )

        self.voice_worker.status_changed.connect(
            self.on_listening_status
        )

        self.voice_worker.transcription_ready.connect(
            self.on_transcription_received
        )

        self.voice_worker.error_occurred.connect(
            self.on_voice_error
        )

        self.voice_worker.finished_listening.connect(
            self.on_listening_finished
        )

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.test_button.setEnabled(False)

        self.update_status(
            microphone="Listening",
            engine="Active"
        )

        self.header_status.setText(
            "● MICROPHONE ACTIVE"
        )

        self.activity_label.setText(
            "Starting microphone recording..."
        )

        self.voice_worker.start()

    # =================================================
    # STOP LISTENING
    # =================================================

    def stop_listening(self):

        if (
            self.voice_worker
            and self.voice_worker.isRunning()
        ):

            self.voice_worker.stop()

            self.activity_label.setText(
                "Stopping after the current recording finishes..."
            )

            self.stop_button.setEnabled(False)

    # =================================================
    # WORKER CALLBACKS
    # =================================================

    def on_listening_status(self, message):

        self.activity_label.setText(message)

    def on_transcription_received(self, transcription):

        transcription = transcription.strip()

        if not transcription:
            return

        self.transcription_label.setText(
            transcription
        )

        self.activity_label.setText(
            "Speech recognized successfully. Processing command..."
        )

        self.command_received.emit(transcription)

    def on_voice_error(self, message):

        self.activity_label.setText(
            f"Voice error: {message}"
        )

    def on_listening_finished(self):

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.test_button.setEnabled(True)

        self.update_status(
            microphone="Ready",
            engine="Connected"
        )

        self.header_status.setText(
            "● VOICE ENGINE CONNECTED"
        )

        if self.voice_worker:

            self.voice_worker.deleteLater()
            self.voice_worker = None

        if self.activity_label.text().startswith("Stopping after"):

            self.activity_label.setText(
                "Listening stopped."
            )

        elif self.activity_label.text().startswith("Listening"):

            self.activity_label.setText(
                "Listening session completed."
            )

    # =================================================
    # TEST VOICE
    # =================================================

    def test_voice(self):

        if self.voice_engine is None:

            QMessageBox.warning(
                self,
                "Voice Test",
                "The voice engine is not connected."
            )

            return

        if (
            self.voice_worker
            and self.voice_worker.isRunning()
        ):

            QMessageBox.information(
                self,
                "Voice Test",
                "Stop listening before testing voice output."
            )

            return

        if (
            self.test_worker
            and self.test_worker.isRunning()
        ):
            return

        self.save_preferences()

        self.test_button.setEnabled(False)
        self.start_button.setEnabled(False)

        self.activity_label.setText(
            "Generating and playing JARVIS voice test..."
        )

        self.test_worker = VoiceTestWorker(
            self.voice_engine,
            parent=self
        )

        self.test_worker.completed.connect(
            self.on_voice_test_completed
        )

        self.test_worker.failed.connect(
            self.on_voice_test_failed
        )

        self.test_worker.finished.connect(
            self.on_voice_test_worker_finished
        )

        self.test_worker.start()

    def on_voice_test_completed(self, message):

        self.activity_label.setText(message)

        self.update_status(
            speech_output="Ready",
            engine="Connected"
        )

    def on_voice_test_failed(self, message):

        self.activity_label.setText(
            f"Voice test failed: {message}"
        )

        self.update_status(
            speech_output="Error"
        )

    def on_voice_test_worker_finished(self):

        self.start_button.setEnabled(True)
        self.test_button.setEnabled(True)

        if self.test_worker:

            self.test_worker.deleteLater()
            self.test_worker = None

    # =================================================
    # EXTERNAL STATUS UPDATE
    # =================================================

    def update_status(
        self,
        microphone=None,
        speech_output=None,
        engine=None
    ):

        if microphone is not None:

            self.microphone_status.findChild(
                QLabel,
                "microphoneStatus"
            ).setText(microphone)

        if speech_output is not None:

            self.speech_status.findChild(
                QLabel,
                "speechStatus"
            ).setText(speech_output)

        if engine is not None:

            self.engine_status.findChild(
                QLabel,
                "engineStatus"
            ).setText(engine)

    # =================================================
    # SAFE WINDOW CLOSING
    # =================================================

    def closeEvent(self, event):

        if (
            self.voice_worker
            and self.voice_worker.isRunning()
        ):

            self.voice_worker.stop()
            self.voice_worker.wait()

        if (
            self.test_worker
            and self.test_worker.isRunning()
        ):

            self.test_worker.wait()

        self.save_preferences()

        event.accept()
