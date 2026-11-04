
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QMessageBox
)

from modules.command_processor import command_processor


BG = "#090909"
PANEL = "#121111"
GOLD = "#E9AD45"
LIGHT_GOLD = "#FFD98A"
TEXT = "#E8E0D3"
MUTED = "#8F8377"
GREEN = "#45D69A"
RED = "#A52B26"


# Keep speech workers alive until their threads actually finish.
# This prevents a running QThread from being destroyed when
# the chat dialog closes during speech generation.

_active_speech_workers = set()


def release_speech_worker(worker):

    _active_speech_workers.discard(worker)

    worker.deleteLater()


# =========================================================
# AI BACKGROUND WORKER
# =========================================================

class AIWorker(QThread):

    chunk_received = Signal(str)
    response_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, ai_engine, message):

        super().__init__()

        self.ai_engine = ai_engine
        self.message = message

    def run(self):

        try:

            response = self.ai_engine.send_message_stream(
                self.message,
                on_chunk=self.chunk_received.emit
            )

            self.response_ready.emit(response)

        except Exception as error:

            self.error_occurred.emit(str(error))


# =========================================================
# SPEECH BACKGROUND WORKER
# =========================================================

class SpeechWorker(QThread):

    speech_started = Signal()
    speech_completed = Signal()
    speech_stopped = Signal()
    speech_failed = Signal(str)

    def __init__(self, voice_engine, text):

        super().__init__()

        self.voice_engine = voice_engine
        self.text = text

    def run(self):

        try:

            if self.voice_engine is None:

                raise RuntimeError(
                    "The shared voice engine is unavailable."
                )

            self.speech_started.emit()

            result = self.voice_engine.speak(
                self.text
            )

            if isinstance(result, dict):

                if not result.get("success", False):

                    message = result.get(
                        "message",
                        "Speech playback failed."
                    )

                    # An intentional stop is not a playback error.
                    if (
                        "stopped" in message.lower()
                        or "cancelled" in message.lower()
                    ):

                        self.speech_stopped.emit()
                        return

                    raise RuntimeError(message)

            self.speech_completed.emit()

        except Exception as error:

            self.speech_failed.emit(str(error))


# =========================================================
# CHAT DIALOG
# =========================================================

class ChatDialog(QDialog):

    def __init__(
        self,
        ai_engine,
        parent=None,
        voice_engine=None
    ):

        super().__init__(parent)

        self.ai_engine = ai_engine

        # The voice engine is injected by ConnectedMainWindow.
        # This dialog does not create another VoiceEngine.
        self.voice_engine = voice_engine

        self.worker = None
        self.speech_worker = None

        self.response_cursor = None
        self.response_started = False

        self.closing = False

        self.setWindowTitle(
            "J.A.R.V.I.S. | AI COMMUNICATION"
        )

        self.resize(850, 650)
        self.setMinimumSize(600, 450)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG};
            }}

            QTextEdit {{
                background-color: {PANEL};
                color: {TEXT};
                border: 1px solid #604322;
                border-radius: 7px;
                padding: 12px;
                font-family: Consolas;
                font-size: 10pt;
            }}

            QLineEdit {{
                background-color: #0D0C0C;
                color: {LIGHT_GOLD};
                border: 1px solid #80552B;
                border-radius: 6px;
                padding: 11px;
                font-family: Consolas;
                font-size: 10pt;
            }}

            QPushButton {{
                background-color: #171311;
                color: {LIGHT_GOLD};
                border: 1px solid #80552B;
                border-radius: 6px;
                padding: 9px 16px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: #352218;
                border: 1px solid {LIGHT_GOLD};
            }}

            QPushButton:disabled {{
                color: #65594C;
                border-color: #40352A;
            }}
        """)

        self.init_ui()
        self.show_welcome_message()

    # =====================================================
    # INITIALIZE INTERFACE
    # =====================================================

    def init_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # HEADER

        header = QHBoxLayout()

        identity = QVBoxLayout()

        title = QLabel("J.A.R.V.I.S.")

        title.setFont(
            QFont("Consolas", 19, QFont.Weight.Bold)
        )

        title.setStyleSheet(
            f"color: {LIGHT_GOLD}; background: transparent;"
        )

        subtitle = QLabel(
            "PERSONAL INTELLIGENCE COMMUNICATION"
        )

        subtitle.setFont(QFont("Consolas", 8))

        subtitle.setStyleSheet(
            f"color: {MUTED}; background: transparent;"
        )

        identity.addWidget(title)
        identity.addWidget(subtitle)

        header.addLayout(identity)
        header.addStretch()

        self.connection_label = QLabel("● AI READY")

        self.connection_label.setStyleSheet(
            f"color: {GREEN}; background: transparent;"
        )

        self.connection_label.setFont(
            QFont("Consolas", 9, QFont.Weight.Bold)
        )

        header.addWidget(self.connection_label)

        root.addLayout(header)

        # CHAT HISTORY

        self.chat_output = QTextEdit()

        self.chat_output.setReadOnly(True)
        self.chat_output.setAcceptRichText(False)

        root.addWidget(self.chat_output, 1)

        # STATUS

        self.status_label = QLabel("SYSTEM READY")

        self.status_label.setFont(QFont("Consolas", 8))

        self.status_label.setStyleSheet(
            f"color: {GREEN}; background: transparent;"
        )

        root.addWidget(self.status_label)

        # MESSAGE INPUT

        input_layout = QHBoxLayout()

        self.message_input = QLineEdit()

        self.message_input.setPlaceholderText(
            "Ask JARVIS anything..."
        )

        self.message_input.returnPressed.connect(
            self.send_message
        )

        self.send_button = QPushButton("SEND")

        self.send_button.clicked.connect(
            self.send_message
        )

        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_button)

        root.addLayout(input_layout)

        # FOOTER

        footer = QHBoxLayout()

        self.clear_button = QPushButton(
            "NEW CONVERSATION"
        )

        self.clear_button.clicked.connect(
            self.clear_conversation
        )

        self.stop_speech_button = QPushButton(
            "STOP SPEAKING"
        )

        self.stop_speech_button.setEnabled(False)

        self.stop_speech_button.clicked.connect(
            self.stop_speech
        )

        self.close_button = QPushButton("CLOSE")

        self.close_button.clicked.connect(
            self.close
        )

        footer.addWidget(self.clear_button)
        footer.addWidget(self.stop_speech_button)

        footer.addStretch()

        footer.addWidget(self.close_button)

        root.addLayout(footer)

    # =====================================================
    # DISPLAY CHAT MESSAGE
    # =====================================================

    def append_message(self, sender, message, color):

        timestamp = datetime.now().strftime("%H:%M:%S")

        formatted_message = (
            f"\n[{timestamp}] {sender}\n"
            f"{message}\n"
            f"{'─' * 65}\n"
        )

        self.chat_output.moveCursor(
            QTextCursor.MoveOperation.End
        )

        self.chat_output.insertPlainText(
            formatted_message
        )

        self.chat_output.ensureCursorVisible()

    # =====================================================
    # START LIVE RESPONSE DISPLAY
    # =====================================================

    def start_response_display(self):

        if self.response_started:
            return

        self.response_started = True

        timestamp = datetime.now().strftime("%H:%M:%S")

        self.chat_output.moveCursor(
            QTextCursor.MoveOperation.End
        )

        self.chat_output.insertPlainText(
            f"\n[{timestamp}] J.A.R.V.I.S.\n"
        )

        self.response_cursor = self.chat_output.textCursor()

        self.chat_output.ensureCursorVisible()

    # =====================================================
    # DISPLAY INCOMING RESPONSE CHUNKS
    # =====================================================

    def handle_chunk(self, chunk):

        if self.closing:
            return

        self.start_response_display()

        self.chat_output.moveCursor(
            QTextCursor.MoveOperation.End
        )

        self.chat_output.insertPlainText(chunk)

        self.chat_output.ensureCursorVisible()

    # =====================================================
    # FINISH LIVE RESPONSE DISPLAY
    # =====================================================

    def finish_response_display(self):

        if self.response_started:

            self.chat_output.moveCursor(
                QTextCursor.MoveOperation.End
            )

            self.chat_output.insertPlainText(
                f"\n{'─' * 65}\n"
            )

            self.chat_output.ensureCursorVisible()

        self.response_started = False
        self.response_cursor = None

    # =====================================================
    # WELCOME MESSAGE
    # =====================================================

    def show_welcome_message(self):

        self.append_message(
            "J.A.R.V.I.S.",
            (
                "Good day. My communication systems are ready.\n"
                "How may I assist you?"
            ),
            LIGHT_GOLD
        )

    # =====================================================
    # UPDATE STATUS
    # =====================================================

    def set_ready_status(self):

        self.status_label.setText("SYSTEM READY")

        self.status_label.setStyleSheet(
            f"color: {GREEN}; background: transparent;"
        )

        self.connection_label.setText("● AI READY")

        self.connection_label.setStyleSheet(
            f"color: {GREEN}; background: transparent;"
        )

    # =====================================================
    # CHECK SPOKEN RESPONSE PREFERENCE
    # =====================================================

    def spoken_responses_enabled(self):

        parent = self.parent()

        if parent is not None:

            voice_dialogs = getattr(
                parent,
                "department_dialogs",
                {}
            )

            voice_panel = voice_dialogs.get("VOICE")

            if voice_panel is not None:

                checkbox = getattr(
                    voice_panel,
                    "spoken_response_checkbox",
                    None
                )

                if checkbox is not None:
                    return checkbox.isChecked()

        # Audio playback is OFF unless explicitly enabled.
        return False

    # =====================================================
    # SPEAK GEMINI RESPONSE
    # =====================================================

    def speak_response(self, response):

        response = str(response or "").strip()

        if not response:
            return

        if not self.spoken_responses_enabled():
            return

        if self.voice_engine is None:

            self.status_label.setText(
                "RESPONSE RECEIVED - VOICE ENGINE NOT CONNECTED"
            )

            return

        if (
            self.speech_worker is not None
            and self.speech_worker.isRunning()
        ):
            return

        self.speech_worker = SpeechWorker(
            self.voice_engine,
            response
        )

        _active_speech_workers.add(self.speech_worker)

        self.speech_worker.speech_started.connect(
            self.on_speech_started
        )

        self.speech_worker.speech_completed.connect(
            self.on_speech_completed
        )

        self.speech_worker.speech_stopped.connect(
            self.on_speech_stopped
        )

        self.speech_worker.speech_failed.connect(
            self.on_speech_failed
        )

        self.speech_worker.finished.connect(
            self.on_speech_worker_finished
        )

        self.speech_worker.finished.connect(
            lambda worker=self.speech_worker:
            release_speech_worker(worker)
        )

        self.speech_worker.start()

    # =====================================================
    # SPEECH STARTED
    # =====================================================

    def on_speech_started(self):

        if self.closing:
            return

        self.stop_speech_button.setEnabled(True)

        self.status_label.setText(
            "JARVIS IS SPEAKING..."
        )

        self.status_label.setStyleSheet(
            f"color: {GOLD}; background: transparent;"
        )

    # =====================================================
    # SPEECH COMPLETED
    # =====================================================

    def on_speech_completed(self):

        if self.closing:
            return

        self.stop_speech_button.setEnabled(False)

        self.status_label.setText(
            "RESPONSE SPOKEN"
        )

        self.status_label.setStyleSheet(
            f"color: {GREEN}; background: transparent;"
        )

    # =====================================================
    # SPEECH STOPPED
    # =====================================================

    def on_speech_stopped(self):

        if self.closing:
            return

        self.stop_speech_button.setEnabled(False)

        self.status_label.setText(
            "SPEECH STOPPED"
        )

        self.status_label.setStyleSheet(
            f"color: {GOLD}; background: transparent;"
        )

    # =====================================================
    # SPEECH FAILED
    # =====================================================

    def on_speech_failed(self, error):

        if self.closing:
            return

        self.stop_speech_button.setEnabled(False)

        self.status_label.setText(
            "SPEECH OUTPUT FAILED"
        )

        self.status_label.setStyleSheet(
            f"color: {RED}; background: transparent;"
        )

        self.append_message(
            "VOICE SYSTEM ERROR",
            f"Could not speak the response: {error}",
            RED
        )

    # =====================================================
    # STOP SPEECH
    # =====================================================

    def stop_speech(self):

        if self.voice_engine is None:
            return

        if (
            self.speech_worker is None
            or not self.speech_worker.isRunning()
        ):

            self.stop_speech_button.setEnabled(False)
            return

        try:

            self.voice_engine.stop_speaking()

            self.stop_speech_button.setEnabled(False)

            self.status_label.setText(
                "STOPPING SPEECH..."
            )

            self.status_label.setStyleSheet(
                f"color: {GOLD}; background: transparent;"
            )

        except Exception as error:

            self.append_message(
                "VOICE SYSTEM ERROR",
                f"Could not stop speech: {error}",
                RED
            )

    # =====================================================
    # SPEECH WORKER FINISHED
    # =====================================================

    def on_speech_worker_finished(self):

        worker = self.speech_worker

        if worker is not None and not worker.isRunning():

            self.speech_worker = None

    # =====================================================
    # PROCESS LOCAL COMMAND
    # =====================================================

    def process_local_command(self, message):

        """
        Process a command through the shared local command
        processor before sending anything to Gemini.

        Returns True if the request was handled locally.
        Returns False if it should be sent to Gemini.
        """

        result = command_processor.process_command(
            message,
            parent=self
        )

        if result.get("type") == "CHAT":
            return False

        response = result.get(
            "message",
            "The command could not be completed."
        )

        if result.get("success"):

            self.append_message(
                "J.A.R.V.I.S.",
                response,
                GREEN
            )

            self.status_label.setText(
                "LOCAL COMMAND COMPLETED"
            )

            self.status_label.setStyleSheet(
                f"color: {GREEN}; background: transparent;"
            )

        else:

            self.append_message(
                "J.A.R.V.I.S.",
                response,
                RED
            )

            self.status_label.setText(
                "LOCAL COMMAND NOT COMPLETED"
            )

            self.status_label.setStyleSheet(
                f"color: {RED}; background: transparent;"
            )

        self.connection_label.setText(
            "● LOCAL SYSTEM"
        )

        self.connection_label.setStyleSheet(
            f"color: {GOLD}; background: transparent;"
        )

        return True

    # =====================================================
    # SEND MESSAGE
    # =====================================================

    def send_message(self):

        message = self.message_input.text().strip()

        if not message:
            return

        if self.worker is not None and self.worker.isRunning():
            return

        self.append_message(
            "YOU",
            message,
            LIGHT_GOLD
        )

        self.message_input.clear()

        # -------------------------------------------------
        # LOCAL COMMAND ROUTING
        # -------------------------------------------------

        try:

            handled_locally = self.process_local_command(
                message
            )

            if handled_locally:

                self.message_input.setFocus()
                return

        except Exception as error:

            self.append_message(
                "SYSTEM ERROR",
                (
                    "The local command processor encountered "
                    "an error.\n\n"
                    f"Details: {error}"
                ),
                RED
            )

            self.status_label.setText(
                "LOCAL COMMAND PROCESSING FAILED"
            )

            self.status_label.setStyleSheet(
                f"color: {RED}; background: transparent;"
            )

            self.set_ready_status()
            self.message_input.setFocus()

            return

        # -------------------------------------------------
        # GEMINI CHAT ROUTING
        # -------------------------------------------------

        self.message_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        self.status_label.setText(
            "JARVIS IS PROCESSING YOUR REQUEST..."
        )

        self.status_label.setStyleSheet(
            f"color: {GOLD}; background: transparent;"
        )

        self.connection_label.setText(
            "● THINKING"
        )

        self.connection_label.setStyleSheet(
            f"color: {GOLD}; background: transparent;"
        )

        self.response_started = False
        self.response_cursor = None

        self.worker = AIWorker(
            self.ai_engine,
            message
        )

        self.worker.chunk_received.connect(
            self.handle_chunk
        )

        self.worker.response_ready.connect(
            self.handle_response
        )

        self.worker.error_occurred.connect(
            self.handle_error
        )

        self.worker.finished.connect(
            self.finish_request
        )

        self.worker.start()

    # =====================================================
    # HANDLE COMPLETED RESPONSE
    # =====================================================

    def handle_response(self, response):

        if self.closing:
            return

        self.finish_response_display()

        self.status_label.setText(
            "RESPONSE RECEIVED"
        )

        self.status_label.setStyleSheet(
            f"color: {GREEN}; background: transparent;"
        )

        self.connection_label.setText(
            "● AI READY"
        )

        self.connection_label.setStyleSheet(
            f"color: {GREEN}; background: transparent;"
        )

        # Speech is only started if explicitly enabled.
        self.speak_response(response)

    # =====================================================
    # HANDLE ERRORS
    # =====================================================

    def handle_error(self, error):

        if self.closing:
            return

        self.finish_response_display()

        self.append_message(
            "SYSTEM ERROR",
            (
                "I could not complete that request.\n\n"
                f"Details: {error}"
            ),
            RED
        )

        self.status_label.setText(
            "AI REQUEST FAILED"
        )

        self.status_label.setStyleSheet(
            f"color: {RED}; background: transparent;"
        )

        self.connection_label.setText(
            "● CONNECTION ERROR"
        )

        self.connection_label.setStyleSheet(
            f"color: {RED}; background: transparent;"
        )

    # =====================================================
    # FINISH REQUEST
    # =====================================================

    def finish_request(self):

        if self.closing:
            return

        self.message_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.clear_button.setEnabled(True)

        self.message_input.setFocus()

        self.worker = None

    # =====================================================
    # NEW CONVERSATION
    # =====================================================

    def clear_conversation(self):

        if self.worker is not None and self.worker.isRunning():
            return

        if (
            self.speech_worker is not None
            and self.speech_worker.isRunning()
        ):
            return

        answer = QMessageBox.question(
            self,
            "New Conversation",
            (
                "Start a new conversation?\n\n"
                "The current session conversation history "
                "will be cleared."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            self.ai_engine.reset_conversation()

            self.chat_output.clear()

            self.show_welcome_message()

            self.status_label.setText(
                "NEW CONVERSATION STARTED"
            )

            self.status_label.setStyleSheet(
                f"color: {GREEN}; background: transparent;"
            )

            self.connection_label.setText("● AI READY")

            self.connection_label.setStyleSheet(
                f"color: {GREEN}; background: transparent;"
            )

        except Exception as error:

            QMessageBox.warning(
                self,
                "Conversation Error",
                str(error)
            )

    # =====================================================
    # SAFE WINDOW CLOSING
    # =====================================================

    def closeEvent(self, event):

        self.closing = True

        # Stop any active speech before closing.
        if (
            self.speech_worker is not None
            and self.speech_worker.isRunning()
        ):

            if self.voice_engine is not None:

                try:
                    self.voice_engine.stop_speaking()
                except Exception as error:
                    print("Speech stop error:", error)

            # Give the playback worker a short time to stop.
            # If it is still generating speech, the global
            # worker reference keeps it alive until completion.
            self.speech_worker.wait(1500)

        # Preserve the existing AI worker shutdown behavior.
        if (
            self.worker is not None
            and self.worker.isRunning()
        ):

            self.worker.wait()

        event.accept()
