
from PySide6.QtWidgets import QMessageBox
from shiboken6 import isValid

from interface.main_window import MainWindow
from interface.chat_dialog import ChatDialog

from modules.command_processor import command_processor
from modules.voice_engine import VoiceEngine
from modules.background_voice_controller import BackgroundVoiceController


class ConnectedMainWindow(MainWindow):

    def __init__(self, ai_engine=None, ai_error=None):

        super().__init__()

        self.ai_engine = ai_engine
        self.ai_error = ai_error
        self.chat_dialog = None

        self._is_shutting_down = False

        # Tracks whether browser audio was muted specifically
        # for a manual microphone recording.
        self._browser_muted_for_manual_capture = False

        # -------------------------------------------------
        # INITIALIZE SHARED VOICE ENGINE
        # -------------------------------------------------

        self.voice_engine = None
        self.voice_error = None

        try:

            self.voice_engine = VoiceEngine()

        except Exception as error:

            self.voice_error = str(error)

        # -------------------------------------------------
        # INITIALIZE BACKGROUND VOICE CONTROLLER
        # -------------------------------------------------

        self.background_voice = None
        self.background_voice_error = None

        if self.voice_engine is not None:

            try:

                self.background_voice = BackgroundVoiceController(
                    voice_engine=self.voice_engine,
                    parent=self
                )

                self.background_voice.status_changed.connect(
                    self.update_voice_status
                )

                self.background_voice.command_ready.connect(
                    self.handle_voice_command
                )

                self.background_voice.error_occurred.connect(
                    self.handle_voice_error
                )

                self.background_voice.start()

            except Exception as error:

                self.background_voice_error = str(error)

        self.update_ai_status()

        # -------------------------------------------------
        # CONNECT HUD MIC BUTTON DIRECTLY
        # -------------------------------------------------

        try:

            self.mic_button.clicked.disconnect()

        except (TypeError, RuntimeError):
            pass

        self.mic_button.clicked.connect(
            self.activate_microphone
        )

        self.mic_button.setToolTip(
            "Click to start recording. Click again to finish."
        )

    # =====================================================
    # QT OBJECT VALIDATION
    # =====================================================

    def is_ui_available(self, widget=None):

        """
        Check whether the window and requested Qt widget
        still have valid underlying C++ objects.
        """

        if self._is_shutting_down:
            return False

        try:

            if not isValid(self):
                return False

            if widget is not None and not isValid(widget):
                return False

            return True

        except (RuntimeError, TypeError):
            return False

    # =====================================================
    # UPDATE AI STATUS
    # =====================================================

    def update_ai_status(self):

        if not self.is_ui_available(self.ai_status):
            return

        if self.ai_engine:

            status = self.ai_engine.get_status()

            if status.get("enabled") and status.get("configured"):

                self.ai_status.setText("● GEMINI ONLINE")

                self.ai_status.setStyleSheet(
                    "color: #45D69A; background: transparent;"
                )

                return

        self.ai_status.setText("● AI UNAVAILABLE")

        self.ai_status.setStyleSheet(
            "color: #E9AD45; background: transparent;"
        )

    # =====================================================
    # UPDATE DASHBOARD STATUS
    # =====================================================

    def update_command_status(self, title, description):

        if not self.is_ui_available(self.task_status):
            return

        self.task_status.setText(str(title))
        self.task_description.setText(str(description))

    # =====================================================
    # CONTROL INTERNAL BROWSER AUDIO
    # =====================================================

    def set_embedded_browser_audio_muted(self, muted):

        """
        Mute or unmute the internal browser without pausing
        or stopping its video and audio elements.

        This only changes the WebEngine page's audio output.
        """

        if not self.is_ui_available():
            return False

        browser = getattr(
            self,
            "embedded_browser",
            None
        )

        if browser is None:
            return False

        if not self.is_ui_available(browser):
            return False

        if not getattr(self, "browser_is_open", False):
            return False

        try:

            web_view = getattr(
                browser,
                "browser",
                None
            )

            if web_view is None or not isValid(web_view):
                return False

            page = web_view.page()

            if page is None:
                return False

            page.setAudioMuted(bool(muted))

            self._browser_muted_for_manual_capture = bool(muted)

            if muted:

                print(
                    "JARVIS: Internal browser audio muted for microphone recording."
                )

            else:

                print(
                    "JARVIS: Internal browser audio restored."
                )

            return True

        except Exception as error:

            print(
                "JARVIS browser audio control error:",
                error
            )

            return False

    # =====================================================
    # RESTORE BROWSER AUDIO AFTER RECORDING
    # =====================================================

    def restore_browser_audio_after_recording(self):

        if not self._browser_muted_for_manual_capture:
            return

        self.set_embedded_browser_audio_muted(False)

        # Clear the flag even if the browser has been closed.
        self._browser_muted_for_manual_capture = False

    # =====================================================
    # VOICE STATUS UPDATES
    # =====================================================

    def update_voice_status(self, state, description):

        if not self.is_ui_available(self.reactor):
            return

        state = str(state).upper()

        # If recording ends because of silence, timeout,
        # transcription, or an error, restore browser audio.
        if (
            self._browser_muted_for_manual_capture
            and state in (
                "TRANSCRIBING",
                "PROCESSING",
                "STANDBY",
                "MIC ERROR",
                "OFFLINE",
                "PAUSED"
            )
        ):

            self.restore_browser_audio_after_recording()

        self.mic_button.setToolTip(
            f"Microphone: {state} — {description}"
        )

        if state == "RECORDING":

            self.reactor.set_state("LISTENING")

            self.reactor_state.setText(
                "CORE STATUS: LISTENING"
            )

            self.reactor_state.setStyleSheet(
                "color: #E9AD45; background: transparent;"
            )

            self.update_command_status(
                "LISTENING",
                description
            )

        elif state == "TRANSCRIBING":

            self.reactor.set_state("THINKING")

            self.reactor_state.setText(
                "CORE STATUS: TRANSCRIBING VOICE"
            )

            self.update_command_status(
                "VOICE PROCESSING",
                description
            )

        elif state == "PROCESSING":

            self.reactor.set_state("THINKING")

            self.reactor_state.setText(
                "CORE STATUS: PROCESSING VOICE COMMAND"
            )

            self.update_command_status(
                "COMMAND RECEIVED",
                description
            )

        elif state == "STANDBY":

            self.reactor.set_state("IDLE")

            self.reactor_state.setText(
                "CORE STATUS: SYSTEM OPERATIONAL"
            )

            self.reactor_state.setStyleSheet(
                "color: #45D69A; background: transparent;"
            )

            self.update_command_status(
                "STANDBY",
                description
            )

        elif state in ("PAUSED", "PAUSING"):

            self.mic_button.setToolTip(
                "Background microphone paused while Voice department is open."
            )

        elif state == "MUTED":

            self.update_command_status(
                "WAKE WORD MUTED",
                description
            )

        elif state == "MIC ERROR":

            self.update_command_status(
                "MICROPHONE ERROR",
                description
            )

        elif state == "MANUAL ONLY":

            self.update_command_status(
                "MANUAL VOICE MODE",
                description
            )

        elif state == "OFFLINE":

            self.mic_button.setToolTip(
                "Background microphone is offline."
            )

    # =====================================================
    # VOICE ERROR HANDLING
    # =====================================================

    def handle_voice_error(self, message):

        if not self.is_ui_available(self.mic_button):
            return

        print("JARVIS Voice Error:", message)

        self.mic_button.setToolTip(
            "Voice system warning: " + str(message)
        )

        # Restore browser audio if recording fails.
        self.restore_browser_audio_after_recording()

    # =====================================================
    # DIRECT HUD MICROPHONE ACTIVATION
    # =====================================================

    def activate_microphone(self):

        if not self.is_ui_available(self.mic_button):
            return

        if self.background_voice is None:

            QMessageBox.warning(
                self,
                "Microphone Unavailable",
                (
                    "The JARVIS voice system could not initialise.\n\n"
                    f"{self.voice_error or self.background_voice_error or 'Check your microphone and audio dependencies.'}"
                )
            )

            return

        if not self.background_voice.isRunning():

            QMessageBox.warning(
                self,
                "Microphone Offline",
                "The background voice controller is not running."
            )

            return

        # ---------------------------------------------
        # SECOND CLICK: FINISH RECORDING
        # ---------------------------------------------

        if self.background_voice.capture_active:

            # Restore browser audio immediately.
            self.restore_browser_audio_after_recording()

            self.background_voice.request_manual_capture()

            self.mic_button.setToolTip(
                "Recording finished. Processing your command."
            )

            return

        # ---------------------------------------------
        # FIRST CLICK: START RECORDING
        # ---------------------------------------------

        if self.background_voice.waiting_for_command:
            return

        # Mute browser audio without stopping its video.
        self.set_embedded_browser_audio_muted(True)

        self.background_voice.request_manual_capture()

    # =====================================================
    # CLOSE BROWSER AFTER NON-BROWSER VOICE COMMANDS
    # =====================================================

    def restore_reactor_after_voice_command(self):

        """
        Restore the reactor display when a spoken command
        is handled by Gemini or a local system action.
        """

        if not self.is_ui_available():
            return

        if not getattr(self, "browser_is_open", False):
            return

        try:

            self.close_embedded_browser()

        except Exception as error:

            print(
                "JARVIS browser restoration warning:",
                error
            )

    # =====================================================
    # PROCESS SPOKEN COMMAND
    # =====================================================

    def handle_voice_command(self, command):

        """
        Process a spoken command.

        Browser playback is no longer stopped here.
        The microphone controls browser muting separately.
        """

        if not self.is_ui_available(self.reactor):
            return

        command = str(command or "").strip()

        if not command:
            return

        self.handle_command(
            command,
            voice_input=True
        )

    # =====================================================
    # PROCESS COMMAND
    # =====================================================

    def handle_command(self, command, voice_input=False):

        if not self.is_ui_available(self.reactor):
            return

        command = str(command).strip()

        if not command:
            return

        try:

            self.update_command_status(
                "COMMAND RECEIVED",
                "JARVIS is analysing the request..."
            )

            self.reactor.set_state("THINKING")

            self.reactor_state.setText(
                "CORE STATUS: PROCESSING REQUEST"
            )

            result = command_processor.process_command(
                command,
                parent=self
            )

            command_type = result.get("type")

            # ---------------------------------------------
            # NORMAL QUESTION: SEND TO GEMINI
            # ---------------------------------------------

            if command_type == "CHAT":

                if voice_input:
                    self.restore_reactor_after_voice_command()

                self.update_command_status(
                    "AI REQUEST",
                    "Forwarding your question to Gemini..."
                )

                self.open_chat(
                    result.get("message", command)
                )

                return

            # ---------------------------------------------
            # EMBEDDED BROWSER
            # ---------------------------------------------

            if command_type == "EMBEDDED_BROWSER":

                success = result.get("success", False)

                message = result.get(
                    "message",
                    "Embedded browser request received."
                )

                if not success:

                    self.update_command_status(
                        "BROWSER REQUEST DENIED",
                        message
                    )

                    self.reactor.set_state("IDLE")

                    self.reactor_state.setText(
                        "CORE STATUS: BROWSER REQUEST DENIED"
                    )

                    self.reactor_state.setStyleSheet(
                        "color: #E9AD45; background: transparent;"
                    )

                    return

                query = result.get("query", "").strip()

                browser_type = result.get(
                    "browser_type",
                    "google"
                )

                if not query:

                    self.update_command_status(
                        "BROWSER ERROR",
                        "No search query was provided."
                    )

                    self.reactor.set_state("IDLE")

                    self.reactor_state.setText(
                        "CORE STATUS: BROWSER ERROR"
                    )

                    return

                self.show_embedded_browser(
                    query=query,
                    browser_type=browser_type
                )

                destination = (
                    "Google"
                    if browser_type == "google"
                    else "YouTube"
                )

                self.update_command_status(
                    "BROWSER ACTIVE",
                    f"{destination} search: {query}"
                )

                self.reactor_state.setText(
                    "CORE STATUS: WEB INTERFACE ACTIVE"
                )

                self.reactor_state.setStyleSheet(
                    "color: #45D69A; background: transparent;"
                )

                return

            # ---------------------------------------------
            # LOCAL OR EXTERNAL ACTION RESULT
            # ---------------------------------------------

            if voice_input:
                self.restore_reactor_after_voice_command()

            success = result.get("success", False)

            message = result.get(
                "message",
                "Command processing completed."
            )

            if success:

                self.update_command_status(
                    "COMMAND COMPLETED",
                    message
                )

                self.reactor.set_state("IDLE")

                self.reactor_state.setText(
                    "CORE STATUS: SYSTEM OPERATIONAL"
                )

                self.reactor_state.setStyleSheet(
                    "color: #45D69A; background: transparent;"
                )

            else:

                self.update_command_status(
                    "COMMAND NOT COMPLETED",
                    message
                )

                self.reactor.set_state("IDLE")

                self.reactor_state.setText(
                    "CORE STATUS: ACTION NOT COMPLETED"
                )

                self.reactor_state.setStyleSheet(
                    "color: #E9AD45; background: transparent;"
                )

        except Exception as error:

            if not self.is_ui_available(self.reactor):
                print("Command Handling Error:", error)
                return

            self.update_command_status(
                "COMMAND ERROR",
                str(error)
            )

            self.reactor.set_state("IDLE")

            self.reactor_state.setText(
                "CORE STATUS: COMMAND ERROR"
            )

            self.reactor_state.setStyleSheet(
                "color: #E9AD45; background: transparent;"
            )

            print("Command Handling Error:", error)

        finally:

            if (
                not self._is_shutting_down
                and self.background_voice is not None
            ):

                try:
                    self.background_voice.command_finished()

                except (RuntimeError, AttributeError):
                    pass

    # =====================================================
    # OPEN CHAT WINDOW
    # =====================================================

    def open_chat(self, initial_message=""):

        if not self.is_ui_available():
            return

        if not self.ai_engine:

            QMessageBox.warning(
                self,
                "AI Unavailable",
                (
                    "JARVIS could not initialise the Gemini AI provider.\n\n"
                    f"{self.ai_error or 'Check your internet connection and API configuration.'}"
                )
            )

            self.update_command_status(
                "AI UNAVAILABLE",
                "Gemini could not be initialised."
            )

            return

        if (
            self.chat_dialog is not None
            and isValid(self.chat_dialog)
            and self.chat_dialog.isVisible()
        ):

            self.chat_dialog.raise_()
            self.chat_dialog.activateWindow()

        else:

            self.chat_dialog = ChatDialog(
                self.ai_engine,
                self,
                voice_engine=self.voice_engine
            )

            self.chat_dialog.finished.connect(
                self.clear_chat_reference
            )

            self.chat_dialog.show()

        if initial_message and self.chat_dialog is not None:

            self.chat_dialog.message_input.setText(
                initial_message
            )

            self.chat_dialog.send_message()

    # =====================================================
    # CLEAR CHAT REFERENCE
    # =====================================================

    def clear_chat_reference(self):

        self.chat_dialog = None

    # =====================================================
    # DASHBOARD COMMAND BAR
    # =====================================================

    def send_command(self):

        if not self.is_ui_available(self.command_input):
            return

        command = self.command_input.text().strip()

        if not command:
            return

        self.command_input.clear()

        self.handle_command(command)

    # =====================================================
    # VOICE DEPARTMENT INTEGRATION
    # =====================================================

    def open_department(self, key):

        if not self.is_ui_available():
            return

        super().open_department(key)

        if key != "VOICE":
            return

        dialog = self.department_dialogs.get(key)

        if dialog is None:
            return

        if self.background_voice is not None:

            self.background_voice.pause()

        if hasattr(dialog, "command_received"):

            if not getattr(
                dialog,
                "_jarvis_command_connected",
                False
            ):

                dialog.command_received.connect(
                    self.handle_voice_command
                )

                dialog._jarvis_command_connected = True

        if not getattr(
            dialog,
            "_jarvis_resume_connected",
            False
        ):

            dialog.finished.connect(
                self.resume_background_voice
            )

            dialog._jarvis_resume_connected = True

    # =====================================================
    # RESUME BACKGROUND VOICE
    # =====================================================

    def resume_background_voice(self, *args):

        if not self.is_ui_available():
            return

        if (
            self.background_voice is not None
            and self.background_voice.isRunning()
        ):

            self.background_voice.resume()

    # =====================================================
    # SAFE APPLICATION SHUTDOWN
    # =====================================================

    def closeEvent(self, event):

        self._is_shutting_down = True

        # Restore browser audio state if the application
        # closes during a manual recording.
        self.restore_browser_audio_after_recording()

        voice_controller = self.background_voice

        if voice_controller is not None:

            for signal, slot in (
                (
                    voice_controller.status_changed,
                    self.update_voice_status
                ),
                (
                    voice_controller.command_ready,
                    self.handle_voice_command
                ),
                (
                    voice_controller.error_occurred,
                    self.handle_voice_error
                )
            ):

                try:
                    signal.disconnect(slot)

                except (TypeError, RuntimeError):
                    pass

            try:

                voice_controller.stop()

                if voice_controller.isRunning():

                    if not voice_controller.wait(5000):

                        print(
                            "WARNING: Background voice controller "
                            "did not stop within 5 seconds."
                        )

            except RuntimeError as error:

                print(
                    "Voice shutdown error:",
                    error
                )

        super().closeEvent(event)
