from __future__ import annotations

from PySide6.QtCore import QLocale, QObject, Signal
from PySide6.QtTextToSpeech import QTextToSpeech


class SpeechService(QObject):
    status_changed = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.engine = QTextToSpeech(self)
        self.engine.stateChanged.connect(self._on_state_changed)
        self._last_text = ""
        self._last_locale = "en-US"

    def available_for(self, locale_name: str) -> bool:
        wanted = QLocale(locale_name.replace("-", "_"))
        wanted_language = wanted.language()
        return any(locale.language() == wanted_language for locale in self.engine.availableLocales())

    def speak(self, text: str, locale_name: str) -> bool:
        text = text.strip()
        if not text:
            return False
        locale = QLocale(locale_name.replace("-", "_"))
        self.engine.stop()
        self.engine.setLocale(locale)
        self._last_text = text
        self._last_locale = locale_name
        self.engine.say(text)
        if self.available_for(locale_name):
            self.status_changed.emit("Speaking")
            return True
        self.status_changed.emit(
            f"No {locale.nativeLanguageName()} voice is installed on this computer."
        )
        return False

    def replay(self) -> bool:
        return self.speak(self._last_text, self._last_locale)

    def stop(self) -> None:
        self.engine.stop()

    def _on_state_changed(self, state: QTextToSpeech.State) -> None:
        if state == QTextToSpeech.State.Ready:
            self.status_changed.emit("Voice ready")
        elif state == QTextToSpeech.State.Error:
            self.status_changed.emit("Speech could not be played")
