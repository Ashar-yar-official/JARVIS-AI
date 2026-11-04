
import os
import tempfile
import unittest
from unittest.mock import patch

from modules.file_manager import copy_item, move_item, delete_item


class TestFileManagerSafety(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.base_path = self.temp_dir.name
        self.source_dir = os.path.join(self.base_path, "source")
        self.destination_dir = os.path.join(self.base_path, "destination")

        os.makedirs(self.source_dir)
        os.makedirs(self.destination_dir)

        self.source_file = os.path.join(self.source_dir, "test.txt")

        with open(self.source_file, "w", encoding="utf-8") as file:
            file.write("JARVIS safety test")

    def tearDown(self):
        self.temp_dir.cleanup()

    # -----------------------------------------------------
    # MOVE TESTS
    # -----------------------------------------------------

    @patch("modules.file_manager.safety_gateway.authorize_action")
    def test_approved_move_moves_file(self, mock_authorize):

        mock_authorize.return_value = {
            "authorized": True,
            "status": "CONFIRMED",
            "message": "Move approved."
        }

        result = move_item(
            self.source_file,
            self.destination_dir
        )

        expected_destination = os.path.join(
            self.destination_dir,
            "test.txt"
        )

        self.assertTrue(result["success"])
        self.assertFalse(os.path.exists(self.source_file))
        self.assertTrue(os.path.exists(expected_destination))
        mock_authorize.assert_called_once()

    @patch("modules.file_manager.safety_gateway.authorize_action")
    def test_rejected_move_keeps_source_file(self, mock_authorize):

        mock_authorize.return_value = {
            "authorized": False,
            "status": "REJECTED",
            "message": "Move rejected."
        }

        result = move_item(
            self.source_file,
            self.destination_dir
        )

        expected_destination = os.path.join(
            self.destination_dir,
            "test.txt"
        )

        self.assertFalse(result["success"])
        self.assertTrue(os.path.exists(self.source_file))
        self.assertFalse(os.path.exists(expected_destination))
        mock_authorize.assert_called_once()

    @patch("modules.file_manager.safety_gateway.authorize_action")
    def test_invalid_move_path_never_reaches_gateway(self, mock_authorize):

        invalid_source = os.path.join(
            self.base_path,
            "missing.txt"
        )

        result = move_item(
            invalid_source,
            self.destination_dir
        )

        self.assertFalse(result["success"])
        mock_authorize.assert_not_called()

    # -----------------------------------------------------
    # COPY TESTS
    # -----------------------------------------------------

    @patch("modules.file_manager.safety_gateway.authorize_action")
    def test_copy_does_not_require_confirmation(self, mock_authorize):

        result = copy_item(
            self.source_file,
            self.destination_dir
        )

        expected_destination = os.path.join(
            self.destination_dir,
            "test.txt"
        )

        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(self.source_file))
        self.assertTrue(os.path.exists(expected_destination))
        mock_authorize.assert_not_called()

    # -----------------------------------------------------
    # DELETE TESTS
    # -----------------------------------------------------

    @patch("modules.file_manager.safety_gateway.authorize_action")
    def test_rejected_deletion_keeps_file(self, mock_authorize):

        mock_authorize.return_value = {
            "authorized": False,
            "status": "REJECTED",
            "message": "Deletion rejected."
        }

        result = delete_item(self.source_file)

        self.assertFalse(result["success"])
        self.assertTrue(os.path.exists(self.source_file))
        mock_authorize.assert_called_once()

    @patch("modules.file_manager.safety_gateway.authorize_action")
    def test_authorized_deletion_removes_file(self, mock_authorize):

        mock_authorize.return_value = {
            "authorized": True,
            "status": "CONFIRMED",
            "message": "Deletion approved."
        }

        result = delete_item(self.source_file)

        self.assertTrue(result["success"])
        self.assertFalse(os.path.exists(self.source_file))
        mock_authorize.assert_called_once()

    @patch("modules.file_manager.safety_gateway.authorize_action")
    def test_invalid_deletion_never_reaches_gateway(self, mock_authorize):

        invalid_path = os.path.join(
            self.base_path,
            "missing.txt"
        )

        result = delete_item(invalid_path)

        self.assertFalse(result["success"])
        mock_authorize.assert_not_called()


if __name__ == "__main__":
    unittest.main()
