#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
from PySide6 import QtWidgets, QtCore, QtGui
import argparse
import shutil

# --- Helper Functions ---

def check_kid3_cli():
    if shutil.which("kid3-cli") is None:
        print("ERROR: kid3-cli not found in PATH. Please install kid3-cli.")
        sys.exit(1)

def copy_and_paste_tags_bulk(source_files, dest_files, log_func=print):
    if len(source_files) != len(dest_files):
        log_func("ERROR: Source and destination counts do not match!", success=False)
        return

    # Ensure absolute paths
    src_files = [Path(f).resolve() for f in source_files]
    dst_files = [Path(f).resolve() for f in dest_files]

    for src_file, dst_file in zip(src_files, dst_files):
        log_func(f"Copying tags from:\n  {src_file}\nto\n  {dst_file}", success=True)

        # Build one kid3-cli command for copy + paste + save
        cmd = [
            "kid3-cli",
            "-c", f'cd "{src_file.parent}"',
            "-c", f'select "{src_file.name}"',
            "-c", "copy",
            "-c", f'cd "{dst_file.parent}"',
            "-c", f'select "{dst_file.name}"',
            "-c", "paste",
            "-c", "save"
        ]

        log_func(f"Running: {' '.join(cmd)}", success=True)
        try:
            output = subprocess.run(cmd, check=True, capture_output=True)
            log_func(f"Tags successfully copied and pasted. {output}", success=True)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else str(e)
            log_func(f"ERROR copying tags for pair:\n{stderr}", success=False)



# --- GUI Widgets ---

class FileListWidget(QtWidgets.QListWidget):
    """A QListWidget that supports drag/drop between lists with removal on drag out."""
    def __init__(self, name="", parent=None):
        super().__init__(parent)
        self.name = name
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.source() != self and event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.source() != self and event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.source() == self:
            super().dropEvent(event)  # internal move
        elif event.mimeData().hasText():
            # Copy dragged items from another list and convert to absolute paths
            for text in event.mimeData().text().splitlines():
                if "file:" in text:
                    abs_path = str(Path.from_uri(text).expanduser().resolve())
                else:
                    abs_path = str(Path(text).expanduser().resolve())
                if not self.findItems(abs_path, QtCore.Qt.MatchExactly):
                    self.addItem(abs_path)
            event.acceptProposedAction()

    def startDrag(self, dropActions):
        drag = QtGui.QDrag(self)
        mime = QtCore.QMimeData()
        selected_text = "\n".join([item.text() for item in self.selectedItems()])
        mime.setText(selected_text)
        drag.setMimeData(mime)
        if drag.exec(QtCore.Qt.MoveAction) == QtCore.Qt.MoveAction:
            # Remove items after successful move out
            for item in self.selectedItems():
                self.takeItem(self.row(item))

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.remove_selected_items()
        else:
            super().keyPressEvent(event)

    def get_files(self):
        return [Path(self.item(i).text()).resolve() for i in range(self.count())]

    def add_files(self, file_paths):
        for f in file_paths:
            abs_path = str(Path(f).resolve())
            if not self.findItems(abs_path, QtCore.Qt.MatchExactly):
                self.addItem(abs_path)

    def remove_selected_items(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))


# --- GUI Main Window ---

class TagCopyApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kid3 Tag Copy")
        self.resize(1200, 500)

        layout = QtWidgets.QHBoxLayout(self)

        # Source panel
        src_layout = QtWidgets.QVBoxLayout()
        src_label = QtWidgets.QLabel("Source Files (reorderable and draggable)")
        self.src_list = FileListWidget("src")
        src_layout.addWidget(src_label)
        src_layout.addWidget(self.src_list)
        layout.addLayout(src_layout)

        # Destination panel
        dst_layout = QtWidgets.QVBoxLayout()
        dst_label = QtWidgets.QLabel("Destination Files (reorderable and draggable)")
        self.dst_list = FileListWidget("dst")
        dst_layout.addWidget(dst_label)
        dst_layout.addWidget(self.dst_list)
        layout.addLayout(dst_layout)

        # Side panel: Copy button + log
        side_layout = QtWidgets.QVBoxLayout()
        self.copy_button = QtWidgets.QPushButton("Copy and Overwrite Tags")
        side_layout.addWidget(self.copy_button)

        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        side_layout.addWidget(self.log)
        layout.addLayout(side_layout)

        # Connections
        self.copy_button.clicked.connect(self.run_copy)
        self.src_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.src_list.customContextMenuRequested.connect(self.show_src_context_menu)
        self.dst_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.dst_list.customContextMenuRequested.connect(self.show_dst_context_menu)

    def append_log(self, message, success=True):
        """Append message to the QTextEdit log with color depending on success."""
        color = "green" if success else "red"
        self.log.append(f'<span style="color:{color}">{message}</span>')

    def run_copy(self):
        source_files = self.src_list.get_files()
        dest_files = self.dst_list.get_files()

        if len(source_files) != len(dest_files):
            QtWidgets.QMessageBox.warning(
                self, "Error", "Source and destination file counts do not match!"
            )
            return

        copy_and_paste_tags_bulk(
            source_files, dest_files, log_func=lambda msg, success=True: self.append_log(msg, success)
        )
        QtWidgets.QMessageBox.information(self, "Done", "Tag copying completed.")

    def show_src_context_menu(self, pos):
        context_menu = QtWidgets.QMenu(self)
        delete_action = context_menu.addAction("Delete")
        action = context_menu.exec(self.src_list.mapToGlobal(pos))
        if action == delete_action:
            self.src_list.remove_selected_items()

    def show_dst_context_menu(self, pos):
        context_menu = QtWidgets.QMenu(self)
        delete_action = context_menu.addAction("Delete")
        action = context_menu.exec(self.dst_list.mapToGlobal(pos))
        if action == delete_action:
            self.dst_list.remove_selected_items()

# --- Command-line Mode ---

def cli_mode(sources, destinations):
    source_files = [Path(f) for f in sources]
    dest_files = [Path(f) for f in destinations]

    if len(source_files) != len(dest_files):
        print("ERROR: Source and destination counts do not match!")
        sys.exit(1)

    copy_and_paste_tags_bulk(source_files, dest_files)

# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Copy tags from source to destination files using kid3-cli.")
    parser.add_argument("--src", nargs="+", help="Source files")
    parser.add_argument("--dst", nargs="+", help="Destination files")
    args = parser.parse_args()

    check_kid3_cli()

    if args.src and args.dst:
        cli_mode(args.src, args.dst)
    else:
        app = QtWidgets.QApplication(sys.argv)
        window = TagCopyApp()
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
