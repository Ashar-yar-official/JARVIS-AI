
import sys

from PySide6.QtWidgets import QApplication

from safety.permission_manager import ActionType
from safety.safety_gateway import safety_gateway


def main():

    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS Safety Test")

    print("\nTesting real JARVIS confirmation dialog...")
    print("A confirmation window should appear.")

    result = safety_gateway.authorize_action(
        ActionType.MODIFY,
        "MANUAL SAFETY TEST\n\n"
        "This is only a test of the confirmation dialog.\n"
        "No files or system settings will be changed."
    )

    print("\n========== TEST RESULT ==========")
    print("Authorized:", result.get("authorized"))
    print("Status:", result.get("status"))
    print("Message:", result.get("message"))
    print("=================================")

    if result.get("authorized"):
        print("The action was approved.")

    else:
        print("The action was rejected or not authorized.")

    app.quit()


if __name__ == "__main__":
    main()
