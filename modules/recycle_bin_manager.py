
import ctypes
import os

from ctypes import wintypes

from safety.safety_gateway import safety_gateway
from safety.permission_manager import ActionType


# =========================================================
# WINDOWS RECYCLE BIN API
# =========================================================

SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004


class SHQUERYRBINFO(ctypes.Structure):

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_longlong),
        ("i64NumItems", ctypes.c_longlong),
    ]


def get_windows_api():

    if os.name != "nt":
        raise OSError(
            "Recycle Bin management is supported only on Windows."
        )

    shell32 = ctypes.WinDLL("shell32", use_last_error=True)

    shell32.SHQueryRecycleBinW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(SHQUERYRBINFO),
    ]

    shell32.SHQueryRecycleBinW.restype = ctypes.c_long

    shell32.SHEmptyRecycleBinW.argtypes = [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.DWORD,
    ]

    shell32.SHEmptyRecycleBinW.restype = ctypes.c_long

    return shell32


# =========================================================
# FORMATTING
# =========================================================

def format_size(size_bytes):

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"

    if size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"

    return f"{size_bytes / (1024 ** 3):.2f} GB"


# =========================================================
# RECYCLE BIN INFORMATION
# =========================================================

def get_recycle_bin_info():

    try:

        shell32 = get_windows_api()

        info = SHQUERYRBINFO()
        info.cbSize = ctypes.sizeof(SHQUERYRBINFO)

        # None means query all available drives.
        result = shell32.SHQueryRecycleBinW(
            None,
            ctypes.byref(info)
        )

        if result != 0:

            return {
                "success": False,
                "message": (
                    f"Windows Recycle Bin query failed. "
                    f"Error code: {result}"
                ),
                "total_items": 0,
                "total_bytes": 0,
                "formatted_size": "0 B",
            }

        total_items = info.i64NumItems
        total_bytes = info.i64Size

        return {
            "success": True,
            "message": "Recycle Bin information retrieved successfully.",
            "total_items": total_items,
            "total_bytes": total_bytes,
            "formatted_size": format_size(total_bytes),
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
            "total_items": 0,
            "total_bytes": 0,
            "formatted_size": "0 B",
        }


# =========================================================
# EMPTY RECYCLE BIN
# =========================================================

def empty_recycle_bin(parent=None):

    # First check whether the Recycle Bin contains anything.

    info = get_recycle_bin_info()

    if not info["success"]:

        return {
            "success": False,
            "status": "FAILED",
            "deleted_items": 0,
            "freed_bytes": 0,
            "message": info["message"],
        }

    if info["total_items"] == 0:

        return {
            "success": True,
            "status": "EMPTY",
            "deleted_items": 0,
            "freed_bytes": 0,
            "message": "The Recycle Bin is already empty.",
        }

    item_count = info["total_items"]
    storage_size = info["total_bytes"]

    description = (
        "Empty the Windows Recycle Bin permanently.\n\n"
        f"Items to remove: {item_count}\n"
        f"Storage occupied: {format_size(storage_size)}\n\n"
        "This operation cannot be undone."
    )

    # Explicit approval is required before permanent deletion.

    authorization = safety_gateway.authorize_action(
        ActionType.DELETE,
        description,
        parent
    )

    if not authorization.get("authorized", False):

        return {
            "success": False,
            "status": authorization.get("status", "REJECTED"),
            "deleted_items": 0,
            "freed_bytes": 0,
            "message": (
                "User rejected the operation. "
                "No operation was performed."
            ),
        }

    # Empty the Recycle Bin across all available drives.
    # The Windows API is called only after approval.

    try:

        shell32 = get_windows_api()

        flags = (
            SHERB_NOCONFIRMATION
            | SHERB_NOPROGRESSUI
            | SHERB_NOSOUND
        )

        result = shell32.SHEmptyRecycleBinW(
            None,
            None,
            flags
        )

        if result != 0:

            return {
                "success": False,
                "status": "FAILED",
                "deleted_items": 0,
                "freed_bytes": 0,
                "message": (
                    "Windows could not empty the Recycle Bin. "
                    f"Error code: {result}"
                ),
            }

        return {
            "success": True,
            "status": "COMPLETED",
            "deleted_items": item_count,
            "freed_bytes": storage_size,
            "message": "Windows Recycle Bin emptied successfully.",
        }

    except Exception as error:

        return {
            "success": False,
            "status": "FAILED",
            "deleted_items": 0,
            "freed_bytes": 0,
            "message": str(error),
        }
