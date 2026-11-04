
import os
import re
import json
import random
import subprocess
import webbrowser
import winreg

from urllib.parse import quote_plus

from safety.safety_gateway import safety_gateway
from safety.permission_manager import ActionType


class CommandProcessor:
    """
    Controlled command processor for JARVIS.

    Supported actions:
    - Open Windows File Explorer.
    - Search Google externally.
    - Search Google inside the JARVIS interface.
    - Search and play YouTube videos inside JARVIS.
    - Play named songs without requiring the words "on YouTube".
    - Select a random song when requested.
    - Launch installed Windows applications.
    - Forward ordinary questions to Gemini.
    """

    REGISTRY_PATHS = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            winreg.KEY_WOW64_64KEY,
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            winreg.KEY_WOW64_32KEY,
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            0,
        ),
    ]

    # Songs used when the user asks JARVIS to play a random song.
    RANDOM_SONGS = [
        "Believer Imagine Dragons",
        "Perfect Ed Sheeran",
        "Shape of You Ed Sheeran",
        "Faded Alan Walker",
        "The Nights Avicii",
        "Counting Stars OneRepublic",
        "Let Me Down Slowly Alec Benjamin",
        "Night Changes One Direction",
        "See You Again Wiz Khalifa",
        "Love Yourself Justin Bieber",
        "Until I Found You Stephen Sanchez",
        "Another Love Tom Odell",
        "Heat Waves Glass Animals",
        "A Thousand Years Christina Perri",
        "Someone You Loved Lewis Capaldi",
        "Dusk Till Dawn Zayn",
    ]

    def __init__(self, gateway=None):

        self.gateway = (
            gateway if gateway is not None
            else safety_gateway
        )

        self._application_cache = None

    # =====================================================
    # NORMALIZATION
    # =====================================================

    @staticmethod
    def normalize_name(value):

        value = str(value or "").lower().strip()

        value = re.sub(
            r"[^a-z0-9]+",
            " ",
            value
        )

        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def normalize_command(command):

        command = str(command or "").lower().strip()

        command = re.sub(
            r"[.!?,;]+",
            " ",
            command
        )

        command = re.sub(
            r"\s+",
            " ",
            command
        )

        return command.strip()

    # =====================================================
    # SAFETY AUTHORIZATION
    # =====================================================

    def authorize(self, action_type, description, parent=None):

        try:

            result = self.gateway.authorize_action(
                action_type,
                description,
                parent
            )

            if isinstance(result, bool):

                return result, (
                    "Action authorized."
                    if result else "Permission denied."
                )

            if isinstance(result, dict):

                authorized = bool(
                    result.get("authorized", False)
                )

                message = result.get(
                    "message",
                    "Action authorized."
                    if authorized else "Permission denied."
                )

                return authorized, message

            return False, (
                "Safety system returned an invalid response."
            )

        except Exception as error:

            return False, (
                f"Safety authorization failed: {error}"
            )

    # =====================================================
    # EMBEDDED GOOGLE SEARCH EXTRACTION
    # =====================================================

    @staticmethod
    def extract_embedded_google_query(command):

        normalized = CommandProcessor.normalize_command(command)

        normalized = re.sub(
            r"^(?:hey\s+)?jarvis\s+",
            "",
            normalized
        )

        patterns = [
            r"^(?:please\s+)?(?:search|google)\s+(?:for\s+)?(.+?)\s+(?:on your own interface|on your interface|on my interface|on this interface|inside your interface|in your interface|inside jarvis|in jarvis|on jarvis|here)$",

            r"^(?:please\s+)?(?:search|google)\s+(?:on|inside|in)\s+(?:your own interface|your interface|my interface|this interface|jarvis)\s+(?:for\s+)?(.+)$",

            r"^(?:please\s+)?(?:search|google)\s+(.+?)\s+(?:using|through)\s+(?:your|my|this)\s+interface$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                normalized,
                flags=re.IGNORECASE
            )

            if match:

                query = match.group(1).strip()

                if query:
                    return query

        return None

    # =====================================================
    # RANDOM SONG SELECTION
    # =====================================================

    @staticmethod
    def is_random_song_request(command):

        normalized = CommandProcessor.normalize_command(command)

        patterns = [
            r"^(?:please\s+)?play\s+(?:any|a random|some random|random)\s+(?:song|music|track)(?:\s+please)?$",

            r"^(?:please\s+)?play\s+(?:any song|something random|random music)(?:\s+please)?$",

            r"^(?:please\s+)?(?:choose|select|pick)\s+(?:any|a random|some random)\s+(?:song|music|track)$",

            r"^(?:please\s+)?play\s+something$",

            r"^(?:please\s+)?play\s+music$",

            r"^(?:please\s+)?play\s+some\s+music$",
        ]

        return any(
            re.match(pattern, normalized, re.IGNORECASE)
            for pattern in patterns
        )

    @staticmethod
    def select_random_song():

        return random.choice(
            CommandProcessor.RANDOM_SONGS
        )

    # =====================================================
    # EMBEDDED YOUTUBE QUERY EXTRACTION
    # =====================================================

    @staticmethod
    def extract_youtube_query(command):

        normalized = CommandProcessor.normalize_command(command)

        normalized = re.sub(
            r"^(?:hey\s+)?jarvis\s+",
            "",
            normalized
        )

        # Explicit YouTube commands.

        patterns = [
            r"^(?:please\s+)?(?:play|watch|search)\s+(?:for\s+)?(.+?)\s+(?:on|in)\s+youtube$",

            r"^(?:please\s+)?(?:search|open)\s+youtube\s+for\s+(.+)$",

            r"^(?:please\s+)?(?:play|watch)\s+(.+?)\s+on\s+youtube$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                normalized,
                flags=re.IGNORECASE
            )

            if match:

                query = match.group(1).strip()

                if query:
                    return query

        # Generic song and music commands.
        # YouTube is the default destination for play requests.

        generic_patterns = [
            r"^(?:please\s+)?(?:play|watch)\s+(.+)$",

            r"^(?:please\s+)?listen\s+to\s+(.+)$",
        ]

        for pattern in generic_patterns:

            match = re.match(
                pattern,
                normalized,
                flags=re.IGNORECASE
            )

            if match:

                query = match.group(1).strip()

                if not query:
                    continue

                # Remove conversational endings.

                query = re.sub(
                    r"\s+(?:please|for me)$",
                    "",
                    query
                ).strip()

                # Avoid treating random requests as literal searches.
                if query in {
                    "any song",
                    "a song",
                    "some song",
                    "random song",
                    "a random song",
                    "some random song",
                    "music",
                    "some music",
                    "random music",
                    "something",
                    "something random",
                }:

                    return CommandProcessor.select_random_song()

                if query:
                    return query

        return None

    # =====================================================
    # COMMAND CLASSIFICATION
    # =====================================================

    def classify_command(self, command):

        if not isinstance(command, str):

            return {
                "type": "INVALID",
                "message": "Invalid command."
            }

        command = command.strip()

        if not command:

            return {
                "type": "INVALID",
                "message": "Please provide a command."
            }

        normalized = self.normalize_command(command)

        # -------------------------------------------------
        # FILE EXPLORER
        # -------------------------------------------------

        explorer_patterns = {
            "open file explorer",
            "open the file explorer",
            "launch file explorer",
            "start file explorer",
            "open explorer",
            "launch explorer",
            "start explorer",
        }

        if normalized in explorer_patterns:

            return {
                "type": "OPEN_EXPLORER",
                "original_command": command
            }

        # -------------------------------------------------
        # EMBEDDED GOOGLE SEARCH
        # -------------------------------------------------

        google_query = self.extract_embedded_google_query(
            command
        )

        if google_query:

            return {
                "type": "EMBEDDED_BROWSER",
                "browser_type": "google",
                "query": google_query,
                "original_command": command
            }

        # -------------------------------------------------
        # RANDOM SONG REQUEST
        # -------------------------------------------------

        if self.is_random_song_request(command):

            selected_song = self.select_random_song()

            return {
                "type": "EMBEDDED_BROWSER",
                "browser_type": "youtube",
                "query": selected_song,
                "original_command": command,
                "random_song": True
            }

        # -------------------------------------------------
        # EMBEDDED YOUTUBE SEARCH / PLAYBACK
        # -------------------------------------------------

        youtube_query = self.extract_youtube_query(
            command
        )

        if youtube_query:

            return {
                "type": "EMBEDDED_BROWSER",
                "browser_type": "youtube",
                "query": youtube_query,
                "original_command": command
            }

        # -------------------------------------------------
        # EXTERNAL GOOGLE SEARCH
        # -------------------------------------------------

        search_patterns = [
            r"^(?:search|google)\s+(?:on\s+)?google\s+for\s+(.+)$",
            r"^search\s+for\s+(.+)\s+on\s+google$",
            r"^google\s+(.+)$",
            r"^search\s+(.+)\s+on\s+google$",
        ]

        for pattern in search_patterns:

            match = re.match(
                pattern,
                normalized,
                flags=re.IGNORECASE
            )

            if match:

                query = match.group(1).strip()

                if query:

                    return {
                        "type": "GOOGLE_SEARCH",
                        "query": query,
                        "original_command": command
                    }

        # -------------------------------------------------
        # APPLICATION LAUNCH
        # -------------------------------------------------

        application_patterns = [
            r"^(?:please\s+)?(?:open|launch|start|run)\s+(.+?)$",
            r"^(?:please\s+)?open\s+up\s+(.+?)$",
        ]

        for pattern in application_patterns:

            match = re.match(
                pattern,
                normalized,
                flags=re.IGNORECASE
            )

            if match:

                application_name = match.group(1).strip()

                excluded_targets = {
                    "settings",
                    "control panel",
                    "task manager",
                    "command prompt",
                    "powershell",
                    "terminal",
                    "the internet",
                    "a website",
                    "google",
                    "google search",
                    "youtube",
                }

                if application_name not in excluded_targets:

                    return {
                        "type": "OPEN_APPLICATION",
                        "application_name": application_name,
                        "original_command": command
                    }

        # -------------------------------------------------
        # ORDINARY CHAT
        # -------------------------------------------------

        return {
            "type": "CHAT",
            "message": command
        }

    # =====================================================
    # PROCESS COMMAND
    # =====================================================

    def process_command(self, command, parent=None):

        intent = self.classify_command(command)

        command_type = intent["type"]

        if command_type == "INVALID":

            return {
                "success": False,
                "type": command_type,
                "message": intent["message"]
            }

        if command_type == "CHAT":

            return {
                "success": True,
                "type": "CHAT",
                "message": intent["message"]
            }

        if command_type == "OPEN_EXPLORER":

            return self.open_file_explorer(parent)

        if command_type == "GOOGLE_SEARCH":

            return self.search_google(
                intent["query"],
                parent
            )

        if command_type == "EMBEDDED_BROWSER":

            return self.open_embedded_browser(
                query=intent["query"],
                browser_type=intent["browser_type"],
                parent=parent
            )

        if command_type == "OPEN_APPLICATION":

            return self.open_application(
                intent["application_name"],
                parent
            )

        return {
            "success": False,
            "type": "UNKNOWN",
            "message": "Unsupported command."
        }

    # =====================================================
    # OPEN EMBEDDED BROWSER
    # =====================================================

    def open_embedded_browser(
        self,
        query,
        browser_type="google",
        parent=None
    ):

        query = str(query or "").strip()

        browser_type = str(
            browser_type or ""
        ).lower().strip()

        if not query:

            return {
                "success": False,
                "type": "EMBEDDED_BROWSER",
                "message": "The browser search query cannot be empty."
            }

        if browser_type not in ("google", "youtube"):

            return {
                "success": False,
                "type": "EMBEDDED_BROWSER",
                "message": "Unsupported embedded browser destination."
            }

        destination = (
            "Google"
            if browser_type == "google"
            else "YouTube"
        )

        return {
            "success": True,
            "type": "EMBEDDED_BROWSER",
            "browser_type": browser_type,
            "query": query,
            "message": (
                f"Opening {destination} inside the JARVIS interface."
            )
        }

    # =====================================================
    # REGISTRY VALUE READING
    # =====================================================

    @staticmethod
    def read_registry_value(key, value_name):

        try:

            value, _ = winreg.QueryValueEx(
                key,
                value_name
            )

            return str(value).strip()

        except OSError:

            return ""

    # =====================================================
    # IDENTIFY REGISTERED EXECUTABLE
    # =====================================================

    @staticmethod
    def find_registered_executable(display_icon):

        if not display_icon:
            return None

        candidate = display_icon.strip()

        if candidate.startswith('"'):

            closing_quote = candidate.find('"', 1)

            if closing_quote == -1:
                return None

            candidate = candidate[1:closing_quote]

        else:

            candidate = re.sub(
                r",\s*-?\d+\s*$",
                "",
                candidate
            ).strip()

        candidate = os.path.expandvars(candidate)

        if not candidate.lower().endswith(".exe"):
            return None

        if not os.path.isfile(candidate):
            return None

        return os.path.abspath(candidate)

    # =====================================================
    # DISCOVER REGISTERED WINDOWS APPLICATIONS
    # =====================================================

    def discover_registry_applications(self):

        applications = []
        seen_names = set()

        if os.name != "nt":
            return applications

        for root, registry_path, access_flag in self.REGISTRY_PATHS:

            access = winreg.KEY_READ | access_flag

            try:

                with winreg.OpenKey(
                    root,
                    registry_path,
                    0,
                    access
                ) as registry_key:

                    index = 0

                    while True:

                        try:

                            subkey_name = winreg.EnumKey(
                                registry_key,
                                index
                            )

                            index += 1

                        except OSError:

                            break

                        try:

                            with winreg.OpenKey(
                                registry_key,
                                subkey_name,
                                0,
                                winreg.KEY_READ
                            ) as app_key:

                                name = self.read_registry_value(
                                    app_key,
                                    "DisplayName"
                                )

                                if not name:
                                    continue

                                normalized_name = self.normalize_name(
                                    name
                                )

                                if not normalized_name:
                                    continue

                                if normalized_name in seen_names:
                                    continue

                                seen_names.add(normalized_name)

                                display_icon = self.read_registry_value(
                                    app_key,
                                    "DisplayIcon"
                                )

                                executable = (
                                    self.find_registered_executable(
                                        display_icon
                                    )
                                )

                                applications.append({
                                    "name": name,
                                    "normalized_name": normalized_name,
                                    "executable": executable,
                                    "app_id": None,
                                    "source": "REGISTRY"
                                })

                        except OSError:

                            continue

            except OSError:

                continue

        return applications

    # =====================================================
    # DISCOVER WINDOWS START APPS
    # =====================================================

    def discover_start_applications(self):

        applications = []

        if os.name != "nt":
            return applications

        powershell_command = (
            "Get-StartApps | "
            "Select-Object Name, AppID | "
            "ConvertTo-Json -Compress"
        )

        try:

            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    powershell_command
                ],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0
                ),
                check=False
            )

            if result.returncode != 0:
                return applications

            output = result.stdout.strip()

            if not output:
                return applications

            data = json.loads(output)

            if isinstance(data, dict):
                data = [data]

            if not isinstance(data, list):
                return applications

            for item in data:

                if not isinstance(item, dict):
                    continue

                name = str(
                    item.get("Name", "")
                ).strip()

                app_id = str(
                    item.get("AppID", "")
                ).strip()

                if not name or not app_id:
                    continue

                applications.append({
                    "name": name,
                    "normalized_name": self.normalize_name(name),
                    "executable": None,
                    "app_id": app_id,
                    "source": "START_APPS"
                })

        except (
            OSError,
            subprocess.TimeoutExpired,
            json.JSONDecodeError,
            TypeError,
            ValueError
        ):

            return applications

        return applications

    # =====================================================
    # LOAD APPLICATION CATALOGUE
    # =====================================================

    def load_application_catalogue(self, force_refresh=False):

        if (
            self._application_cache is not None
            and not force_refresh
        ):

            return self._application_cache

        applications = self.discover_registry_applications()

        seen = {
            item["normalized_name"]
            for item in applications
        }

        for application in self.discover_start_applications():

            normalized_name = application["normalized_name"]

            if normalized_name in seen:

                existing = next(
                    (
                        item for item in applications
                        if item["normalized_name"] == normalized_name
                    ),
                    None
                )

                if existing and not existing.get("app_id"):

                    existing["app_id"] = application.get(
                        "app_id"
                    )

                continue

            seen.add(normalized_name)
            applications.append(application)

        self._application_cache = applications

        return applications

    # =====================================================
    # MATCH APPLICATION NAME
    # =====================================================

    def find_application_matches(self, requested_name):

        requested = self.normalize_name(requested_name)

        if not requested:
            return []

        applications = self.load_application_catalogue()

        exact_matches = [
            app for app in applications
            if app["normalized_name"] == requested
        ]

        if exact_matches:
            return exact_matches

        partial_matches = [
            app for app in applications
            if (
                app["normalized_name"].startswith(requested + " ")
                or requested.startswith(app["normalized_name"] + " ")
            )
        ]

        if partial_matches:
            return partial_matches

        requested_tokens = set(requested.split())

        token_matches = []

        for app in applications:

            app_tokens = set(
                app["normalized_name"].split()
            )

            if (
                requested_tokens
                and requested_tokens.issubset(app_tokens)
            ):

                token_matches.append(app)

        return token_matches

    # =====================================================
    # OPEN INSTALLED APPLICATION
    # =====================================================

    def open_application(self, application_name, parent=None):

        if os.name != "nt":

            return {
                "success": False,
                "type": "OPEN_APPLICATION",
                "message": (
                    "Application launching is supported only on Windows."
                )
            }

        matches = self.find_application_matches(
            application_name
        )

        if not matches:

            return {
                "success": False,
                "type": "APPLICATION_NOT_FOUND",
                "message": (
                    f"I could not find an installed application named "
                    f"'{application_name}'. You can open the Application "
                    f"Management panel to inspect installed applications."
                )
            }

        if len(matches) > 1:

            names = "\n".join(
                f"• {app['name']}"
                for app in matches[:8]
            )

            return {
                "success": False,
                "type": "AMBIGUOUS_APPLICATION",
                "message": (
                    f"I found multiple applications matching "
                    f"'{application_name}':\n\n{names}\n\n"
                    "Please specify the full application name."
                )
            }

        application = matches[0]

        name = application["name"]
        executable = application.get("executable")
        app_id = application.get("app_id")

        if not executable and not app_id:

            return {
                "success": False,
                "type": "APPLICATION_NOT_LAUNCHABLE",
                "message": (
                    f"I found {name}, but Windows did not provide "
                    "a registered launch target. Please launch it "
                    "through the Windows Start menu."
                )
            }

        try:

            if executable:

                if not os.path.isfile(executable):

                    return {
                        "success": False,
                        "type": "APPLICATION_NOT_LAUNCHABLE",
                        "message": (
                            f"The registered executable for {name} "
                            "no longer exists."
                        )
                    }

                os.startfile(executable)

            else:

                os.startfile(
                    "shell:AppsFolder\\" + app_id
                )

            return {
                "success": True,
                "type": "OPEN_APPLICATION",
                "message": f"Launch requested: {name}."
            }

        except OSError as error:

            return {
                "success": False,
                "type": "OPEN_APPLICATION",
                "message": f"Could not launch {name}: {error}"
            }

    # =====================================================
    # OPEN WINDOWS FILE EXPLORER
    # =====================================================

    def open_file_explorer(self, parent=None):

        description = "Open Windows File Explorer."

        authorized, authorization_message = self.authorize(
            ActionType.SYSTEM,
            description,
            parent
        )

        if not authorized:

            return {
                "success": False,
                "type": "OPEN_EXPLORER",
                "message": authorization_message
            }

        try:

            if os.name != "nt":

                raise OSError(
                    "File Explorer is available only on Windows."
                )

            os.startfile("explorer.exe")

            return {
                "success": True,
                "type": "OPEN_EXPLORER",
                "message": "File Explorer launch requested."
            }

        except OSError as error:

            return {
                "success": False,
                "type": "OPEN_EXPLORER",
                "message": f"Could not open File Explorer: {error}"
            }

    # =====================================================
    # GOOGLE SEARCH
    # =====================================================

    def search_google(self, query, parent=None):

        query = str(query).strip()

        if not query:

            return {
                "success": False,
                "type": "GOOGLE_SEARCH",
                "message": "Google search query cannot be empty."
            }

        description = (
            "Open Google search in the default browser.\n\n"
            f"Search query: {query}"
        )

        authorized, authorization_message = self.authorize(
            ActionType.EXTERNAL,
            description,
            parent
        )

        if not authorized:

            return {
                "success": False,
                "type": "GOOGLE_SEARCH",
                "message": authorization_message
            }

        try:

            search_url = (
                "https://www.google.com/search?q="
                + quote_plus(query)
            )

            opened = webbrowser.open(
                search_url,
                new=2
            )

            if not opened:

                return {
                    "success": False,
                    "type": "GOOGLE_SEARCH",
                    "message": (
                        "The default browser could not open "
                        "the Google search."
                    )
                }

            return {
                "success": True,
                "type": "GOOGLE_SEARCH",
                "message": f"Google search opened for: {query}"
            }

        except Exception as error:

            return {
                "success": False,
                "type": "GOOGLE_SEARCH",
                "message": f"Google search failed: {error}"
            }


# =====================================================
# SHARED COMMAND PROCESSOR
# =====================================================

command_processor = CommandProcessor()
