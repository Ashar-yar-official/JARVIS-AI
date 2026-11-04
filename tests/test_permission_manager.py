
import unittest

from safety.permission_manager import (
    PermissionManager,
    ActionType
)


class TestPermissionManager(unittest.TestCase):

    def setUp(self):
        self.manager = PermissionManager()

    def test_read_action_is_allowed(self):

        result = self.manager.check_permission(
            ActionType.READ,
            "Read a test file"
        )

        self.assertTrue(result["authorized"])

    def test_modify_action_requires_confirmation(self):

        result = self.manager.check_permission(
            ActionType.MODIFY,
            "Modify a test file"
        )

        self.assertFalse(result["authorized"])
        self.assertEqual(
            result["status"],
            "CONFIRMATION_REQUIRED"
        )

    def test_confirmed_modify_action_is_allowed(self):

        result = self.manager.check_permission(
            ActionType.MODIFY,
            "Modify a test file",
            confirmed=True
        )

        self.assertTrue(result["authorized"])

    def test_blocked_action_is_denied(self):

        self.manager.block_action(ActionType.DELETE)

        result = self.manager.check_permission(
            ActionType.DELETE,
            "Delete a test file",
            confirmed=True
        )

        self.assertFalse(result["authorized"])

    def test_unknown_action_is_denied(self):

        result = self.manager.check_permission(
            "UNKNOWN_ACTION",
            "Test unknown action"
        )

        self.assertFalse(result["authorized"])

    def test_unblocking_action(self):

        self.manager.block_action(ActionType.DELETE)
        self.manager.unblock_action(ActionType.DELETE)

        result = self.manager.check_permission(
            ActionType.DELETE,
            "Delete a test file"
        )

        self.assertEqual(
            result["status"],
            "CONFIRMATION_REQUIRED"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
