
import unittest
from unittest.mock import patch

from modules import recycle_bin_manager


class TestRecycleBinManager(unittest.TestCase):

    def setUp(self):

        self.sample_info = {
            "success": True,
            "message": "Recycle Bin information retrieved successfully.",
            "total_items": 7,
            "total_bytes": 137572,
            "formatted_size": "134.35 KB",
        }

    # -----------------------------------------------------
    # TEST 1: INFORMATION RETRIEVAL
    # -----------------------------------------------------

    @patch(
        "modules.recycle_bin_manager.get_windows_api"
    )
    def test_get_recycle_bin_info_success(self, mock_api):

        mock_shell32 = mock_api.return_value

        def mock_query(drive, info_pointer):

            info = info_pointer._obj
            info.i64NumItems = 7
            info.i64Size = 137572

            return 0

        mock_shell32.SHQueryRecycleBinW.side_effect = mock_query

        result = recycle_bin_manager.get_recycle_bin_info()

        self.assertTrue(result["success"])
        self.assertEqual(result["total_items"], 7)
        self.assertEqual(result["total_bytes"], 137572)

    # -----------------------------------------------------
    # TEST 2: REJECTED CLEANUP
    # -----------------------------------------------------

    @patch(
        "modules.recycle_bin_manager.get_recycle_bin_info"
    )
    @patch(
        "modules.recycle_bin_manager.safety_gateway.authorize_action"
    )
    @patch(
        "modules.recycle_bin_manager.get_windows_api"
    )
    def test_rejected_cleanup_does_not_empty_bin(
        self,
        mock_api,
        mock_authorize,
        mock_info
    ):

        mock_info.return_value = self.sample_info

        mock_authorize.return_value = {
            "authorized": False,
            "status": "REJECTED",
        }

        result = recycle_bin_manager.empty_recycle_bin()

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "REJECTED")
        self.assertEqual(result["deleted_items"], 0)

        # Windows empty function must never be called.
        mock_api.assert_not_called()

    # -----------------------------------------------------
    # TEST 3: APPROVED CLEANUP
    # -----------------------------------------------------

    @patch(
        "modules.recycle_bin_manager.get_recycle_bin_info"
    )
    @patch(
        "modules.recycle_bin_manager.safety_gateway.authorize_action"
    )
    @patch(
        "modules.recycle_bin_manager.get_windows_api"
    )
    def test_approved_cleanup_calls_windows_api(
        self,
        mock_api,
        mock_authorize,
        mock_info
    ):

        mock_info.return_value = self.sample_info

        mock_authorize.return_value = {
            "authorized": True,
            "status": "CONFIRMED",
        }

        mock_shell32 = mock_api.return_value
        mock_shell32.SHEmptyRecycleBinW.return_value = 0

        result = recycle_bin_manager.empty_recycle_bin()

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["deleted_items"], 7)
        self.assertEqual(result["freed_bytes"], 137572)

        # Verify that Windows was asked to empty the bin.
        mock_shell32.SHEmptyRecycleBinW.assert_called_once()

    # -----------------------------------------------------
    # TEST 4: EMPTY RECYCLE BIN
    # -----------------------------------------------------

    @patch(
        "modules.recycle_bin_manager.get_recycle_bin_info"
    )
    @patch(
        "modules.recycle_bin_manager.safety_gateway.authorize_action"
    )
    @patch(
        "modules.recycle_bin_manager.get_windows_api"
    )
    def test_empty_bin_does_not_request_confirmation(
        self,
        mock_api,
        mock_authorize,
        mock_info
    ):

        mock_info.return_value = {
            "success": True,
            "message": "Recycle Bin is empty.",
            "total_items": 0,
            "total_bytes": 0,
            "formatted_size": "0 B",
        }

        result = recycle_bin_manager.empty_recycle_bin()

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "EMPTY")
        self.assertEqual(result["deleted_items"], 0)

        mock_authorize.assert_not_called()
        mock_api.assert_not_called()

    # -----------------------------------------------------
    # TEST 5: WINDOWS API FAILURE
    # -----------------------------------------------------

    @patch(
        "modules.recycle_bin_manager.get_recycle_bin_info"
    )
    @patch(
        "modules.recycle_bin_manager.safety_gateway.authorize_action"
    )
    @patch(
        "modules.recycle_bin_manager.get_windows_api"
    )
    def test_windows_api_failure(
        self,
        mock_api,
        mock_authorize,
        mock_info
    ):

        mock_info.return_value = self.sample_info

        mock_authorize.return_value = {
            "authorized": True,
            "status": "CONFIRMED",
        }

        mock_shell32 = mock_api.return_value
        mock_shell32.SHEmptyRecycleBinW.return_value = 5

        result = recycle_bin_manager.empty_recycle_bin()

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["deleted_items"], 0)


if __name__ == "__main__":

    unittest.main()
