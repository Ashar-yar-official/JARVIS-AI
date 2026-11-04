
import queue
import threading
import time

import numpy as np
import sounddevice as sd

from math import gcd
from scipy.signal import resample_poly

from PySide6.QtCore import QThread, Signal


class BackgroundVoiceController(QThread):

    status_changed = Signal(str, str)
    command_ready = Signal(str)
    error_occurred = Signal(str)

    # -----------------------------------------------------
    # AUDIO CONFIGURATION
    # -----------------------------------------------------

    SAMPLE_RATE = 16000
    FRAME_DURATION = 0.08
    FRAME_SIZE = 1280

    WAKE_THRESHOLD = 0.50

    SPEECH_THRESHOLD = 0.012
    SILENCE_DURATION = 1.2

    MAX_COMMAND_DURATION = 15.0
    NO_SPEECH_TIMEOUT = 5.0

    WAKE_COOLDOWN = 1.5

    # -----------------------------------------------------
    # INITIALIZATION
    # -----------------------------------------------------

    def __init__(
        self,
        voice_engine,
        device=None,
        parent=None
    ):

        super().__init__(parent)

        self.voice_engine = voice_engine
        self.device = device

        self.detector = None
        self.stream = None

        self.native_sample_rate = self.SAMPLE_RATE

        self.audio_queue = queue.Queue(maxsize=40)

        self.callback_buffer = np.empty(
            0,
            dtype=np.int16
        )

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        self.manual_request = threading.Event()
        self.manual_finish = threading.Event()

        self.command_finished_event = threading.Event()

        self.capture_active = False
        self.capture_frames = []

        self.speech_started = False
        self.silence_frames = 0

        self.capture_started_at = 0.0
        self.ignore_audio_until = 0.0

        self.last_wake_time = 0.0

        self.waiting_for_command = False
        self.muted = False

        self._state_lock = threading.Lock()

    # =====================================================
    # PUBLIC CONTROLS
    # =====================================================

    def request_manual_capture(self):

        with self._state_lock:

            if self.capture_active:

                self.manual_finish.set()

            elif not self.waiting_for_command:

                self.manual_request.set()

    def set_muted(self, muted):

        self.muted = bool(muted)

        if self.muted:

            self.status_changed.emit(
                "MUTED",
                "Automatic wake-word detection is disabled. "
                "The HUD MIC button remains available."
            )

        else:

            self.status_changed.emit(
                "STANDBY",
                'Waiting for "Hey JARVIS".'
            )

    def toggle_mute(self):

        self.set_muted(not self.muted)

        return self.muted

    def pause(self):

        self.pause_event.set()

        self.status_changed.emit(
            "PAUSING",
            "Releasing the microphone."
        )

    def resume(self):

        self.pause_event.clear()

        self.status_changed.emit(
            "STARTING",
            "Restarting background listening."
        )

    def command_finished(self):

        self.command_finished_event.set()

    def stop(self):

        self.stop_event.set()

        self.pause_event.clear()
        self.command_finished_event.set()

        if self.isRunning():
            self.wait(15000)

    # =====================================================
    # INITIALIZE WAKE WORD DETECTOR
    # =====================================================

    def initialise_detector(self):

        try:

            from openwakeword.model import Model

            self.detector = Model(
                wakeword_models=["hey_jarvis"],
                inference_framework="onnx",
                vad_threshold=0.5
            )

            self.status_changed.emit(
                "STANDBY",
                'Local "Hey JARVIS" wake-word detector ready.'
            )

            return True

        except Exception as error:

            self.detector = None

            self.error_occurred.emit(
                "Wake-word initialization failed: " + str(error)
            )

            self.status_changed.emit(
                "MANUAL ONLY",
                "Wake-word detection unavailable. "
                "Use the HUD MIC button."
            )

            return False

    # =====================================================
    # CLEAR AUDIO QUEUE
    # =====================================================

    def clear_audio_queue(self):

        while True:

            try:
                self.audio_queue.get_nowait()

            except queue.Empty:
                break

        self.callback_buffer = np.empty(
            0,
            dtype=np.int16
        )

    # =====================================================
    # OPEN MICROPHONE
    # =====================================================

    def open_microphone(self):

        device_info = sd.query_devices(
            self.device,
            "input"
        )

        self.native_sample_rate = int(
            device_info["default_samplerate"]
        )

        max_channels = int(
            device_info["max_input_channels"]
        )

        if max_channels < 1:

            raise RuntimeError(
                "The selected microphone has no input channels."
            )

        if self.native_sample_rate <= 0:

            raise RuntimeError(
                "Invalid microphone sample rate."
            )

        self.clear_audio_queue()

        block_size = max(
            1,
            int(
                self.native_sample_rate *
                self.FRAME_DURATION
            )
        )

        self.stream = sd.InputStream(

            device=self.device,

            samplerate=self.native_sample_rate,

            channels=1,

            dtype="float32",

            blocksize=block_size,

            callback=self.audio_callback
        )

        self.stream.start()

    # =====================================================
    # CLOSE MICROPHONE
    # =====================================================

    def close_microphone(self):

        if self.stream is not None:

            try:

                if self.stream.active:
                    self.stream.stop()

                self.stream.close()

            except Exception as error:

                print(
                    "Microphone shutdown error:",
                    error
                )

            finally:

                self.stream = None

        self.clear_audio_queue()

    # =====================================================
    # AUDIO CALLBACK
    # =====================================================

    def audio_callback(
        self,
        indata,
        frames,
        time_info,
        status
    ):

        if status:

            print(
                "Microphone stream status:",
                status
            )

        try:

            audio = np.asarray(
                indata,
                dtype=np.float32
            ).reshape(-1)

            # Convert the native microphone sample rate
            # into the 16 kHz rate required by openWakeWord.

            if self.native_sample_rate != self.SAMPLE_RATE:

                divisor = gcd(
                    self.native_sample_rate,
                    self.SAMPLE_RATE
                )

                up = self.SAMPLE_RATE // divisor
                down = self.native_sample_rate // divisor

                audio = resample_poly(
                    audio,
                    up,
                    down
                )

            audio = np.clip(
                audio,
                -1.0,
                1.0
            )

            audio_int16 = (
                audio * 32767
            ).astype(np.int16)

            # Preserve leftover samples so that every
            # processed frame has exactly 1280 samples.

            self.callback_buffer = np.concatenate(
                (
                    self.callback_buffer,
                    audio_int16
                )
            )

            while len(self.callback_buffer) >= self.FRAME_SIZE:

                frame = self.callback_buffer[
                    :self.FRAME_SIZE
                ].copy()

                self.callback_buffer = self.callback_buffer[
                    self.FRAME_SIZE:
                ]

                try:

                    self.audio_queue.put_nowait(frame)

                except queue.Full:

                    try:
                        self.audio_queue.get_nowait()

                    except queue.Empty:
                        pass

                    try:

                        self.audio_queue.put_nowait(
                            frame
                        )

                    except queue.Full:
                        pass

        except Exception as error:

            print(
                "Audio callback error:",
                error
            )

    # =====================================================
    # START COMMAND RECORDING
    # =====================================================

    def begin_capture(self, source):

        self.capture_active = True

        self.capture_frames = []

        self.speech_started = False
        self.silence_frames = 0

        self.capture_started_at = time.monotonic()

        self.manual_finish.clear()

        if source == "WAKE":

            self.ignore_audio_until = (
                time.monotonic() + 0.35
            )

        else:

            self.ignore_audio_until = (
                time.monotonic()
            )

        self.status_changed.emit(
            "RECORDING",
            (
                "Wake phrase detected. Speak your command."
                if source == "WAKE"
                else "Microphone activated. Speak your command."
            )
        )

    # =====================================================
    # AUDIO LEVEL
    # =====================================================

    def get_audio_level(self, frame):

        audio = frame.astype(
            np.float32
        ) / 32768.0

        return float(
            np.sqrt(
                np.mean(audio ** 2)
            )
        )

    # =====================================================
    # PROCESS RECORDING FRAME
    # =====================================================

    def process_capture_frame(self, frame):

        now = time.monotonic()

        elapsed = now - self.capture_started_at

        if self.manual_finish.is_set():

            self.finish_capture()
            return

        if elapsed >= self.MAX_COMMAND_DURATION:

            self.finish_capture()
            return

        if now < self.ignore_audio_until:
            return

        self.capture_frames.append(
            frame.copy()
        )

        level = self.get_audio_level(frame)

        if level >= self.SPEECH_THRESHOLD:

            self.speech_started = True
            self.silence_frames = 0

        elif self.speech_started:

            self.silence_frames += 1

            silence_seconds = (
                self.silence_frames *
                self.FRAME_DURATION
            )

            if silence_seconds >= self.SILENCE_DURATION:

                self.finish_capture()
                return

        elif elapsed >= self.NO_SPEECH_TIMEOUT:

            self.cancel_capture(
                "No speech detected. Returning to standby."
            )

    # =====================================================
    # FINISH RECORDING
    # =====================================================

    def finish_capture(self):

        if not self.capture_active:
            return

        self.capture_active = False

        if not self.speech_started or not self.capture_frames:

            self.cancel_capture(
                "No understandable speech was detected."
            )

            return

        self.status_changed.emit(
            "TRANSCRIBING",
            "Transcribing your voice command."
        )

        try:

            audio_int16 = np.concatenate(
                self.capture_frames
            )

            audio_float = (
                audio_int16.astype(np.float32) /
                32768.0
            )

            recording = {

                "audio": audio_float.reshape(
                    -1,
                    1
                ),

                "sample_rate": self.SAMPLE_RATE
            }

            # Use the existing shared VoiceEngine.

            result = self.voice_engine.transcribe_audio(
                recording
            )

            if not result.get("success"):

                self.status_changed.emit(
                    "STANDBY",
                    result.get(
                        "message",
                        "Voice transcription failed."
                    )
                )

                return

            command = str(
                result.get(
                    "transcription",
                    ""
                )
            ).strip()

            if not command:

                self.status_changed.emit(
                    "STANDBY",
                    "No understandable command was detected."
                )

                return

            # Prevent another command from starting until
            # the current command has been processed.

            self.waiting_for_command = True

            self.command_finished_event.clear()

            self.status_changed.emit(
                "PROCESSING",
                "JARVIS is processing your voice command."
            )

            self.command_ready.emit(command)

            # Wait for ConnectedMainWindow to finish.

            while (
                not self.stop_event.is_set()
                and not self.command_finished_event.is_set()
            ):

                time.sleep(0.05)

        except Exception as error:

            self.error_occurred.emit(
                "Voice processing error: " + str(error)
            )

        finally:

            self.capture_frames = []

            self.speech_started = False
            self.silence_frames = 0

            self.manual_finish.clear()

            self.waiting_for_command = False

            self.last_wake_time = time.monotonic()

            if not self.stop_event.is_set():

                self.status_changed.emit(
                    "STANDBY",
                    (
                        "Background listening is muted."
                        if self.muted
                        else 'Waiting for "Hey JARVIS".'
                    )
                )

    # =====================================================
    # CANCEL RECORDING
    # =====================================================

    def cancel_capture(self, message):

        self.capture_active = False

        self.capture_frames = []

        self.speech_started = False
        self.silence_frames = 0

        self.manual_finish.clear()

        self.status_changed.emit(
            "STANDBY",
            message
        )

    # =====================================================
    # WAKE WORD DETECTION
    # =====================================================

    def detect_wake_word(self, frame):

        if self.detector is None:
            return False

        now = time.monotonic()

        if now - self.last_wake_time < self.WAKE_COOLDOWN:
            return False

        try:

            prediction = self.detector.predict(
                frame
            )

            if not prediction:
                return False

            score = max(
                float(value)
                for value in prediction.values()
            )

            return score >= self.WAKE_THRESHOLD

        except Exception as error:

            self.error_occurred.emit(
                "Wake-word detection error: " + str(error)
            )

            return False

    # =====================================================
    # MAIN THREAD LOOP
    # =====================================================

    def run(self):

        try:

            self.initialise_detector()

            while not self.stop_event.is_set():

                # -----------------------------------------
                # PAUSE MICROPHONE
                # -----------------------------------------

                if self.pause_event.is_set():

                    self.close_microphone()

                    self.capture_active = False
                    self.capture_frames = []

                    self.manual_request.clear()
                    self.manual_finish.clear()

                    self.status_changed.emit(
                        "PAUSED",
                        "Microphone released for another module."
                    )

                    time.sleep(0.1)

                    continue

                # -----------------------------------------
                # OPEN MICROPHONE
                # -----------------------------------------

                if self.stream is None:

                    try:

                        self.open_microphone()

                        self.status_changed.emit(
                            "STANDBY",
                            (
                                "Microphone active. Background "
                                'listening for "Hey JARVIS".'
                            )
                        )

                    except Exception as error:

                        self.error_occurred.emit(
                            "Could not open microphone: " +
                            str(error)
                        )

                        self.status_changed.emit(
                            "MIC ERROR",
                            "Check microphone connection and permissions."
                        )

                        time.sleep(2)

                        continue

                # -----------------------------------------
                # DIRECT HUD MIC BUTTON
                # -----------------------------------------

                if (
                    self.manual_request.is_set()
                    and not self.capture_active
                    and not self.waiting_for_command
                ):

                    self.manual_request.clear()

                    self.begin_capture(
                        "MANUAL"
                    )

                # -----------------------------------------
                # GET AUDIO FRAME
                # -----------------------------------------

                try:

                    frame = self.audio_queue.get(
                        timeout=0.1
                    )

                except queue.Empty:
                    continue

                # -----------------------------------------
                # RECORD COMMAND
                # -----------------------------------------

                if self.capture_active:

                    self.process_capture_frame(
                        frame
                    )

                    continue

                if self.waiting_for_command:
                    continue

                # -----------------------------------------
                # LOCAL WAKE WORD
                # -----------------------------------------

                if self.muted:
                    continue

                if self.detect_wake_word(frame):

                    self.last_wake_time = time.monotonic()

                    self.begin_capture(
                        "WAKE"
                    )

        except Exception as error:

            self.error_occurred.emit(
                "Background voice controller error: " +
                str(error)
            )

        finally:

            self.close_microphone()

            self.capture_active = False
            self.waiting_for_command = False

            self.status_changed.emit(
                "OFFLINE",
                "Background microphone service stopped."
            )
