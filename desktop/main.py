import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QStackedWidget, QPushButton, QLabel,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from desktop.pages.panel_page   import PanelPage
from desktop.pages.analyze_page import AnalyzePage
from desktop.pages.saved_page   import SavedPage


class Sidebar(QWidget):
    def __init__(self, on_navigate):
        super().__init__()
        self.on_navigate = on_navigate
        self.buttons     = {}
        self.setup_ui()

    def setup_ui(self):
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #181825;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App title
        title = QLabel("FH RFLP Screener")
        title.setStyleSheet("""
            color: #89b4fa;
            font-size: 14px;
            font-weight: bold;
            padding: 20px 16px 8px;
        """)
        layout.addWidget(title)

        version = QLabel("v1.0.0")
        version.setStyleSheet("color: #6c7086; font-size: 11px; padding: 0 16px 16px;")
        layout.addWidget(version)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #313244;")
        layout.addWidget(div)

        # Nav label
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet("""
            color: #6c7086;
            font-size: 11px;
            font-weight: bold;
            padding: 12px 16px 4px;
            letter-spacing: 1px;
        """)
        layout.addWidget(nav_label)

        # Nav buttons
        pages = [
            ("panel",   "Panel Lookup"),
            ("analyze", "Run Analysis"),
            ("saved",   "Saved Results"),
        ]

        for page_id, label in pages:
            btn = QPushButton(label)
            btn.setStyleSheet(self._btn_style(False))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, p=page_id: self.on_navigate(p))
            self.buttons[page_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Footer
        footer = QLabel("Open source · GitHub")
        footer.setStyleSheet("color: #45475a; font-size: 11px; padding: 16px;")
        layout.addWidget(footer)

        # Set default active
        self.set_active("panel")

    def set_active(self, page_id):
        for pid, btn in self.buttons.items():
            btn.setStyleSheet(self._btn_style(pid == page_id))

    def _btn_style(self, active):
        if active:
            return """
                QPushButton {
                    background: #313244;
                    color: #cdd6f4;
                    border: none;
                    border-left: 3px solid #89b4fa;
                    padding: 10px 16px;
                    text-align: left;
                    font-size: 13px;
                }
            """
        return """
            QPushButton {
                background: transparent;
                color: #6c7086;
                border: none;
                border-left: 3px solid transparent;
                padding: 10px 16px;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #1e1e2e;
                color: #cdd6f4;
            }
        """


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FH RFLP Screener")
        self.setMinimumSize(1000, 650)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1e1e2e;")

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self.navigate)
        main_layout.addWidget(self.sidebar)

        # Divider line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet("color: #313244; max-width: 1px;")
        main_layout.addWidget(line)

        # Page stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #1e1e2e;")
        main_layout.addWidget(self.stack)

        # Add pages
        self.pages = {
            "panel":   PanelPage(),
            "analyze": AnalyzePage(),
            "saved":   SavedPage(),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.navigate("panel")

    def navigate(self, page_id):
        self.sidebar.set_active(page_id)
        self.stack.setCurrentWidget(self.pages[page_id])


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()