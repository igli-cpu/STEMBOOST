import threading


class TTSFacade:
    """Facade + Adapter over pyttsx3 for text-to-speech.

    Provides a simplified interface (speak, stop, set_rate) and adapts the
    pyttsx3 engine to our application's needs. Uses the Singleton pattern
    so one engine instance is shared across the entire app.
    """

    _instance = None
    _lock = threading.Lock()
    _initializing = False  # Guard against direct instantiation

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
            raise RuntimeError(
                "Use TTSFacade.get_instance() instead of TTSFacade()")
        import pyttsx3
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", 175)
        self._engine.setProperty("volume", 1.0)
        self._speaking = False
        self._speech_lock = threading.Lock()
        self.enabled = True  # Controls whether speak() actually produces audio

    def speak(self, text):
        """Speak text in a background thread so the GUI is not blocked."""
        if not text or not self.enabled:
            return
        thread = threading.Thread(target=self._speak_blocking, args=(text,),
                                  daemon=True)
        thread.start()

    def _speak_blocking(self, text):
        with self._speech_lock:
            self._speaking = True
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except RuntimeError:
                pass
            finally:
                self._speaking = False

    def stop(self):
        try:
            self._engine.stop()
        except RuntimeError:
            pass

    def set_rate(self, rate):
        self._engine.setProperty("rate", rate)

    def set_volume(self, volume):
        self._engine.setProperty("volume", volume)

    @property
    def is_speaking(self):
        return self._speaking
