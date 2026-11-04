
from urllib.parse import quote_plus

from PySide6.QtCore import Qt, QUrl, QUrlQuery, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QSizePolicy,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings


class EmbeddedBrowser(QWidget):

    close_requested = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setObjectName("EmbeddedBrowser")
        self.setMinimumSize(300, 300)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # YouTube playback state
        self.youtube_search_pending = False
        self.youtube_video_pending = False

        self.youtube_search_attempts = 0
        self.youtube_play_attempts = 0

        self.max_search_attempts = 6
        self.max_play_attempts = 5

        self.build_interface()
        self.configure_browser()
        self.apply_style()

    # =====================================================
    # INTERFACE
    # =====================================================

    def build_interface(self):

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        # -------------------------------------------------
        # TOP TOOLBAR
        # -------------------------------------------------

        self.toolbar = QWidget()

        self.toolbar_layout = QHBoxLayout(self.toolbar)

        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_layout.setSpacing(5)

        self.back_button = QPushButton("‹")
        self.forward_button = QPushButton("›")
        self.refresh_button = QPushButton("↻")
        self.close_button = QPushButton("✕")

        for button in (
            self.back_button,
            self.forward_button,
            self.refresh_button,
            self.close_button
        ):

            button.setFixedSize(30, 28)
            button.setCursor(Qt.PointingHandCursor)

        self.address_bar = QLineEdit()

        self.address_bar.setPlaceholderText(
            "Search Google or enter a website address..."
        )

        self.address_bar.setClearButtonEnabled(True)

        self.status_label = QLabel("JARVIS WEB INTERFACE")

        self.status_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        self.status_label.setMinimumWidth(85)

        self.toolbar_layout.addWidget(self.back_button)
        self.toolbar_layout.addWidget(self.forward_button)
        self.toolbar_layout.addWidget(self.refresh_button)
        self.toolbar_layout.addWidget(self.address_bar, 1)
        self.toolbar_layout.addWidget(self.status_label)
        self.toolbar_layout.addWidget(self.close_button)

        self.main_layout.addWidget(self.toolbar)

        # -------------------------------------------------
        # BROWSER DISPLAY
        # -------------------------------------------------

        self.browser = QWebEngineView()

        self.browser.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.main_layout.addWidget(self.browser, 1)

        # -------------------------------------------------
        # SIGNAL CONNECTIONS
        # -------------------------------------------------

        self.back_button.clicked.connect(
            self.browser.back
        )

        self.forward_button.clicked.connect(
            self.browser.forward
        )

        self.refresh_button.clicked.connect(
            self.browser.reload
        )

        self.close_button.clicked.connect(
            self.close_browser
        )

        self.address_bar.returnPressed.connect(
            self.navigate_from_address
        )

        self.browser.urlChanged.connect(
            self.update_address
        )

        self.browser.loadStarted.connect(
            self.on_load_started
        )

        self.browser.loadFinished.connect(
            self.on_load_finished
        )

    # =====================================================
    # BROWSER CONFIGURATION
    # =====================================================

    def configure_browser(self):

        settings = self.browser.settings()

        # Allow JavaScript for modern websites.
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled,
            True
        )

        # Permit HTML5 media playback without requiring
        # an initial mouse click, where supported.
        try:

            settings.setAttribute(
                QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture,
                False
            )

        except (AttributeError, RuntimeError) as error:

            print(
                "JARVIS browser autoplay setting warning:",
                error
            )

    # =====================================================
    # AUDIO CONTROL
    # =====================================================

    def resume_browser_audio(self):

        """
        Restore browser audio when the mini browser
        is opened for a new browsing session.
        """

        try:

            self.browser.page().setAudioMuted(False)

        except (AttributeError, RuntimeError) as error:

            print(
                "JARVIS browser audio restore warning:",
                error
            )

    def stop_browser_media(self):

        """
        Immediately mute the browser page and stop
        active HTML5 audio/video playback.

        Also cancel pending YouTube autoplay attempts
        so a delayed timer cannot restart playback.
        """

        self.reset_youtube_state()

        try:

            # Mute the entire WebEngine page immediately.
            self.browser.page().setAudioMuted(True)

        except (AttributeError, RuntimeError) as error:

            print(
                "JARVIS browser mute warning:",
                error
            )

        javascript = """
        (() => {

            // Stop all HTML5 video elements.
            document.querySelectorAll("video").forEach(video => {

                try {
                    video.pause();
                    video.muted = true;
                    video.autoplay = false;
                } catch (error) {}
            });

            // Stop all HTML5 audio elements.
            document.querySelectorAll("audio").forEach(audio => {

                try {
                    audio.pause();
                    audio.muted = true;
                    audio.autoplay = false;
                } catch (error) {}
            });

            // Stop browser speech synthesis if active.
            try {
                window.speechSynthesis.cancel();
            } catch (error) {}

            return "MEDIA_STOPPED";

        })();
        """

        try:

            self.browser.page().runJavaScript(
                javascript
            )

        except RuntimeError as error:

            print(
                "JARVIS media stop warning:",
                error
            )

        print(
            "JARVIS browser media stopped."
        )

    def close_browser(self):

        """
        Stop all browser audio before requesting
        the parent window to hide the mini browser.
        """

        self.stop_browser_media()

        self.status_label.setText(
            "BROWSER CLOSED"
        )

        self.close_requested.emit()

    def closeEvent(self, event):

        """
        Safety fallback: stop media if the widget
        itself is closed or destroyed through Qt.
        """

        self.stop_browser_media()

        super().closeEvent(event)

    # =====================================================
    # STYLING
    # =====================================================

    def apply_style(self):

        self.setStyleSheet("""
            QWidget#EmbeddedBrowser {
                background-color: #05080D;
                border: 1px solid #A87932;
                border-radius: 7px;
            }

            QWidget {
                color: #D6B46A;
                font-family: Consolas;
            }

            QPushButton {
                background-color: #101820;
                color: #D6B46A;
                border: 1px solid #765B31;
                border-radius: 4px;
                font-size: 17px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #26303A;
                border: 1px solid #E5B85C;
            }

            QPushButton:pressed {
                background-color: #3B3020;
            }

            QLineEdit {
                background-color: #0B1118;
                color: #E5D3A3;
                border: 1px solid #765B31;
                border-radius: 4px;
                padding: 5px 8px;
                selection-background-color: #A87932;
                font-size: 10px;
            }

            QLineEdit:focus {
                border: 1px solid #D6B46A;
            }

            QLabel {
                color: #A98B56;
                font-size: 8px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)

    # =====================================================
    # NAVIGATION
    # =====================================================

    def load_url(self, url):

        if isinstance(url, str):
            url = QUrl.fromUserInput(url)

        if not url.isValid():

            self.status_label.setText("INVALID URL")
            return

        self.browser.setUrl(url)

    def open_url(self, url):

        self.resume_browser_audio()
        self.reset_youtube_state()
        self.load_url(url)

    def open_google_search(self, query):

        query = str(query or "").strip()

        if not query:
            return

        self.resume_browser_audio()
        self.reset_youtube_state()

        search_url = (
            "https://www.google.com/search?q="
            + quote_plus(query)
        )

        self.load_url(search_url)

    def open_youtube_search(self, query):

        query = str(query or "").strip()

        if not query:
            return

        self.resume_browser_audio()

        self.youtube_search_pending = True
        self.youtube_video_pending = False

        self.youtube_search_attempts = 0
        self.youtube_play_attempts = 0

        search_url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(query)
        )

        self.status_label.setText("FINDING VIDEO...")

        self.load_url(search_url)

    def open_youtube_video(self, video_url):

        self.resume_browser_audio()

        self.youtube_search_pending = False
        self.youtube_video_pending = True

        self.youtube_play_attempts = 0

        video_url = QUrl.fromUserInput(
            str(video_url)
        )

        query = QUrlQuery(video_url)

        query.removeAllQueryItems("autoplay")
        query.addQueryItem("autoplay", "1")

        video_url.setQuery(query)

        self.load_url(video_url)

    # =====================================================
    # RESET YOUTUBE STATE
    # =====================================================

    def reset_youtube_state(self):

        self.youtube_search_pending = False
        self.youtube_video_pending = False

        self.youtube_search_attempts = 0
        self.youtube_play_attempts = 0

    # =====================================================
    # AUTOMATIC YOUTUBE RESULT DETECTION
    # =====================================================

    def find_first_youtube_video(self):

        if not self.youtube_search_pending:
            return

        self.youtube_search_attempts += 1

        self.status_label.setText(
            "SEARCHING VIDEOS..."
        )

        javascript = """
        (() => {

            const selectors = [
                'ytd-video-renderer a#thumbnail[href*="/watch?v="]',
                'ytd-rich-item-renderer a#thumbnail[href*="/watch?v="]',
                'a#video-title[href*="/watch?v="]'
            ];

            for (const selector of selectors) {

                const links = document.querySelectorAll(selector);

                for (const link of links) {

                    const href = link.getAttribute("href");

                    if (
                        href &&
                        href.includes("/watch?v=")
                    ) {
                        return href;
                    }
                }
            }

            return null;

        })();
        """

        self.browser.page().runJavaScript(
            javascript,
            self.on_youtube_video_found
        )

    def on_youtube_video_found(self, video_path):

        if not self.youtube_search_pending:
            return

        if video_path:

            video_url = QUrl(
                "https://www.youtube.com"
                + str(video_path)
                if str(video_path).startswith("/")
                else str(video_path)
            )

            query = QUrlQuery(video_url)

            query.removeAllQueryItems("autoplay")
            query.addQueryItem("autoplay", "1")

            video_url.setQuery(query)

            self.youtube_search_pending = False
            self.youtube_video_pending = True

            self.youtube_play_attempts = 0

            self.status_label.setText(
                "OPENING VIDEO..."
            )

            print(
                "JARVIS selected YouTube video:",
                video_url.toString()
            )

            self.browser.setUrl(video_url)

            return

        if (
            self.youtube_search_attempts
            < self.max_search_attempts
        ):

            QTimer.singleShot(
                1800,
                self.find_first_youtube_video
            )

        else:

            self.youtube_search_pending = False

            self.status_label.setText(
                "VIDEO NOT FOUND"
            )

            print(
                "JARVIS could not detect a YouTube search result."
            )

    # =====================================================
    # AUTOMATIC YOUTUBE PLAYBACK
    # =====================================================

    def attempt_youtube_playback(self):

        if not self.youtube_video_pending:
            return

        self.youtube_play_attempts += 1

        self.status_label.setText(
            "STARTING PLAYBACK..."
        )

        javascript = """
        (() => {

            const video = document.querySelector("video");

            if (!video) {
                return "NO_VIDEO";
            }

            video.volume = 1;
            video.muted = false;
            video.autoplay = true;

            try {

                const playback = video.play();

                if (playback && playback.catch) {
                    playback.catch(() => {});
                }

                return "PLAY_REQUESTED";

            } catch (error) {

                return "PLAY_ERROR";
            }

        })();
        """

        self.browser.page().runJavaScript(
            javascript,
            self.verify_youtube_playback
        )

    def verify_youtube_playback(self, result):

        if not self.youtube_video_pending:
            return

        if result == "NO_VIDEO":

            self.schedule_playback_retry()
            return

        javascript = """
        (() => {

            const video = document.querySelector("video");

            return !!(
                video &&
                !video.paused &&
                !video.ended
            );

        })();
        """

        self.browser.page().runJavaScript(
            javascript,
            self.on_youtube_playback_verified
        )

    def on_youtube_playback_verified(self, playing):

        if not self.youtube_video_pending:
            return

        if playing:

            self.youtube_video_pending = False

            self.status_label.setText(
                "PLAYING"
            )

            print(
                "JARVIS YouTube playback started."
            )

            return

        self.schedule_playback_retry()

    def schedule_playback_retry(self):

        if (
            self.youtube_play_attempts
            < self.max_play_attempts
        ):

            self.status_label.setText(
                "RETRYING PLAYBACK..."
            )

            QTimer.singleShot(
                1800,
                self.attempt_youtube_playback
            )

        else:

            self.youtube_video_pending = False

            self.status_label.setText(
                "CLICK PLAY TO START"
            )

            print(
                "YouTube autoplay was not permitted. "
                "Manual playback may be required."
            )

    # =====================================================
    # ADDRESS BAR
    # =====================================================

    def navigate_from_address(self):

        text = self.address_bar.text().strip()

        if not text:
            return

        self.resume_browser_audio()
        self.reset_youtube_state()

        if (
            "://" not in text
            and "." not in text
        ):

            self.open_google_search(text)
            return

        self.load_url(
            QUrl.fromUserInput(text)
        )

    def update_address(self, url):

        self.address_bar.setText(
            url.toString()
        )

    # =====================================================
    # LOADING STATUS
    # =====================================================

    def on_load_started(self):

        self.status_label.setText(
            "LOADING..."
        )

    def on_load_finished(self, successful):

        if not successful:

            self.status_label.setText(
                "LOAD ERROR"
            )

            return

        current_url = self.browser.url().toString().lower()

        if (
            self.youtube_search_pending
            and "youtube.com/results" in current_url
        ):

            self.status_label.setText(
                "FINDING VIDEO..."
            )

            QTimer.singleShot(
                2000,
                self.find_first_youtube_video
            )

            return

        if (
            self.youtube_video_pending
            and (
                "youtube.com/watch" in current_url
                or "youtube.com/shorts/" in current_url
            )
        ):

            self.status_label.setText(
                "STARTING PLAYBACK..."
            )

            QTimer.singleShot(
                1800,
                self.attempt_youtube_playback
            )

            return

        self.status_label.setText(
            "CONNECTED"
        )
