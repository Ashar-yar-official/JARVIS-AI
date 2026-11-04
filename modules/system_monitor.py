
import platform
import psutil
import time
from datetime import datetime


# Store previous network readings for speed calculation
_previous_network = None
_previous_network_time = None


def get_system_information():
    """Collect read-only information about the computer."""

    global _previous_network
    global _previous_network_time

    # CPU information
    cpu_usage = psutil.cpu_percent(interval=None)
    cpu_cores = psutil.cpu_count(logical=False)
    logical_processors = psutil.cpu_count(logical=True)

    # RAM information
    memory = psutil.virtual_memory()

    # Disk information
    try:
        disk = psutil.disk_usage("C:\\")
        disk_information = {
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_used_gb": round(disk.used / (1024 ** 3), 2),
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "disk_percent": disk.percent
        }
    except Exception:
        disk_information = {
            "disk_total_gb": 0,
            "disk_used_gb": 0,
            "disk_free_gb": 0,
            "disk_percent": 0
        }

    # Battery information
    battery = psutil.sensors_battery()

    if battery:
        battery_percent = round(battery.percent, 1)
        battery_plugged = battery.power_plugged
        battery_seconds_left = battery.secsleft
    else:
        battery_percent = None
        battery_plugged = None
        battery_seconds_left = None

    # Network information
    network = psutil.net_io_counters()
    current_time = time.time()

    network_sent_speed = 0
    network_received_speed = 0

    if _previous_network is not None:
        time_difference = current_time - _previous_network_time

        if time_difference > 0:
            network_sent_speed = (
                network.bytes_sent - _previous_network.bytes_sent
            ) / time_difference

            network_received_speed = (
                network.bytes_recv - _previous_network.bytes_recv
            ) / time_difference

    _previous_network = network
    _previous_network_time = current_time

    # Running processes
    running_processes = len(psutil.pids())

    # System health
    system_status = "NOMINAL"

    if cpu_usage >= 90 or memory.percent >= 90:
        system_status = "CRITICAL"
    elif cpu_usage >= 75 or memory.percent >= 80:
        system_status = "WARNING"

    if disk_information["disk_percent"] >= 95:
        system_status = "CRITICAL"
    elif disk_information["disk_percent"] >= 85:
        if system_status != "CRITICAL":
            system_status = "WARNING"

    # Compile all information
    information = {
        "operating_system": platform.platform(),
        "computer_name": platform.node(),
        "processor": platform.processor(),

        "cpu_usage": cpu_usage,
        "cpu_cores": cpu_cores,
        "logical_processors": logical_processors,

        "ram_total_gb": round(memory.total / (1024 ** 3), 2),
        "ram_used_gb": round(memory.used / (1024 ** 3), 2),
        "ram_available_gb": round(memory.available / (1024 ** 3), 2),
        "ram_percent": memory.percent,

        **disk_information,

        "running_processes": running_processes,

        "network_sent_mb": round(
            network.bytes_sent / (1024 ** 2), 2
        ),
        "network_received_mb": round(
            network.bytes_recv / (1024 ** 2), 2
        ),

        "network_sent_speed_kbps": round(
            network_sent_speed / 1024, 2
        ),
        "network_received_speed_kbps": round(
            network_received_speed / 1024, 2
        ),

        "battery_percent": battery_percent,
        "battery_plugged": battery_plugged,
        "battery_seconds_left": battery_seconds_left,

        "system_status": system_status,

        "checked_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    return information
