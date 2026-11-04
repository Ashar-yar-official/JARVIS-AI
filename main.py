
import sys

from PySide6.QtWidgets import QApplication

from core.ai_engine import AIEngine
from core.gemini_provider import GeminiProvider

from interface.connected_window import ConnectedMainWindow


def main():

    app = QApplication(sys.argv)

    app.setApplicationName("JARVIS")

    # Initialise the AI provider
    ai_engine = None
    ai_error = None

    try:

        ai_engine = AIEngine(
            provider=GeminiProvider()
        )

    except Exception as error:

        ai_error = str(error)

    # Create the integrated dashboard
    window = ConnectedMainWindow(
        ai_engine=ai_engine,
        ai_error=ai_error
    )

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
