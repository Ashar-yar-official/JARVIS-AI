
import socket
import time


# =========================================================
# NETWORK CONFIGURATION
# =========================================================

DNS_TEST_HOST = "example.com"
CONNECTION_TEST_HOST = "1.1.1.1"
CONNECTION_TEST_PORT = 443

TIMEOUT_SECONDS = 5


# =========================================================
# LOCAL NETWORK INFORMATION
# =========================================================

def get_local_ip():

    try:

        connection = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        connection.settimeout(TIMEOUT_SECONDS)

        try:
            # This does not send application data.
            # It lets Windows select the local network interface.
            connection.connect(
                (CONNECTION_TEST_HOST, CONNECTION_TEST_PORT)
            )

            local_ip = connection.getsockname()[0]

        finally:
            connection.close()

        return {
            "success": True,
            "ip_address": local_ip,
            "message": "Local IP address retrieved successfully."
        }

    except Exception as error:

        return {
            "success": False,
            "ip_address": None,
            "message": str(error)
        }


# =========================================================
# NETWORK CONNECTION TEST
# =========================================================

def test_network_connection():

    start_time = time.time()

    try:

        connection = socket.create_connection(
            (
                CONNECTION_TEST_HOST,
                CONNECTION_TEST_PORT
            ),
            timeout=TIMEOUT_SECONDS
        )

        connection.close()

        elapsed_time = round(
            (time.time() - start_time) * 1000,
            2
        )

        return {
            "success": True,
            "host": CONNECTION_TEST_HOST,
            "port": CONNECTION_TEST_PORT,
            "response_time_ms": elapsed_time,
            "message": "Network connection established successfully."
        }

    except socket.timeout:

        return {
            "success": False,
            "host": CONNECTION_TEST_HOST,
            "port": CONNECTION_TEST_PORT,
            "response_time_ms": None,
            "message": "Network connection timed out."
        }

    except OSError as error:

        return {
            "success": False,
            "host": CONNECTION_TEST_HOST,
            "port": CONNECTION_TEST_PORT,
            "response_time_ms": None,
            "message": str(error)
        }


# =========================================================
# DNS RESOLUTION TEST
# =========================================================

def test_dns_resolution():

    start_time = time.time()

    try:

        addresses = socket.getaddrinfo(
            DNS_TEST_HOST,
            None,
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        ip_addresses = sorted({
            result[4][0]
            for result in addresses
        })

        elapsed_time = round(
            (time.time() - start_time) * 1000,
            2
        )

        return {
            "success": True,
            "hostname": DNS_TEST_HOST,
            "ip_addresses": ip_addresses,
            "response_time_ms": elapsed_time,
            "message": "DNS resolution completed successfully."
        }

    except socket.gaierror as error:

        return {
            "success": False,
            "hostname": DNS_TEST_HOST,
            "ip_addresses": [],
            "response_time_ms": None,
            "message": f"DNS resolution failed: {error}"
        }

    except OSError as error:

        return {
            "success": False,
            "hostname": DNS_TEST_HOST,
            "ip_addresses": [],
            "response_time_ms": None,
            "message": str(error)
        }


# =========================================================
# COMPLETE NETWORK DIAGNOSTICS
# =========================================================

def get_network_diagnostics():

    checked_at = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    local_ip = get_local_ip()
    network_test = test_network_connection()
    dns_test = test_dns_resolution()

    if network_test["success"] and dns_test["success"]:
        overall_status = "CONNECTED"

    elif network_test["success"] or dns_test["success"]:
        overall_status = "LIMITED"

    else:
        overall_status = "DISCONNECTED"

    return {
        "success": True,
        "overall_status": overall_status,
        "local_ip": local_ip["ip_address"],
        "local_ip_status": local_ip["message"],
        "network_connection": network_test,
        "dns_resolution": dns_test,
        "checked_at": checked_at,
    }
