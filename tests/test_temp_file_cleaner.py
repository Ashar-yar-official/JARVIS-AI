
import os
import tempfile
import unittest
from unittest.mock import patch

from modules.temp_file_cleaner import (
    scan_temp_files,
    clean_temp_files
)


class TestTempFileCleaner(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = self.temp_dir.name

        self.file_one = os.path.join(self.test_root, "test_one.tmp")
        self.file_two = os.path.join(self.test_root, "test_two.tmp")

        with open(self.file_one, "w", encoding="utf-8") as file:
            file.write("Temporary test data one")

        with open(self.file_two, "w", encoding="utf-8") as file:
            file.write("Temporary test data two")

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------
    # SCAN TEST
    # -------------------------------------------------

    @patch("modules.temp_file_cleaner.get_temp_directory")
    def test_scan_finds_temporary_files(self, mock_directory):

        mock_directory.return_value = self.test_root

        result = scan_temp_files()

        self.assertTrue(result["success"])
        self.assertEqual(result["total_files"], 2)
        self.assertGreater(result["total_bytes"], 0)

    # -------------------------------------------------
    # REJECTION TEST
    # -------------------------------------------------

    @patch("modules.temp_file_cleaner.get_temp_directory")
    @patch("modules.temp_file_cleaner.safety_gateway.authorize_action")
    def test_rejected_cleanup_keeps_files(
        self,
        mock_authorize,
        mock_directory
    ):

        mock_directory.return_value = self.test_root

        mock_authorize.return_value = {
            "authorized": False,
            "status": "REJECTED",
            "message": "Cleanup rejected."
        }

        result = clean_temp_files()

        self.assertFalse(result["success"])
        self.assertTrue(os.path.exists(self.file_one))
        self.assertTrue(os.path.exists(self.file_two))
        mock_authorize.assert_called_once()

    # -------------------------------------------------
    # APPROVAL TEST
    # -------------------------------------------------

    @patch("modules.temp_file_cleaner.get_temp_directory")
    @patch("modules.temp_file_cleaner.safety_gateway.authorize_action")
    def test_approved_cleanup_deletes_files(
        self,
        mock_authorize,
        mock_directory
    ):

        mock_directory.return_value = self.test_root

        mock_authorize.return_value = {
            "authorized": True,
            "status": "CONFIRMED",
            "message": "Cleanup approved."
        }

        result = clean_temp_files()

        self.assertTrue(result["success"])
        self.assertEqual(result["deleted_files"], 2)
        self.assertFalse(os.path.exists(self.file_one))
        self.assertFalse(os.path.exists(self.file_two))
        mock_authorize.assert_called_once()

    # -------------------------------------------------
    # EMPTY DIRECTORY TEST
    # -------------------------------------------------

    @patch("modules.temp_file_cleaner.get_temp_directory")
    @patch("modules.temp_file_cleaner.safety_gateway.authorize_action")
    def test_empty_directory_does_not_request_confirmation(
        self,
        mock_authorize,
        mock_directory
    ):

        empty_dir = os.path.join(self.test_root, "empty")
        os.makedirs(empty_dir)

        mock_directory.return_value = empty_dir

        result = clean_temp_files()

        self.assertTrue(result["success"])
        self.assertEqual(result["deleted_files"], 0)
        mock_authorize.assert_not_called()


if __name__ == "__main__":
    unittest.main()
