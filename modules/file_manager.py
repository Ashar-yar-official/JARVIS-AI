
import os
import shutil
from datetime import datetime

from safety.permission_manager import ActionType
from safety.safety_gateway import safety_gateway


# =========================================================
# FILE MANAGER CONFIGURATION
# =========================================================

SYSTEM_DRIVES = [
    "A:\\", "B:\\", "C:\\", "D:\\", "E:\\",
    "F:\\", "G:\\", "H:\\", "I:\\", "J:\\"
]

MAX_SCAN_DEPTH = 10


# =========================================================
# SAFE FILE SIZE FORMATTER
# =========================================================

def format_size(size_bytes):

    if size_bytes < 1024:
        return f"{size_bytes} B"

    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"

    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"

    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


# =========================================================
# PATH VALIDATION
# =========================================================

def validate_paths(source, destination):

    if not source or not destination:
        return False, "Source and destination paths are required."

    source = os.path.abspath(os.path.expanduser(source))
    destination = os.path.abspath(os.path.expanduser(destination))

    if not os.path.exists(source):
        return False, "The source path does not exist."

    if os.path.islink(source):
        return False, "Symbolic links are not supported."

    if not os.path.isdir(destination):
        return False, "The destination must be an existing folder."

    if os.path.islink(destination):
        return False, "Symbolic-link destinations are not supported."

    if os.path.normcase(source) == os.path.normcase(destination):
        return False, "Source and destination cannot be the same."

    if os.path.isdir(source):

        try:
            common_path = os.path.commonpath([source, destination])

            if os.path.normcase(common_path) == os.path.normcase(source):
                return False, "A folder cannot be copied or moved into itself."

        except ValueError:
            pass

    return True, "Paths validated successfully."


# =========================================================
# DELETION PATH SAFETY VALIDATION
# =========================================================

def validate_deletion_path(path):

    if not path or not str(path).strip():
        return False, "A deletion path is required."

    try:

        path = os.path.realpath(
            os.path.abspath(os.path.expanduser(path))
        )

        if not os.path.exists(path):
            return False, "The selected item does not exist."

        if os.path.islink(path):
            return False, "Symbolic links cannot be deleted through JARVIS."

        # Protect drive roots.

        drive, tail = os.path.splitdrive(path)

        if drive and tail in ("\\", "/", ""):
            return False, "Deleting a drive root is not permitted."

        # Protected Windows system locations.

        protected_locations = [
            os.environ.get("WINDIR", r"C:\Windows"),
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
            os.path.expanduser("~"),
            os.getcwd()
        ]

        target = os.path.normcase(os.path.normpath(path))

        for protected in protected_locations:

            if not protected:
                continue

            protected = os.path.normcase(
                os.path.normpath(
                    os.path.realpath(
                        os.path.abspath(protected)
                    )
                )
            )

            try:
                common_path = os.path.commonpath([target, protected])

            except ValueError:
                continue

            if common_path == target:
                return False, (
                    "This location contains a protected system, "
                    "user-profile, or active project directory."
                )

            if (
                common_path == protected
                and protected != os.path.normcase(
                    os.path.normpath(os.path.realpath(os.getcwd()))
                )
                and protected != os.path.normcase(
                    os.path.normpath(
                        os.path.realpath(os.path.expanduser("~"))
                    )
                )
            ):
                return False, "This is a protected system location."

        return True, "Deletion path validated successfully."

    except (PermissionError, OSError, ValueError) as error:

        return False, f"Unable to validate deletion path: {error}"


# =========================================================
# DRIVE INFORMATION
# =========================================================

def get_available_drives():

    drives = []

    for drive in SYSTEM_DRIVES:

        if os.path.exists(drive):

            try:
                usage = shutil.disk_usage(drive)

                drives.append({
                    "drive": drive,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "total": format_size(usage.total),
                    "used": format_size(usage.used),
                    "free": format_size(usage.free),
                    "usage_percent": round(
                        (usage.used / usage.total) * 100, 2
                    ) if usage.total else 0
                })

            except (PermissionError, OSError):
                continue

    return drives


# =========================================================
# DIRECTORY CONTENTS
# =========================================================

def list_directory(path):

    if not os.path.exists(path):
        return {
            "success": False,
            "message": "The requested path does not exist.",
            "folders": [],
            "files": []
        }

    if not os.path.isdir(path):
        return {
            "success": False,
            "message": "The requested path is not a folder.",
            "folders": [],
            "files": []
        }

    folders = []
    files = []

    try:
        with os.scandir(path) as entries:

            for entry in entries:

                try:
                    if entry.is_dir(follow_symlinks=False):

                        folders.append({
                            "name": entry.name,
                            "path": entry.path,
                            "type": "FOLDER"
                        })

                    elif entry.is_file(follow_symlinks=False):

                        size = entry.stat(follow_symlinks=False).st_size

                        files.append({
                            "name": entry.name,
                            "path": entry.path,
                            "type": "FILE",
                            "size_bytes": size,
                            "size": format_size(size),
                            "extension": os.path.splitext(
                                entry.name
                            )[1].lower()
                        })

                except (PermissionError, OSError):
                    continue

        folders.sort(key=lambda item: item["name"].lower())
        files.sort(key=lambda item: item["name"].lower())

        return {
            "success": True,
            "message": "Directory inspection completed.",
            "path": os.path.abspath(path),
            "folder_count": len(folders),
            "file_count": len(files),
            "folders": folders,
            "files": files,
            "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except (PermissionError, OSError) as error:

        return {
            "success": False,
            "message": f"Unable to access directory: {error}",
            "folders": [],
            "files": []
        }


# =========================================================
# FILE INFORMATION
# =========================================================

def get_file_information(path):

    if not os.path.exists(path):
        return {
            "success": False,
            "message": "File does not exist."
        }

    if not os.path.isfile(path):
        return {
            "success": False,
            "message": "The requested path is not a file."
        }

    try:
        information = os.stat(path)
        extension = os.path.splitext(path)[1].lower()

        return {
            "success": True,
            "name": os.path.basename(path),
            "path": os.path.abspath(path),
            "extension": extension,
            "size_bytes": information.st_size,
            "size": format_size(information.st_size),
            "created_timestamp": information.st_ctime,
            "modified_timestamp": information.st_mtime,
            "created": datetime.fromtimestamp(
                information.st_ctime
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "modified": datetime.fromtimestamp(
                information.st_mtime
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "is_readable": os.access(path, os.R_OK)
        }

    except (PermissionError, OSError) as error:

        return {
            "success": False,
            "message": f"Unable to inspect file: {error}"
        }


# =========================================================
# FOLDER STORAGE CALCULATION
# =========================================================

def get_folder_size(path):

    if not os.path.exists(path) or not os.path.isdir(path):
        return {
            "success": False,
            "message": "Invalid folder path."
        }

    total_size = 0
    file_count = 0
    folder_count = 0
    inaccessible_items = 0

    try:
        for root, directories, files in os.walk(
            path,
            topdown=True,
            followlinks=False
        ):

            depth = os.path.relpath(root, path).count(os.sep)

            if depth >= MAX_SCAN_DEPTH:
                directories.clear()

            valid_directories = []

            for directory in directories:

                directory_path = os.path.join(root, directory)

                if not os.path.islink(directory_path):
                    valid_directories.append(directory)

            directories[:] = valid_directories
            folder_count += len(directories)

            for filename in files:

                file_path = os.path.join(root, filename)

                try:
                    if os.path.islink(file_path):
                        continue

                    total_size += os.path.getsize(file_path)
                    file_count += 1

                except (PermissionError, OSError):
                    inaccessible_items += 1

        return {
            "success": True,
            "path": os.path.abspath(path),
            "total_bytes": total_size,
            "total_size": format_size(total_size),
            "file_count": file_count,
            "folder_count": folder_count,
            "inaccessible_items": inaccessible_items,
            "message": "Folder inspection completed."
        }

    except (PermissionError, OSError) as error:

        return {
            "success": False,
            "message": f"Unable to calculate folder size: {error}"
        }


# =========================================================
# SEARCH FILES
# =========================================================

def search_files(directory, search_term):

    if not os.path.exists(directory) or not os.path.isdir(directory):
        return {
            "success": False,
            "message": "Invalid search directory.",
            "results": []
        }

    if not search_term.strip():
        return {
            "success": False,
            "message": "Enter a search term.",
            "results": []
        }

    results = []

    try:
        for root, directories, files in os.walk(
            directory,
            followlinks=False
        ):

            directories[:] = [
                directory_name
                for directory_name in directories
                if not os.path.islink(
                    os.path.join(root, directory_name)
                )
            ]

            for filename in files:

                if search_term.lower() in filename.lower():

                    path = os.path.join(root, filename)

                    try:
                        size = os.path.getsize(path)

                        results.append({
                            "name": filename,
                            "path": path,
                            "size": format_size(size),
                            "size_bytes": size
                        })

                    except (PermissionError, OSError):
                        continue

        return {
            "success": True,
            "search_term": search_term,
            "result_count": len(results),
            "results": results,
            "message": "File search completed."
        }

    except (PermissionError, OSError) as error:

        return {
            "success": False,
            "message": f"Search error: {error}",
            "results": results
        }


# =========================================================
# FILE TYPE INFORMATION
# =========================================================

def get_file_type(path):

    extension = os.path.splitext(path)[1].lower()

    file_types = {
        ".txt": "Text Document",
        ".doc": "Word Document",
        ".docx": "Word Document",
        ".pdf": "PDF Document",
        ".jpg": "Image",
        ".jpeg": "Image",
        ".png": "Image",
        ".gif": "Image",
        ".bmp": "Image",
        ".mp3": "Audio",
        ".wav": "Audio",
        ".mp4": "Video",
        ".mkv": "Video",
        ".py": "Python Source Code",
        ".cpp": "C++ Source Code",
        ".h": "C++ Header File",
        ".html": "HTML Document",
        ".css": "CSS Stylesheet",
        ".js": "JavaScript File",
        ".exe": "Executable Application",
        ".msi": "Windows Installer",
        ".zip": "Compressed Archive",
        ".rar": "Compressed Archive",
        ".7z": "Compressed Archive"
    }

    return file_types.get(extension, "Unknown File Type")


# =========================================================
# COPY FILE OR FOLDER
# No confirmation required.
# =========================================================

def copy_item(source, destination):

    valid, message = validate_paths(source, destination)

    if not valid:
        return {
            "success": False,
            "message": message
        }

    source = os.path.abspath(os.path.expanduser(source))
    destination = os.path.abspath(os.path.expanduser(destination))

    destination_path = os.path.join(
        destination,
        os.path.basename(os.path.normpath(source))
    )

    if os.path.exists(destination_path):
        return {
            "success": False,
            "message": "An item with this name already exists at the destination."
        }

    try:

        if os.path.isdir(source):
            shutil.copytree(
                source,
                destination_path,
                symlinks=True
            )

        else:
            shutil.copy2(source, destination_path)

        return {
            "success": True,
            "source": source,
            "destination": destination_path,
            "message": "Copy operation completed successfully."
        }

    except (PermissionError, OSError, shutil.Error) as error:

        return {
            "success": False,
            "message": f"Copy operation failed: {error}"
        }


# =========================================================
# MOVE FILE OR FOLDER
# Confirmation required every time.
# =========================================================

def move_item(source, destination, parent=None):

    valid, message = validate_paths(source, destination)

    if not valid:
        return {
            "success": False,
            "message": message
        }

    source = os.path.abspath(os.path.expanduser(source))
    destination = os.path.abspath(os.path.expanduser(destination))

    destination_path = os.path.join(
        destination,
        os.path.basename(os.path.normpath(source))
    )

    if os.path.exists(destination_path):
        return {
            "success": False,
            "message": "An item with this name already exists at the destination."
        }

    # Ask permission before moving.

    authorization = safety_gateway.authorize_action(
        ActionType.MODIFY,
        (
            "Move this item:\n\n"
            f"From: {source}\n\n"
            f"To: {destination_path}"
        ),
        parent
    )

    if not authorization.get("authorized", False):

        return {
            "success": False,
            "source": source,
            "destination": destination_path,
            "message": authorization.get(
                "message",
                "Move operation was not authorized."
            ),
            "status": authorization.get("status", "DENIED")
        }

    try:

        shutil.move(source, destination_path)

        return {
            "success": True,
            "source": source,
            "destination": destination_path,
            "message": "Move operation completed successfully.",
            "status": "MOVED"
        }

    except (PermissionError, OSError, shutil.Error) as error:

        return {
            "success": False,
            "message": f"Move operation failed: {error}",
            "status": "ERROR"
        }


# =========================================================
# PERMANENTLY DELETE FILE OR FOLDER
# Confirmation required every time.
# =========================================================

def delete_item(path, parent=None):

    valid, message = validate_deletion_path(path)

    if not valid:
        return {
            "success": False,
            "message": message,
            "path": path
        }

    path = os.path.realpath(
        os.path.abspath(os.path.expanduser(path))
    )

    authorization = safety_gateway.authorize_action(
        ActionType.DELETE,
        f"Permanently delete this item:\n\n{path}",
        parent
    )

    if not authorization.get("authorized", False):

        return {
            "success": False,
            "path": path,
            "message": authorization.get(
                "message",
                "Deletion was not authorized."
            ),
            "status": authorization.get("status", "DENIED")
        }

    try:

        if os.path.isdir(path):
            shutil.rmtree(path)

        else:
            os.remove(path)

        return {
            "success": True,
            "path": path,
            "message": "Item permanently deleted successfully.",
            "status": "DELETED"
        }

    except (PermissionError, OSError, shutil.Error) as error:

        return {
            "success": False,
            "path": path,
            "message": f"Permanent deletion failed: {error}",
            "status": "ERROR"
        }


# =========================================================
# FILE MANAGER OVERVIEW
# =========================================================

def get_file_manager_overview():

    drives = get_available_drives()

    return {
        "drives": drives,
        "drive_count": len(drives),
        "checked_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "message": "File manager inspection completed."
    }
