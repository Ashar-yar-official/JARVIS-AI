
import platform
import psutil
from datetime import datetime


# =========================================================
# DIAGNOSTIC CONFIGURATION
# =========================================================

CPU_WARNING = 75
CPU_CRITICAL = 90

RAM_WARNING = 75
RAM_CRITICAL = 90

DISK_WARNING = 85
DISK_CRITICAL = 95

PROCESS_LIMIT = 5


# =========================================================
# BATTERY TIME FORMATTER
# =========================================================

def format_battery_time(seconds):

    if seconds is None:
        return None

    if seconds == psutil.POWER_TIME_UNLIMITED:
        return "Unlimited"

    if seconds == psutil.POWER_TIME_UNKNOWN:
        return "Unknown"

    return int(seconds)


# =========================================================
# SAFE VALUE FORMATTER
# =========================================================

def safe_value(value, default="Not available"):

    if value is None:
        return default

    return value


# =========================================================
# CPU DIAGNOSTICS
# =========================================================

def diagnose_cpu():

    usage = psutil.cpu_percent(interval=0.2)

    cores = psutil.cpu_count(logical=False)
    logical_processors = psutil.cpu_count(logical=True)

    if usage >= CPU_CRITICAL:
        status = "CRITICAL"
        message = "Very high CPU utilization detected."

    elif usage >= CPU_WARNING:
        status = "WARNING"
        message = "CPU utilization is elevated."

    else:
        status = "NOMINAL"
        message = "CPU utilization is normal."

    return {
        "name": "CPU",
        "status": status,
        "usage_percent": usage,
        "physical_cores": cores,
        "logical_processors": logical_processors,
        "message": message
    }


# =========================================================
# MEMORY DIAGNOSTICS
# =========================================================

def diagnose_memory():

    memory = psutil.virtual_memory()

    usage = memory.percent

    if usage >= RAM_CRITICAL:
        status = "CRITICAL"
        message = "Critical RAM usage detected."

    elif usage >= RAM_WARNING:
        status = "WARNING"
        message = "RAM usage is elevated."

    else:
        status = "NOMINAL"
        message = "RAM usage is normal."

    return {
        "name": "MEMORY",
        "status": status,
        "usage_percent": usage,
        "total_gb": round(memory.total / (1024 ** 3), 2),
        "used_gb": round(memory.used / (1024 ** 3), 2),
        "available_gb": round(memory.available / (1024 ** 3), 2),
        "message": message
    }


# =========================================================
# STORAGE DIAGNOSTICS
# =========================================================

def diagnose_storage():

    drives = []

    partitions = psutil.disk_partitions(all=False)

    for partition in partitions:

        try:

            usage = psutil.disk_usage(partition.mountpoint)

            percent = usage.percent

            if percent >= DISK_CRITICAL:
                status = "CRITICAL"
                message = "Very low free storage space."

            elif percent >= DISK_WARNING:
                status = "WARNING"
                message = "Available storage space is decreasing."

            else:
                status = "NOMINAL"
                message = "Storage capacity is normal."

            drives.append({
                "drive": partition.device,
                "mountpoint": partition.mountpoint,
                "status": status,
                "usage_percent": percent,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "message": message
            })

        except (PermissionError, OSError):
            continue

    if not drives:

        return {
            "status": "WARNING",
            "drives": [],
            "message": "No accessible storage drives found."
        }

    if any(drive["status"] == "CRITICAL" for drive in drives):
        overall_status = "CRITICAL"

    elif any(drive["status"] == "WARNING" for drive in drives):
        overall_status = "WARNING"

    else:
        overall_status = "NOMINAL"

    return {
        "status": overall_status,
        "drives": drives,
        "message": "Storage diagnostics completed."
    }


# =========================================================
# BATTERY DIAGNOSTICS
# =========================================================

def diagnose_battery():

    battery = psutil.sensors_battery()

    if battery is None:

        return {
            "name": "BATTERY",
            "status": "NOT AVAILABLE",
            "percentage": None,
            "plugged_in": None,
            "time_remaining_seconds": None,
            "message": "Battery information is unavailable."
        }

    percentage = battery.percent
    plugged_in = battery.power_plugged

    if percentage <= 10 and not plugged_in:

        status = "WARNING"
        message = "Battery charge is low."

    else:

        status = "NOMINAL"
        message = "Battery condition requires no immediate attention."

    return {
        "name": "BATTERY",
        "status": status,
        "percentage": percentage,
        "plugged_in": plugged_in,
        "time_remaining_seconds": format_battery_time(
            battery.secsleft
        ),
        "message": message
    }


# =========================================================
# PROCESS DIAGNOSTICS
# =========================================================

def diagnose_processes():

    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "memory_percent"]
    ):

        try:

            data = process.info

            processes.append({
                "pid": data["pid"],
                "name": safe_value(data["name"]),
                "memory_percent": round(
                    data["memory_percent"] or 0, 2
                )
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    processes.sort(
        key=lambda item: item["memory_percent"],
        reverse=True
    )

    return {
        "total_processes": len(psutil.pids()),
        "top_processes": processes[:PROCESS_LIMIT],
        "message": "Process inspection completed."
    }


# =========================================================
# OVERALL SYSTEM DIAGNOSTICS
# =========================================================

def get_system_diagnostics():

    cpu = diagnose_cpu()
    memory = diagnose_memory()
    storage = diagnose_storage()
    battery = diagnose_battery()
    processes = diagnose_processes()

    statuses = [
        cpu["status"],
        memory["status"],
        storage["status"],
        battery["status"]
    ]

    if "CRITICAL" in statuses:
        overall_status = "CRITICAL"

    elif "WARNING" in statuses:
        overall_status = "WARNING"

    else:
        overall_status = "NOMINAL"

    return {
        "overall_status": overall_status,
        "computer_name": platform.node(),
        "operating_system": platform.platform(),
        "processor": platform.processor(),
        "cpu": cpu,
        "memory": memory,
        "storage": storage,
        "battery": battery,
        "processes": processes,
        "checked_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }
