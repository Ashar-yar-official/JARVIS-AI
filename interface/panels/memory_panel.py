
import json
import os

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QFrame,
    QMessageBox,
    QInputDialog,
)


BG = "#10141C"
PANEL = "#191F2B"
GOLD = "#D6A84F"
TEXT = "#E8EAF0"
MUTED = "#929BAA"
GREEN = "#45D69A"
RED = "#E56B6F"


class MemoryPanel(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.memories = []
        self.selected_memory_index = -1

        self.setWindowTitle("JARVIS | Memory & Intelligence")
        self.resize(1000, 700)
        self.setMinimumSize(750, 550)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG};
                color: {TEXT};
            }}

            QLabel {{
                color: {TEXT};
                background: transparent;
            }}

            QFrame#panel {{
                background-color: {PANEL};
                border: 1px solid #303949;
                border-radius: 9px;
            }}

            QLineEdit, QListWidget, QTextEdit {{
                background-color: {PANEL};
                color: {TEXT};
                border: 1px solid #343D4D;
                border-radius: 6px;
                padding: 8px;
            }}

            QPushButton {{
                background-color: #252D3B;
                color: {TEXT};
                border: 1px solid #3A4557;
                border-radius: 6px;
                padding: 9px 13px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                border-color: {GOLD};
            }}

            QPushButton#goldButton {{
                background-color: {GOLD};
                color: {BG};
                border: none;
            }}

            QPushButton#dangerButton {{
                background-color: #632E35;
                color: white;
                border: 1px solid #91434B;
            }}
        """)

        self.build_ui()
        self.refresh_memory_list()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------

    def build_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        heading = QLabel("MEMORY & INTELLIGENCE")
        heading.setStyleSheet(
            f"color: {GOLD}; font-size: 21px; font-weight: bold;"
        )

        description = QLabel(
            "Manage information that JARVIS is permitted to remember."
        )
        description.setStyleSheet(f"color: {MUTED};")

        main_layout.addWidget(heading)
        main_layout.addWidget(description)

        # Memory status
        status_panel = QFrame()
        status_panel.setObjectName("panel")

        status_layout = QHBoxLayout(status_panel)

        self.memory_count_label = QLabel("Saved memories: 0")
        self.memory_count_label.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.storage_status_label = QLabel("Local storage")
        self.storage_status_label.setStyleSheet(
            f"color: {GREEN};"
        )

        status_layout.addWidget(self.memory_count_label)
        status_layout.addStretch()
        status_layout.addWidget(self.storage_status_label)

        main_layout.addWidget(status_panel)

        # Search
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search saved memories..."
        )

        self.search_button = QPushButton("SEARCH")
        self.show_all_button = QPushButton("SHOW ALL")

        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.show_all_button)

        main_layout.addLayout(search_layout)

        # Content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        list_panel = QFrame()
        list_panel.setObjectName("panel")

        list_layout = QVBoxLayout(list_panel)

        list_heading = QLabel("SAVED MEMORIES")
        list_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.memory_list = QListWidget()

        list_layout.addWidget(list_heading)
        list_layout.addWidget(self.memory_list)

        details_panel = QFrame()
        details_panel.setObjectName("panel")

        details_layout = QVBoxLayout(details_panel)

        details_heading = QLabel("MEMORY DETAILS")
        details_heading.setStyleSheet(
            f"color: {GOLD}; font-weight: bold;"
        )

        self.memory_title_input = QLineEdit()
        self.memory_title_input.setPlaceholderText(
            "Memory title..."
        )

        self.memory_content_input = QTextEdit()
        self.memory_content_input.setPlaceholderText(
            "Memory information..."
        )

        details_layout.addWidget(details_heading)
        details_layout.addWidget(self.memory_title_input)
        details_layout.addWidget(self.memory_content_input, 1)

        content_layout.addWidget(list_panel, 1)
        content_layout.addWidget(details_panel, 1)

        main_layout.addLayout(content_layout, 1)

        # Memory actions
        action_layout = QHBoxLayout()

        self.add_button = QPushButton("ADD MEMORY")
        self.add_button.setObjectName("goldButton")

        self.update_button = QPushButton("UPDATE MEMORY")
        self.update_button.setEnabled(False)

        self.delete_button = QPushButton("DELETE MEMORY")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setEnabled(False)

        self.clear_button = QPushButton("CLEAR ALL")
        self.clear_button.setObjectName("dangerButton")

        action_layout.addWidget(self.add_button)
        action_layout.addWidget(self.update_button)
        action_layout.addWidget(self.delete_button)
        action_layout.addWidget(self.clear_button)

        main_layout.addLayout(action_layout)

        # Footer
        footer = QHBoxLayout()

        self.status_label = QLabel("Memory manager ready.")
        self.status_label.setStyleSheet(f"color: {GREEN};")

        self.close_button = QPushButton("CLOSE")

        footer.addWidget(self.status_label, 1)
        footer.addWidget(self.close_button)

        main_layout.addLayout(footer)

        # Connections
        self.search_button.clicked.connect(self.search_memories)
        self.search_input.returnPressed.connect(self.search_memories)
        self.show_all_button.clicked.connect(self.refresh_memory_list)

        self.memory_list.currentRowChanged.connect(
            self.select_memory
        )

        self.add_button.clicked.connect(self.add_memory)
        self.update_button.clicked.connect(self.update_memory)
        self.delete_button.clicked.connect(self.delete_memory)
        self.clear_button.clicked.connect(self.clear_all_memories)

        self.close_button.clicked.connect(self.close)

    # -------------------------------------------------
    # Storage
    # -------------------------------------------------

    def get_storage_path(self):

        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )

        database_folder = os.path.join(
            project_root,
            "database"
        )

        os.makedirs(database_folder, exist_ok=True)

        return os.path.join(
            database_folder,
            "jarvis_memory.json"
        )

    def load_memories(self):

        path = self.get_storage_path()

        if not os.path.exists(path):
            self.memories = []
            return

        try:

            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError(
                    "Memory file must contain a JSON list."
                )

            self.memories = [
                item for item in data
                if isinstance(item, dict)
                and isinstance(item.get("title"), str)
                and isinstance(item.get("content"), str)
            ]

        except (OSError, json.JSONDecodeError, ValueError) as error:

            QMessageBox.warning(
                self,
                "Memory Loading Error",
                f"Could not load saved memories.\n\n{error}"
            )

            self.memories = []

    def save_memories(self):

        path = self.get_storage_path()
        temporary_path = path + ".tmp"

        try:

            with open(
                temporary_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.memories,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

            os.replace(temporary_path, path)

            self.storage_status_label.setText(
                "Local storage: Saved"
            )

            return True

        except OSError as error:

            if os.path.exists(temporary_path):
                try:
                    os.remove(temporary_path)
                except OSError:
                    pass

            QMessageBox.warning(
                self,
                "Memory Saving Error",
                f"Could not save memories.\n\n{error}"
            )

            return False

    # -------------------------------------------------
    # Display
    # -------------------------------------------------

    def refresh_memory_list(self):

        self.load_memories()

        self.selected_memory_index = -1
        self.memory_list.clear()

        for memory in self.memories:
            self.memory_list.addItem(memory["title"])

        self.memory_count_label.setText(
            f"Saved memories: {len(self.memories)}"
        )

        self.memory_title_input.clear()
        self.memory_content_input.clear()

        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        self.status_label.setText(
            "All saved memories displayed."
        )

    def select_memory(self, index):

        if index < 0 or index >= self.memory_list.count():
            self.selected_memory_index = -1
            return

        title = self.memory_list.item(index).text()

        memory_index = next(
            (
                i for i, memory in enumerate(self.memories)
                if memory["title"] == title
            ),
            -1
        )

        if memory_index == -1:
            return

        self.selected_memory_index = memory_index

        memory = self.memories[memory_index]

        self.memory_title_input.setText(memory["title"])
        self.memory_content_input.setPlainText(memory["content"])

        self.update_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    # -------------------------------------------------
    # Add memory
    # -------------------------------------------------

    def add_memory(self):

        title = self.memory_title_input.text().strip()
        content = self.memory_content_input.toPlainText().strip()

        if not title or not content:

            self.status_label.setText(
                "Enter both a title and memory information."
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Memory",
            (
                "Allow JARVIS to save this information?\n\n"
                f"{title}\n\n{content}"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self.memories.append({
            "title": title,
            "content": content
        })

        if self.save_memories():
            self.refresh_memory_list()

            self.status_label.setText(
                "Memory saved with your approval."
            )

    # -------------------------------------------------
    # Update memory
    # -------------------------------------------------

    def update_memory(self):

        index = self.selected_memory_index

        if index < 0 or index >= len(self.memories):
            return

        title = self.memory_title_input.text().strip()
        content = self.memory_content_input.toPlainText().strip()

        if not title or not content:

            self.status_label.setText(
                "Title and content cannot be empty."
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Update",
            "Save the changes to this memory?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self.memories[index] = {
            "title": title,
            "content": content
        }

        if self.save_memories():
            self.refresh_memory_list()

            self.status_label.setText(
                "Memory updated."
            )

    # -------------------------------------------------
    # Delete memory
    # -------------------------------------------------

    def delete_memory(self):

        index = self.selected_memory_index

        if index < 0 or index >= len(self.memories):
            return

        title = self.memories[index]["title"]

        confirmation = QMessageBox.warning(
            self,
            "Delete Memory",
            (
                "Permanently delete this saved memory?\n\n"
                f"{title}"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        del self.memories[index]

        if self.save_memories():
            self.refresh_memory_list()

            self.status_label.setText(
                "Memory deleted."
            )

    # -------------------------------------------------
    # Clear all memories
    # -------------------------------------------------

    def clear_all_memories(self):

        if not self.memories:

            self.status_label.setText(
                "There are no saved memories to clear."
            )
            return

        confirmation = QMessageBox.warning(
            self,
            "Clear All Memories",
            (
                "This will permanently delete all saved memories.\n\n"
                "Do you want to continue?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        final_confirmation = QMessageBox.warning(
            self,
            "Final Confirmation",
            "Confirm permanent deletion of all memories?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if final_confirmation != QMessageBox.StandardButton.Yes:
            return

        old_memories = self.memories
        self.memories = []

        if self.save_memories():
            self.refresh_memory_list()

            self.status_label.setText(
                "All saved memories have been deleted."
            )
        else:
            self.memories = old_memories

    # -------------------------------------------------
    # Search
    # -------------------------------------------------

    def search_memories(self):

        query = self.search_input.text().strip().lower()

        if not query:

            self.refresh_memory_list()
            return

        self.memory_list.clear()
        self.selected_memory_index = -1

        for memory in self.memories:

            if (
                query in memory["title"].lower()
                or query in memory["content"].lower()
            ):

                self.memory_list.addItem(memory["title"])

        self.status_label.setText(
            f"Search completed. {self.memory_list.count()} result(s)."
        )
