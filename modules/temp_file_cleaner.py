
import os
from datetime import datetime

from safety.permission_manager import ActionType
from safety.safety_gateway import safety_gateway


def normalize_path(path):
    """Return a consistently normalized absolute path."""

    return os.path.normcase(
        os.path.normpath(
            os.path.realpath(
                os.path.abspath(path)
            )
        )
    )


def get_temp_directory():
    """Return the current user's Windows temporary directory."""

    temp_path = os.environ.get("TEMP") or os.environ.get("TMP")

    if not temp_path:
        return None

    return os.path.realpath(os.path.abspath(temp_path))


def scan_temp_files():
    """
    Inspect the current user's temporary directory.

    Read-only operation. Does not delete or modify files.
    Symbolic links and inaccessible files are skipped.
    Only directly contained regular files are inspected.
    """

    temp_directory = get_temp_directory()

    if not temp_directory or not os.path.isdir(temp_directory):
        return {
            "success": False,
            "message": "The user temporary directory could not be accessed.",
            "files": [],
            "total_files": 0,
            "total_bytes": 0
        }

    files = []
    total_bytes = 0
    skipped = 0

    try:
        with os.scandir(temp_directory) as entries:

            for entry in entries:

                try:
                    if entry.is_symlink():
                        skipped += 1
                        continue

                    if not entry.is_file(follow_symlinks=False):
                        continue

                    information = entry.stat(follow_symlinks=False)

                    files.append({
                        "name": entry.name,
                        "path": entry.path,
                        "size_bytes": information.st_size
                    })

                    total_bytes += information.st_size

                except (PermissionError, OSError):
                    skipped += 1

        return {
            "success": True,
            "directory": temp_directory,
            "files": files,
            "total_files": len(files),
            "total_bytes": total_bytes,
            "skipped": skipped,
            "checked_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "message": "Temporary-file scan completed."
        }

    except (PermissionError, OSError) as error:

        return {
            "success": False,
            "message": f"Temporary-file scan failed: {error}",
            "files": [],
            "total_files": 0,
            "total_bytes": 0
        }


def clean_temp_files(parent=None):
    """
    Delete eligible files directly inside the user's TEMP directory.

    Requires safety-gateway authorization before deletion.
    Directories and symbolic links are never deleted.
    """

    scan_result = scan_temp_files()

    if not scan_result["success"]:
        return {
            "success": False,
            "message": scan_result["message"],
            "deleted_files": 0,
            "deleted_bytes": 0,
            "skipped_files": 0
        }

    files = scan_result["files"]

    if not files:
        return {
            "success": True,
            "message": "No eligible temporary files were found.",
            "deleted_files": 0,
            "deleted_bytes": 0,
            "skipped_files": scan_result["skipped"]
        }

    authorization = safety_gateway.authorize_action(
        ActionType.DELETE,
        (
            "JARVIS Temporary File Cleanup\n\n"
            f"Location: {scan_result['directory']}\n"
            f"Files to delete: {len(files)}\n"
            f"Total size: {scan_result['total_bytes']} bytes\n\n"
            "Only regular files directly inside the current user's "
            "temporary directory will be deleted. "
            "Folders and symbolic links will not be deleted."
        ),
        parent
    )

    if not authorization.get("authorized", False):
        return {
            "success": False,
            "message": authorization.get(
                "message",
                "Temporary-file cleanup was not authorized."
            ),
            "status": authorization.get("status", "DENIED"),
            "deleted_files": 0,
            "deleted_bytes": 0,
            "skipped_files": scan_result["skipped"]
        }

    deleted_files = 0
    deleted_bytes = 0
    skipped_files = scan_result["skipped"]

    expected_directory = normalize_path(
        scan_result["directory"]
    )

    for item in files:

        path = item["path"]

        try:
            # Reject symbolic links.
            if os.path.islink(path):
                skipped_files += 1
                continue

            # The item must still be a regular file.
            if not os.path.isfile(path):
                skipped_files += 1
                continue

            # Normalize both paths before comparing them.
            actual_parent = normalize_path(
                os.path.dirname(os.path.abspath(path))
            )

            if actual_parent != expected_directory:
                skipped_files += 1
                continue

            # Recheck the entry immediately before deletion.
            if os.path.islink(path) or not os.path.isfile(path):
                skipped_files += 1
                continue

            current_size = os.path.getsize(path)

            os.remove(path)

            deleted_files += 1
            deleted_bytes += current_size

        except (PermissionError, OSError):
            # Locked or inaccessible files remain untouched.
            skipped_files += 1

    return {
        "success": True,
        "status": "COMPLETED",
        "directory": scan_result["directory"],
        "deleted_files": deleted_files,
        "deleted_bytes": deleted_bytes,
        "skipped_files": skipped_files,
        "message": "Temporary-file cleanup completed."
    }
