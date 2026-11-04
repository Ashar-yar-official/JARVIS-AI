
from safety.permission_manager import (
    PermissionManager,
    ActionType,
    permission_manager
)

from safety.confirmation_dialog import ConfirmationDialog


class SafetyGateway:
    """
    Central permission gateway for JARVIS.

    Checks every requested operation before it is allowed
    to proceed. This class does not execute operations.
    """

    def __init__(self, manager=None):

        self.permission_manager = (
            manager if manager is not None
            else permission_manager
        )

    # =====================================================
    # AUTHORIZE AN OPERATION
    # =====================================================

    def authorize_action(
        self,
        action_type,
        description,
        parent=None
    ):
        """
        Returns a result dictionary.

        ALLOWED / CONFIRMED:
            The operation is authorized.

        CONFIRMATION_REQUIRED:
            User approval was not given.

        DENIED / BLOCKED:
            The operation is not authorized.
        """

        # First check without user confirmation.

        result = self.permission_manager.check_permission(
            action_type,
            description,
            confirmed=False
        )

        # Read operations may already be authorized.

        if result["authorized"]:
            return result

        # Only ask for confirmation when required.

        if result["status"] != "CONFIRMATION_REQUIRED":
            return result

        # Display confirmation dialog.

        try:

            approved = ConfirmationDialog.request_confirmation(
                action_type.value
                if isinstance(action_type, ActionType)
                else str(action_type),

                description,
                parent
            )

        except Exception as error:

            return {
                "authorized": False,
                "status": "ERROR",
                "message": (
                    "Could not display the confirmation dialog. "
                    f"Operation denied. Details: {error}"
                )
            }

        # Reject or closed dialog.

        if not approved:

            return {
                "authorized": False,
                "status": "REJECTED",
                "message": (
                    "User rejected the operation. "
                    "No operation was performed."
                )
            }

        # User approved: verify permission again.

        final_result = self.permission_manager.check_permission(
            action_type,
            description,
            confirmed=True
        )

        return final_result

    # =====================================================
    # BLOCK AN ACTION TYPE
    # =====================================================

    def block_action(self, action_type):

        return self.permission_manager.block_action(
            action_type
        )

    # =====================================================
    # UNBLOCK AN ACTION TYPE
    # =====================================================

    def unblock_action(self, action_type):

        return self.permission_manager.unblock_action(
            action_type
        )

    # =====================================================
    # GET ACTIVITY LOG
    # =====================================================

    def get_activity_log(self, limit=50):

        return self.permission_manager.get_activity_log(
            limit
        )


# =========================================================
# SHARED SAFETY GATEWAY
# =========================================================

safety_gateway = SafetyGateway()
