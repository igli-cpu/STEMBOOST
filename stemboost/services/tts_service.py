import threading


class TTSFacade:
    """Facade + Adapter over pyttsx3 for text-to-speech.

    Provides a simplified interface (speak, stop, set_rate) and adapts the
    pyttsx3 engine to our application's needs. Uses the Singleton pattern
    so one engine instance is shared across the entire app.

    pyttsx3's SAPI5 backend on Windows is a COM STA component. Two things
    follow: (1) the engine must be driven from the thread that called
    pyttsx3.init(); (2) runAndWait() leaves the engine loop flag dirty on
    subsequent calls, so repeated runAndWait is unreliable. We therefore
    run the engine in continuous non-blocking mode (startLoop(False)) and
    drive iterate() from Tk's event loop via after().
    """

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
            raise RuntimeError(
                "Use TTSFacade.get_instance() instead of TTSFacade()")
        import pyttsx3
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", 175)
        self._engine.setProperty("volume", 1.0)
        self._tk = None
        self._loop_started = False
        self.enabled = True

    def attach_to_root(self, root):
        """Wire pyttsx3's iterate loop into Tk's event loop.

        Must be called once, on the Tk main thread, before any speak()
        calls that expect non-blocking behavior.
        """
        self._tk = root
        if not self._loop_started:
            try:
                self._engine.startLoop(False)
                self._loop_started = True
            except RuntimeError:
                pass
        self._schedule_iterate()

    def _schedule_iterate(self):
        if self._tk is None:
            return
        try:
            self._engine.iterate()
        except RuntimeError:
            pass
        self._tk.after(50, self._schedule_iterate)

    def speak(self, text):
        """Queue text for speech. Returns immediately."""
        if not text or not self.enabled:
            return
        if not self._loop_started:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except RuntimeError:
                pass
            return
        try:
            self._engine.stop()
        except RuntimeError:
            pass
        try:
            self._engine.say(text)
        except RuntimeError:
            pass

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
        return False
