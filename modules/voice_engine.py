
import io
import tempfile
import wave
import winsound
import threading

import numpy as np
import sounddevice as sd

from math import gcd
from scipy.io.wavfile import write as write_wav
from scipy.signal import resample_poly

from google.genai import types
from core.gemini_provider import GeminiProvider


class VoiceEngine:

    def __init__(
        self,
        transcription_model="gemini-3.5-flash-lite",
        speech_model="gemini-3.8-flash-tts",
        voice_name="Charon"
    ):

        self.provider = GeminiProvider()
        self.client = self.provider.client

        self.transcription_model = transcription_model
        self.speech_model = speech_model
        self.voice_name = voice_name

        self.sample_rate = 16000
        self.recording = False

        # Tracks cancellation of the current speech operation.
        self._speech_stop_event = threading.Event()

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def get_status(self):

        return {
            "available": self.client is not None,
            "provider": "Google Gemini",
            "transcription_model": self.transcription_model,
            "speech_model": self.speech_model,
            "voice": self.voice_name,
            "recording": self.recording
        }

    # --------------------------------------------------
    # AUDIO DEVICES
    # --------------------------------------------------

    def get_audio_devices(self):

        devices = sd.query_devices()

        input_devices = []
        output_devices = []

        for index, device in enumerate(devices):

            if device["max_input_channels"] > 0:

                input_devices.append({
                    "index": index,
                    "name": device["name"],
                    "channels": device["max_input_channels"],
                    "sample_rate": device["default_samplerate"]
                })

            if device["max_output_channels"] > 0:

                output_devices.append({
                    "index": index,
                    "name": device["name"],
                    "channels": device["max_output_channels"],
                    "sample_rate": device["default_samplerate"]
                })

        return {
            "input_devices": input_devices,
            "output_devices": output_devices
        }

    # --------------------------------------------------
    # RECORD AUDIO
    # --------------------------------------------------

    def record_audio(self, duration=5, device=1):

        if duration < 1 or duration > 60:
            raise ValueError(
                "Recording duration must be between 1 and 60 seconds."
            )

        try:

            device_info = sd.query_devices(device, "input")

            native_rate = int(device_info["default_samplerate"])
            max_channels = int(device_info["max_input_channels"])

            if max_channels < 1:
                raise RuntimeError(
                    "Selected device has no input channels."
                )

            channels = min(2, max_channels)

            self.recording = True

            try:

                audio = sd.rec(
                    int(duration * native_rate),
                    samplerate=native_rate,
                    channels=channels,
                    dtype="float32",
                    device=device
                )

                sd.wait()

            finally:
                self.recording = False

            return {
                "audio": audio,
                "sample_rate": native_rate
            }

        except Exception:
            self.recording = False
            raise

    # --------------------------------------------------
    # CONVERT TO MONO
    # --------------------------------------------------

    def convert_to_mono(self, audio):

        audio = np.asarray(audio, dtype=np.float32)

        if audio.ndim == 2:

            if audio.shape[1] > 1:
                audio = np.mean(audio, axis=1)
            else:
                audio = audio[:, 0]

        return audio

    # --------------------------------------------------
    # RESAMPLE AUDIO
    # --------------------------------------------------

    def resample_audio(self, audio, original_rate):

        if original_rate == self.sample_rate:
            return audio

        divisor = gcd(
            int(original_rate),
            self.sample_rate
        )

        up = self.sample_rate // divisor
        down = int(original_rate) // divisor

        audio = resample_poly(
            audio,
            up,
            down
        )

        return audio.astype(np.float32)

    # --------------------------------------------------
    # NORMALIZE AUDIO
    # --------------------------------------------------

    def normalize_audio(self, audio):

        audio = np.asarray(audio, dtype=np.float32)

        if len(audio) == 0:
            return audio

        audio = audio - np.mean(audio)

        peak = float(np.max(np.abs(audio)))

        if peak < 0.0001:
            return audio

        rms = float(np.sqrt(np.mean(audio ** 2)))

        if rms < 0.0001:
            return audio

        target_rms = 0.10

        gain = target_rms / rms
        gain = min(gain, 8.0)

        audio = audio * gain
        audio = np.clip(audio, -0.98, 0.98)

        return audio.astype(np.float32)

    # --------------------------------------------------
    # PREPARE AUDIO
    # --------------------------------------------------

    def prepare_audio(self, recording):

        audio = recording["audio"]
        original_rate = recording["sample_rate"]

        audio = self.convert_to_mono(audio)

        audio = self.resample_audio(
            audio,
            original_rate
        )

        audio = self.normalize_audio(audio)

        return audio

    # --------------------------------------------------
    # SAVE RECORDING
    # --------------------------------------------------

    def save_recording(self, recording, file_path=None):

        audio = self.prepare_audio(recording)

        if file_path is None:

            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )

            file_path = temp_file.name
            temp_file.close()

        audio_int16 = np.int16(
            np.clip(audio, -1.0, 1.0) * 32767
        )

        write_wav(
            file_path,
            self.sample_rate,
            audio_int16
        )

        return file_path

    # --------------------------------------------------
    # CREATE WAV BYTES
    # --------------------------------------------------

    def create_wav_bytes(self, audio):

        audio_int16 = np.int16(
            np.clip(audio, -1.0, 1.0) * 32767
        )

        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav_file:

            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)

            wav_file.writeframes(
                audio_int16.tobytes()
            )

        return buffer.getvalue()

    # --------------------------------------------------
    # TRANSCRIBE AUDIO
    # --------------------------------------------------

    def transcribe_audio(self, recording):

        try:

            audio = self.prepare_audio(recording)

            if len(audio) == 0:

                return {
                    "success": False,
                    "transcription": "",
                    "message": "No audio was recorded."
                }

            rms = float(
                np.sqrt(np.mean(audio ** 2))
            )

            if rms < 0.001:

                return {
                    "success": False,
                    "transcription": "",
                    "message": "Audio is too quiet. Check your microphone."
                }

            audio_bytes = self.create_wav_bytes(audio)

            instruction = """
You are an accurate speech recognition system.

Transcribe the supplied audio recording exactly as spoken.

Requirements:

1. Listen to the entire recording from beginning to end.
2. Write each spoken word only once.
3. Do not repeat phrases or sentences.
4. Do not summarize or paraphrase.
5. Do not answer questions spoken in the audio.
6. Do not invent words that cannot be heard.
7. Preserve the speaker's original wording.
8. Include the beginning and ending of the recording.
9. Use appropriate punctuation.
10. Return only the transcription.

Important:
The recording contains one continuous speech sample.
Do not treat it as multiple separate recordings.

If there is no intelligible speech, return an empty response.
"""

            response = self.client.models.generate_content(

                model=self.transcription_model,

                contents=[
                    instruction,
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type="audio/wav"
                    )
                ],

                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=512
                )
            )

            transcription = (response.text or "").strip()

            if not transcription:

                return {
                    "success": False,
                    "transcription": "",
                    "message": "No understandable speech detected."
                }

            return {
                "success": True,
                "transcription": transcription,
                "message": "Speech transcribed successfully."
            }

        except Exception as error:

            error_message = str(error)

            print("Transcription Error:", error_message)

            if "503" in error_message:
                message = "Gemini service is temporarily unavailable."

            elif "429" in error_message:
                message = "Gemini API rate limit reached."

            elif "401" in error_message or "403" in error_message:
                message = "Gemini API authentication failed."

            else:
                message = "Transcription failed: " + error_message

            return {
                "success": False,
                "transcription": "",
                "message": message
            }

    # --------------------------------------------------
    # LISTEN
    # --------------------------------------------------

    def listen(self, duration=5, device=1):

        try:

            recording = self.record_audio(
                duration=duration,
                device=device
            )

            return self.transcribe_audio(recording)

        except Exception as error:

            return {
                "success": False,
                "transcription": "",
                "message": str(error)
            }

    # --------------------------------------------------
    # GENERATE SPEECH
    # --------------------------------------------------

    def generate_speech(self, text):

        try:

            if not text or not text.strip():

                return {
                    "success": False,
                    "audio": None,
                    "mime_type": None,
                    "message": "No text provided."
                }

            if self.client is None:
                raise RuntimeError("Gemini client is unavailable.")

            response = self.client.models.generate_content(

                model=self.speech_model,

                contents=text,

                config=types.GenerateContentConfig(

                    response_modalities=["AUDIO"],

                    speech_config=types.SpeechConfig(

                        voice_config=types.VoiceConfig(

                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name
                            )
                        )
                    )
                )
            )

            if not response.candidates:
                raise RuntimeError("Gemini returned no response.")

            content = response.candidates[0].content

            for part in content.parts:

                if part.inline_data and part.inline_data.data:

                    return {
                        "success": True,
                        "audio": part.inline_data.data,
                        "mime_type": part.inline_data.mime_type,
                        "message": "Speech generated successfully."
                    }

            return {
                "success": False,
                "audio": None,
                "mime_type": None,
                "message": "Gemini returned no audio."
            }

        except Exception as error:

            return {
                "success": False,
                "audio": None,
                "mime_type": None,
                "message": str(error)
            }

    # --------------------------------------------------
    # STOP SPEECH PLAYBACK
    # --------------------------------------------------

    def stop_speaking(self):

        self._speech_stop_event.set()

        try:

            # Interrupt currently playing Windows audio.
            winsound.PlaySound(
                None,
                winsound.SND_PURGE
            )

        except Exception as error:

            print("Windows audio stop warning:", error)

            try:
                sd.stop()
            except Exception:
                pass

        return True

    # --------------------------------------------------
    # PLAY AUDIO
    # --------------------------------------------------

    def play_audio(
        self,
        audio_data,
        sample_rate=24000,
        mime_type=None
    ):

        try:

            if not audio_data:
                raise ValueError("Audio data is empty.")

            if self._speech_stop_event.is_set():
                return False

            audio_data = bytes(audio_data)

            # Case 1: Gemini returned a complete WAV file.

            if audio_data.startswith(b"RIFF") and audio_data[8:12] == b"WAVE":

                with wave.open(io.BytesIO(audio_data), "rb") as wav_file:

                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    frame_rate = wav_file.getframerate()
                    compression = wav_file.getcomptype()

                    if compression != "NONE":
                        raise ValueError(
                            "Compressed WAV audio is not supported."
                        )

                    if sample_width != 2:
                        raise ValueError(
                            "WAV audio must use 16-bit PCM samples."
                        )

                    if channels not in (1, 2):
                        raise ValueError(
                            "WAV audio must have one or two channels."
                        )

                    if frame_rate <= 0:
                        raise ValueError(
                            "Invalid WAV sample rate."
                        )

                    frames = wav_file.readframes(
                        wav_file.getnframes()
                    )

                    if not frames:
                        raise ValueError("WAV contains no audio frames.")

                if self._speech_stop_event.is_set():
                    return False

                winsound.PlaySound(
                    audio_data,
                    winsound.SND_MEMORY
                )

                return not self._speech_stop_event.is_set()

            # Case 2: Gemini returned raw PCM audio.

            buffer = io.BytesIO()

            with wave.open(buffer, "wb") as wav_file:

                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)

                wav_file.writeframes(audio_data)

            if self._speech_stop_event.is_set():
                return False

            winsound.PlaySound(
                buffer.getvalue(),
                winsound.SND_MEMORY
            )

            return not self._speech_stop_event.is_set()

        except Exception as error:

            print("Audio Playback Error:", error)

            return False

    # --------------------------------------------------
    # SPEAK
    # --------------------------------------------------

    def speak(self, text):

        # Reset cancellation state for a new speech request.
        self._speech_stop_event.clear()

        result = self.generate_speech(text)

        if not result["success"]:
            return result

        # Do not play audio if cancellation happened
        # while Gemini was generating the speech.
        if self._speech_stop_event.is_set():

            return {
                "success": False,
                "message": "Speech playback was cancelled."
            }

        played = self.play_audio(
            result["audio"],
            sample_rate=24000,
            mime_type=result.get("mime_type")
        )

        if self._speech_stop_event.is_set():

            return {
                "success": False,
                "message": "Speech playback was stopped."
            }

        return {
            "success": played,
            "message": (
                "Speech played successfully."
                if played
                else "Speech playback failed."
            )
        }

    # --------------------------------------------------
    # TEST MICROPHONE
    # --------------------------------------------------

    def test_microphone(self, duration=5, device=1):

        try:

            recording = self.record_audio(
                duration=duration,
                device=device
            )

            audio = self.prepare_audio(recording)

            rms = float(np.sqrt(np.mean(audio ** 2)))
            peak = float(np.max(np.abs(audio)))

            return {
                "success": True,
                "rms": round(rms, 4),
                "peak": round(peak, 4),
                "sample_rate": self.sample_rate,
                "duration": round(
                    len(audio) / self.sample_rate,
                    2
                ),
                "message": "Microphone recording completed."
            }

        except Exception as error:

            return {
                "success": False,
                "message": str(error)
            }

    # --------------------------------------------------
    # TEST VOICE
    # --------------------------------------------------

    def test_voice(self):

        result = self.generate_speech(
            "Hello. I am JARVIS, your personal desktop assistant."
        )

        if not result["success"]:
            return result

        self._speech_stop_event.clear()

        played = self.play_audio(
            result["audio"],
            sample_rate=24000,
            mime_type=result.get("mime_type")
        )

        return {
            "success": played,
            "message": (
                "Voice test completed."
                if played
                else "Voice playback failed."
            )
        }
