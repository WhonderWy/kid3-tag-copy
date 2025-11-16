#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtGui import QMovie
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


class Worker(QtCore.QThread):
    log_signal = QtCore.Signal(str, bool)
    finished_signal = QtCore.Signal()

    def __init__(self, src, dst):
        super().__init__()
        self.src = src
        self.dst = dst

    def run(self):
        copy_and_paste_tags_bulk(
            self.src,
            self.dst,
            log_func=lambda msg, success=True: self.log_signal.emit(msg, success)
        )
        self.finished_signal.emit()

# --- GUI Widgets ---

class FileListWidget(QtWidgets.QListWidget):
    """Multi-select, reorderable, drag/drop capable list widget."""
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label = label

        # Multi-select
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        # Drag/drop
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

    # --- Drag / Drop handling ---

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
        md = event.mimeData()

        # dragged from external file manager
        if md.hasUrls():
            for url in md.urls():
                abs_path = Path(url.toLocalFile()).resolve()
                if abs_path.exists() and not self.findItems(str(abs_path), QtCore.Qt.MatchExactly):
                    self.addItem(str(abs_path))

        # dragged from another list widget
        elif md.hasText():
            for line in md.text().splitlines():
                p = Path(line).resolve()
                if p.exists() and not self.findItems(str(p), QtCore.Qt.MatchExactly):
                    self.addItem(str(p))

            event.acceptProposedAction()

    def startDrag(self, dropActions):
        drag = QtGui.QDrag(self)
        mime = QtCore.QMimeData()
        paths = "\n".join(item.text() for item in self.selectedItems())
        mime.setText(paths)
        drag.setMimeData(mime)

        if drag.exec(QtCore.Qt.MoveAction) == QtCore.Qt.MoveAction:
            for item in self.selectedItems():
                self.takeItem(self.row(item))

    # --- Delete key support ---
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
        self.resize(1200, 650)

        # Make a grid layout: 2 cols × 3 rows
        grid = QtWidgets.QGridLayout(self)

        # --- Row 1: Lists ---

        self.src_list = FileListWidget("Source")
        self.dst_list = FileListWidget("Destination")

        grid.addWidget(QtWidgets.QLabel("Source Files"), 0, 0)
        grid.addWidget(QtWidgets.QLabel("Destination Files"), 0, 1)

        grid.addWidget(self.src_list, 1, 0)
        grid.addWidget(self.dst_list, 1, 1)

        # --- Row 2: Buttons ---

        self.clear_btn = QtWidgets.QPushButton("Clear Inputs + Log")
        self.run_btn = QtWidgets.QPushButton("Copy Tags (Run)")

        grid.addWidget(self.clear_btn, 2, 0)
        grid.addWidget(self.run_btn, 2, 1)

        # --- Row 3: Log View ---

        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)

        grid.addWidget(QtWidgets.QLabel("Log Output"), 3, 0, 1, 2)
        grid.addWidget(self.log, 4, 0, 1, 2)

        # --- Connections ---
        self.clear_btn.clicked.connect(self.clear_all)
        self.run_btn.clicked.connect(self.run_copy)

        # Progress dialog
        self.progress = None

    # ========== Helpers ==========

    def log_line(self, text, success=True):
        color = "green" if success else "red"
        self.log.append(f'<span style="color:{color}">{text}</span>')

    def clear_all(self):
        self.src_list.clear()
        self.dst_list.clear()
        self.log.clear()

    def run_copy(self):
        src = self.src_list.get_files()
        dst = self.dst_list.get_files()

        if len(src) != len(dst):
            QtWidgets.QMessageBox.warning(self, "Error", "Source and destination file counts differ.")
            return

        # Log button press
        self.log_line("Run button pressed, starting copy...", success=True)

        # Disable button, show spinner
        self.run_btn.setEnabled(False)

        # Show progress dialog
        self.progress = QtWidgets.QProgressDialog("Copying tags...", None, 0, 0, self)
        self.progress.setWindowTitle("Please wait")
        self.progress.setWindowModality(QtCore.Qt.WindowModal)
        self.progress.setCancelButton(None)
        self.progress.show()

        # Launch worker thread
        self.worker = Worker(src, dst)
        self.worker.log_signal.connect(self.log_line)
        self.worker.finished_signal.connect(self.copy_finished)
        self.worker.start()

    def copy_finished(self):
        if self.progress:
            self.progress.close()
            self.progress = None
        self.run_btn.setEnabled(True)
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
