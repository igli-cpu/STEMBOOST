import queue
import threading
import time
import urllib.request
from pathlib import Path

import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice

# Curated list of Piper voices.
AVAILABLE_VOICES = {
    # --- US English (en_US) ---
    "amy": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium",
    "arctic": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/arctic/medium/en_US-arctic-medium",
    "bryce": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/bryce/medium/en_US-bryce-medium",
    "danny": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/danny/low/en_US-danny-low",
    "hfc_female": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/hfc_female/medium/en_US-hfc_female-medium",
    "hfc_male": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/hfc_male/medium/en_US-hfc_male-medium",
    "joe": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/joe/medium/en_US-joe-medium",
    "john": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/john/medium/en_US-john-medium",
    "kathleen": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/kathleen/low/en_US-kathleen-low",
    "kristin": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/kristin/medium/en_US-kristin-medium",
    "kusal": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/kusal/medium/en_US-kusal-medium",
    "l2arctic": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/l2arctic/medium/en_US-l2arctic-medium",
    "lessac": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/high/en_US-lessac-high",
    "libritts": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/libritts/high/en_US-libritts-high",
    "libritts_r": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/libritts_r/medium/en_US-libritts_r-medium",
    "ljspeech": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ljspeech/high/en_US-ljspeech-high",
    "norman": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/norman/medium/en_US-norman-medium",
    "reza_ibrahim": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/reza_ibrahim/medium/en_US-reza_ibrahim-medium",
    "ryan": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high",
    "sam": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/sam/medium/en_US-sam-medium",
    # --- GB English (en_GB) ---
    "alan": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium",
    "alba": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alba/medium/en_GB-alba-medium",
    "aru": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/aru/medium/en_GB-aru-medium",
    "cori": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/cori/high/en_GB-cori-high",
    "jenny_dioco": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium",
    "northern_english_male": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium",
    "semaine": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/semaine/medium/en_GB-semaine-medium",
    "southern_english_female": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/southern_english_female/low/en_GB-southern_english_female-low",
    "vctk": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/vctk/medium/en_GB-vctk-medium",
}


class TTSFacade:
    """Facade + Adapter over Piper High-Fidelity local neural TTS."""

    _instance = None
    _lock = threading.Lock()
    _initializing = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._initializing = True
                    cls._instance = TTSFacade()
                    cls._initializing = False
        return cls._instance

    def __init__(self):
        if not TTSFacade._initializing:
            raise RuntimeError("Use TTSFacade.get_instance() instead of TTSFacade()")

        self.enabled = True
        self._queue = queue.Queue()
        self._is_speaking_state = False
        self._abort_current = False

        self._current_volume = 1.0
        self._current_voice_id = "hfc_female"

        self._worker = threading.Thread(target=self._tts_worker, daemon=True)
        self._worker.start()

    def _ensure_model_exist(self, voice_id: str) -> Path:
        """Downloads a Piper voice model using pathlib if it doesn't exist yet."""
        if voice_id not in AVAILABLE_VOICES:
            raise ValueError(f"Voice '{voice_id}' not found in AVAILABLE_VOICES.")

        base_url = AVAILABLE_VOICES[voice_id]

        model_dir = Path("models/piper-tts")
        model_dir.mkdir(parents=True, exist_ok=True)

        model_name = f"{base_url.split('/')[-1]}.onnx"
        config_name = f"{model_name}.json"

        model_path = model_dir / model_name
        config_path = model_dir / config_name

        if not model_path.exists() or not config_path.exists():
            print(f"[TTS] Downloading '{voice_id}' voice model to {model_dir}...")
            urllib.request.urlretrieve(f"{base_url}.onnx", str(model_path))
            urllib.request.urlretrieve(f"{base_url}.onnx.json", str(config_path))
            print(f"[TTS] Download of '{voice_id}' complete!")

        return model_path

    def _tts_worker(self):
        """Runs continuously in the background, generating and playing audio."""
        try:
            active_voice_id = self._current_voice_id
            model_path = self._ensure_model_exist(active_voice_id)
            voice = PiperVoice.load(str(model_path))
            sample_rate = voice.config.sample_rate
        except Exception as e:
            print(f"[TTS Initialization Error]: {e}")
            return

        while True:
            try:
                command, payload = self._queue.get()

                if command == "SPEAK":
                    self._abort_current = False
                    self._is_speaking_state = True
                    try:
                        clean_text = str(payload).strip()
                        if not clean_text:
                            continue

                        audio_batches = []
                        for chunk in voice.synthesize(clean_text):
                            if self._abort_current:
                                break
                            audio_batches.append(chunk.audio_int16_bytes)

                        if self._abort_current or not audio_batches:
                            continue

                        raw_audio = b"".join(audio_batches)
                        if len(raw_audio) == 0:
                            continue

                        audio_np = (
                            np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32)
                            / 32768.0
                        )
                        audio_np *= self._current_volume

                        sd.play(audio_np, sample_rate)

                        duration = len(audio_np) / sample_rate
                        start_time = time.time()

                        while time.time() - start_time < duration:
                            if self._abort_current:
                                sd.stop()
                                break
                            time.sleep(0.05)

                    except Exception as e:
                        print(f"[TTS Error in synthesize/play]: {e}")
                    finally:
                        self._is_speaking_state = False

                elif command == "STOP":
                    self._is_speaking_state = False

                elif command == "VOLUME":
                    self._current_volume = payload

                elif command == "VOICE":
                    new_voice_id = payload
                    if new_voice_id != active_voice_id:
                        print(f"[TTS] Swapping voice to '{new_voice_id}'...")
                        try:
                            # Swap the engine on the fly
                            model_path = self._ensure_model_exist(new_voice_id)
                            voice = PiperVoice.load(str(model_path))
                            sample_rate = voice.config.sample_rate
                            active_voice_id = new_voice_id
                            print(f"[TTS] Voice swapped successfully.")
                        except Exception as e:
                            print(f"[TTS Error swapping voice]: {e}")

            except Exception as critical_error:
                print(f"[TTS CRITICAL WORKER ERROR]: {critical_error}")
                self._is_speaking_state = False

    def attach_to_root(self, root):
        pass

    def _clear_queue(self):
        """Safely empties the queue."""
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def speak(self, text):
        if not text or not self.enabled or not str(text).strip():
            return

        self._abort_current = True
        self._clear_queue()
        self._queue.put(("SPEAK", text))

    def stop(self):
        self._abort_current = True
        self._clear_queue()
        self._queue.put(("STOP", None))

    def set_volume(self, volume):
        """Sets playback volume (0.0 to 1.0)."""
        self._current_volume = max(0.0, min(volume, 1.0))
        self._queue.put(("VOLUME", self._current_volume))

    def set_voice(self, voice_id):
        """
        Changes the current voice.
        Valid options: 'lessac', 'ryan', 'alba', 'cori', 'arctic'.
        """
        if voice_id in AVAILABLE_VOICES:
            self._queue.put(("VOICE", voice_id))
        else:
            print(f"[TTS Warning] Voice '{voice_id}' not found. Skipping change.")

    @property
    def is_speaking(self):
        return self._is_speaking_state
