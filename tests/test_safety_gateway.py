
import unittest
from unittest.mock import patch

from safety.permission_manager import (
    PermissionManager,
    ActionType
)

from safety.safety_gateway import SafetyGateway


class TestSafetyGateway(unittest.TestCase):

    def setUp(self):
        self.manager = PermissionManager()
        self.gateway = SafetyGateway(self.manager)

    @patch(
        "safety.safety_gateway.ConfirmationDialog.request_confirmation"
    )
    def test_read_action_does_not_require_confirmation(
        self, mock_confirmation
    ):
        result = self.gateway.authorize_action(
            ActionType.READ,
            "Read a test file"
        )

        self.assertTrue(result["authorized"])
        mock_confirmation.assert_not_called()

    @patch(
        "safety.safety_gateway.ConfirmationDialog.request_confirmation",
        return_value=True
    )
    def test_approved_action_is_authorized(
        self, mock_confirmation
    ):
        result = self.gateway.authorize_action(
            ActionType.MODIFY,
            "Modify a test file"
        )

        self.assertTrue(result["authorized"])
        self.assertEqual(result["status"], "CONFIRMED")
        mock_confirmation.assert_called_once()

    @patch(
        "safety.safety_gateway.ConfirmationDialog.request_confirmation",
        return_value=False
    )
    def test_rejected_action_is_denied(
        self, mock_confirmation
    ):
        result = self.gateway.authorize_action(
            ActionType.DELETE,
            "Delete a test file"
        )

        self.assertFalse(result["authorized"])
        self.assertEqual(result["status"], "REJECTED")
        mock_confirmation.assert_called_once()

    @patch(
        "safety.safety_gateway.ConfirmationDialog.request_confirmation"
    )
    def test_blocked_action_never_opens_dialog(
        self, mock_confirmation
    ):
        self.gateway.block_action(ActionType.DELETE)

        result = self.gateway.authorize_action(
            ActionType.DELETE,
            "Delete a test file"
        )

        self.assertFalse(result["authorized"])
        mock_confirmation.assert_not_called()

    @patch(
        "safety.safety_gateway.ConfirmationDialog.request_confirmation",
        side_effect=Exception("Test dialog error")
    )
    def test_dialog_error_denies_action(
        self, mock_confirmation
    ):
        result = self.gateway.authorize_action(
            ActionType.INSTALL,
            "Install a test application"
        )

        self.assertFalse(result["authorized"])
        self.assertEqual(result["status"], "ERROR")

    @patch(
        "safety.safety_gateway.ConfirmationDialog.request_confirmation",
        return_value=False
    )
    def test_unblock_action(
        self, mock_confirmation
    ):
        self.gateway.block_action(ActionType.DELETE)
        self.gateway.unblock_action(ActionType.DELETE)

        result = self.gateway.authorize_action(
            ActionType.DELETE,
            "Delete a test file"
        )

        self.assertFalse(result["authorized"])
        self.assertEqual(result["status"], "REJECTED")
        mock_confirmation.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
