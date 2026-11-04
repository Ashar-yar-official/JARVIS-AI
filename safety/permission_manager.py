
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock


# =========================================================
# PERMISSION LEVELS
# =========================================================

class ActionType(Enum):

    READ = "READ"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    SYSTEM = "SYSTEM"
    INSTALL = "INSTALL"
    EXTERNAL = "EXTERNAL"


# =========================================================
# PERMISSION MANAGER
# =========================================================

class PermissionManager:

    def __init__(self):

        self.lock = Lock()

        self.log_file = (
            Path(__file__).resolve().parent
            / "activity_log.jsonl"
        )

        self.allowed_actions = {
            ActionType.READ
        }

        self.confirmation_required = {
            ActionType.MODIFY,
            ActionType.DELETE,
            ActionType.SYSTEM,
            ActionType.INSTALL,
            ActionType.EXTERNAL
        }

        self.blocked_actions = set()

    # =====================================================
    # VALIDATE ACTION TYPE
    # =====================================================

    def validate_action_type(self, action_type):

        if isinstance(action_type, ActionType):
            return action_type

        if isinstance(action_type, str):

            try:
                return ActionType(
                    action_type.strip().upper()
                )

            except ValueError:
                return None

        return None

    # =====================================================
    # CHECK PERMISSION
    # =====================================================

    def check_permission(
        self,
        action_type,
        description,
        confirmed=False
    ):

        action_type = self.validate_action_type(
            action_type
        )

        description = str(description).strip()

        if not description:
            description = "No description provided"

        # Unknown action types are denied.

        if action_type is None:

            result = {
                "authorized": False,
                "status": "DENIED",
                "message": "Unknown action type."
            }

            self.log_activity(
                "UNKNOWN",
                description,
                result["status"]
            )

            return result

        # Explicitly blocked actions are denied.

        if action_type in self.blocked_actions:

            result = {
                "authorized": False,
                "status": "BLOCKED",
                "message": (
                    "This action has been blocked "
                    "by the permission manager."
                )
            }

            self.log_activity(
                action_type.value,
                description,
                result["status"]
            )

            return result

        # Read-only operations are permitted.

        if action_type in self.allowed_actions:

            result = {
                "authorized": True,
                "status": "ALLOWED",
                "message": "Read operation permitted."
            }

            self.log_activity(
                action_type.value,
                description,
                result["status"]
            )

            return result

        # Sensitive operations require confirmation.

        if action_type in self.confirmation_required:

            if not confirmed:

                result = {
                    "authorized": False,
                    "status": "CONFIRMATION_REQUIRED",
                    "message": (
                        "User confirmation is required "
                        "before this operation."
                    )
                }

                self.log_activity(
                    action_type.value,
                    description,
                    result["status"]
                )

                return result

            result = {
                "authorized": True,
                "status": "CONFIRMED",
                "message": (
                    "User confirmation received. "
                    "The operation may proceed."
                )
            }

            self.log_activity(
                action_type.value,
                description,
                result["status"]
            )

            return result

        # Default-deny protection.

        result = {
            "authorized": False,
            "status": "DENIED",
            "message": "Operation not authorized."
        }

        self.log_activity(
            action_type.value,
            description,
            result["status"]
        )

        return result

    # =====================================================
    # BLOCK AN ACTION TYPE
    # =====================================================

    def block_action(self, action_type):

        action_type = self.validate_action_type(
            action_type
        )

        if action_type is None:
            return False

        self.blocked_actions.add(action_type)

        self.log_activity(
            action_type.value,
            "Action type blocked.",
            "BLOCKED"
        )

        return True

    # =====================================================
    # UNBLOCK AN ACTION TYPE
    # =====================================================

    def unblock_action(self, action_type):

        action_type = self.validate_action_type(
            action_type
        )

        if action_type is None:
            return False

        self.blocked_actions.discard(
            action_type
        )

        self.log_activity(
            action_type.value,
            "Action type unblocked.",
            "UNBLOCKED"
        )

        return True

    # =====================================================
    # ACTIVITY LOG
    # =====================================================

    def log_activity(
        self,
        action_type,
        description,
        status
    ):

        entry = {
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
            "action_type": str(action_type),
            "description": str(description),
            "status": str(status)
        }

        try:

            with self.lock:

                self.log_file.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                with self.log_file.open(
                    "a",
                    encoding="utf-8"
                ) as file:

                    file.write(
                        json.dumps(
                            entry,
                            ensure_ascii=False
                        ) + "\n"
                    )

        except OSError as error:

            print(
                "JARVIS activity log error:",
                error
            )

    # =====================================================
    # READ ACTIVITY LOG
    # =====================================================

    def get_activity_log(self, limit=50):

        if not self.log_file.exists():
            return []

        try:

            with self.lock:

                with self.log_file.open(
                    "r",
                    encoding="utf-8"
                ) as file:

                    lines = file.readlines()

            entries = []

            for line in lines[-max(1, int(limit)):]:
                try:

                    entries.append(
                        json.loads(line)
                    )

                except json.JSONDecodeError:
                    continue

            return entries

        except (OSError, ValueError):

            return []


# =========================================================
# SHARED PERMISSION MANAGER
# =========================================================

permission_manager = PermissionManager()
