import sys
import os
from PyQt6.QtCore import QUrl, QStandardPaths, QDir
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QPushButton, QWidget,
    QVBoxLayout, QFileDialog, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

class OfflineBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline Python Browser")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height

        self.current_offline_root = "" # Stores the root directory of the loaded offline site

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.browser_view = QWebEngineView()
        layout.addWidget(self.browser_view)

        # Navigation Toolbar
        nav_toolbar = QToolBar("Navigation")
        self.addToolBar(nav_toolbar)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.browser_view.back)
        nav_toolbar.addWidget(back_btn)

        forward_btn = QPushButton("Forward")
        forward_btn.clicked.connect(self.browser_view.forward)
        nav_toolbar.addWidget(forward_btn)

        reload_btn = QPushButton("Reload")
        reload_btn.clicked.connect(self.browser_view.reload)
        nav_toolbar.addWidget(reload_btn)

        # URL Bar (will show the path to the local file)
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_toolbar.addWidget(self.url_bar)

        go_btn = QPushButton("Go")
        go_btn.clicked.connect(self.navigate_to_url)
        nav_toolbar.addWidget(go_btn)

        # --- Offline Specific Functionality ---
        load_offline_btn = QPushButton("Load Offline Site")
        load_offline_btn.clicked.connect(self.load_offline_site)
        nav_toolbar.addWidget(load_offline_btn)

        # Connect URL bar to current URL changes in the browser view
        self.browser_view.urlChanged.connect(self.update_url_bar)

        # Load an initial placeholder or prompt
        self.browser_view.setHtml("<h1>Welcome to the Offline Python Browser!</h1>"
                                  "<p>Click 'Load Offline Site' to browse a downloaded website.</p>")

    def navigate_to_url(self):
        """
        Handles navigation. Prioritizes local files if a root is set.
        """
        text = self.url_bar.text()
        url = QUrl(text)

        if not url.isValid() or url.scheme() == "":
            # Try to interpret as a local file path relative to the current offline root
            if self.current_offline_root and text:
                local_path = os.path.join(self.current_offline_root, text)
                if os.path.exists(local_path):
                    self.browser_view.setUrl(QUrl.fromLocalFile(local_path))
                    return
                else:
                    QMessageBox.warning(self, "File Not Found", f"Could not find local file: {local_path}")
                    return
            # If no root or text is empty, try to open as a web URL
            else:
                url = QUrl.fromUserInput(text) # QUrl.fromUserInput handles common prefixes
        self.browser_view.setUrl(url)


    def update_url_bar(self, url):
        """Updates the URL bar with the current URL displayed by the browser."""
        self.url_bar.setText(url.toString())
        # For local files, try to show relative path if within the offline root
        if url.isLocalFile() and self.current_offline_root:
            file_path = url.toLocalFile()
            try:
                relative_path = os.path.relpath(file_path, self.current_offline_root)
                self.url_bar.setText(relative_path)
            except ValueError: # Path is not within current_offline_root
                pass

    def load_offline_site(self):
        """
        Prompts the user to select the root directory of a downloaded website
        (e.g., the 'www.example.com' folder).
        """
        # Suggest a common download location for file dialog
        suggested_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setWindowTitle("Select Offline Website Root Directory")
        if os.path.isdir(suggested_path):
            dialog.setDirectory(suggested_path)

        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_directory = dialog.selectedFiles()[0]
            if selected_directory:
                self.current_offline_root = selected_directory
                # Try to find common entry points like index.html
                index_path = os.path.join(selected_directory, "index.html")
                if not os.path.exists(index_path):
                    # Also check common `wget` output structure (e.g., domain/index.html)
                    base_name = os.path.basename(selected_directory)
                    alt_index_path = os.path.join(selected_directory, base_name, "index.html")
                    if os.path.exists(alt_index_path):
                        index_path = alt_index_path
                    else:
                        QMessageBox.information(self, "No Index Found",
                                                f"No 'index.html' found directly in '{selected_directory}' or a subfolder with the same name. "
                                                "Please navigate manually using the URL bar.")
                        # Load the directory itself, the browser might list files
                        self.browser_view.setUrl(QUrl.fromLocalFile(selected_directory))
                        self.url_bar.setText("") # Clear URL bar as no specific file is loaded yet
                        return

                self.browser_view.setUrl(QUrl.fromLocalFile(index_path))
                # Update URL bar to show the relative path or base filename
                try:
                    relative_path = os.path.relpath(index_path, self.current_offline_root)
                    self.url_bar.setText(relative_path)
                except ValueError:
                    self.url_bar.setText(os.path.basename(index_path))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = OfflineBrowser()
    browser.show()
    sys.exit(app.exec())
