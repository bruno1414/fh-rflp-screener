import sys
import os
import json
import glob
import base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class SavedPage(QWidget):
    def __init__(self):
        super().__init__()
        self.saved_results = []
        self.saves_dir     = os.path.join(
            os.path.expanduser("~"), "FH_RFLP_Saves"
        )
        os.makedirs(self.saves_dir, exist_ok=True)
        self.setup_ui()
        self.load_saved()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Saved Results")
        title.setStyleSheet(
            "color: #cdd6f4; font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title)

        subtitle = QLabel(
            "View and manage results you have saved from "
            "Panel Lookup and Run Analysis."
        )
        subtitle.setStyleSheet("color: #6c7086; font-size: 12px;")
        layout.addWidget(subtitle)

        btn_row = QHBoxLayout()
        load_btn = QPushButton("Load Result File")
        load_btn.setStyleSheet(self._btn_style("#89b4fa", "#1e1e2e"))
        load_btn.clicked.connect(self.load_file)
        btn_row.addWidget(load_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet(self._btn_style("#f38ba8", "#1e1e2e"))
        clear_btn.clicked.connect(self.clear_all)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        content = QHBoxLayout()
        content.setSpacing(16)

        # List panel
        list_widget = QWidget()
        list_widget.setFixedWidth(280)
        list_widget.setStyleSheet(
            "background: #181825; border-radius: 8px;"
        )
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(12, 12, 12, 12)

        list_title = QLabel("Saved Items")
        list_title.setStyleSheet(
            "color: #6c7086; font-size: 11px; font-weight: bold;"
        )
        list_layout.addWidget(list_title)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                color: #cdd6f4;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected { background: #313244; }
            QListWidget::item:hover    { background: #1e1e2e; }
        """)
        self.list_widget.itemSelectionChanged.connect(self.on_item_selected)
        list_layout.addWidget(self.list_widget)
        content.addWidget(list_widget)

        # Detail panel
        self.detail_widget = QWidget()
        self.detail_widget.setStyleSheet(
            "background: #181825; border-radius: 8px;"
        )
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(16, 16, 16, 16)

        self.empty_label = QLabel("Select a saved result to view details.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            "color: #45475a; font-size: 13px;"
        )
        self.detail_layout.addWidget(
            self.empty_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.detail_layout.addStretch()

        content.addWidget(self.detail_widget)
        layout.addLayout(content)

    def showEvent(self, event):
        """Refresh list every time this tab becomes visible."""
        super().showEvent(event)
        self.refresh_list()

    def load_saved(self):
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        self.saved_results = []

        files = glob.glob(os.path.join(self.saves_dir, "*.json"))
        for f in sorted(files, reverse=True):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                label = f"{data.get('gene','?')} {data.get('cdna_change','?')}"
                item  = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, data)
                self.list_widget.addItem(item)
                self.saved_results.append(data)
            except Exception:
                pass

        if not self.saved_results:
            item = QListWidgetItem("No saved results yet")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_widget.addItem(item)

    def on_item_selected(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
        data = items[0].data(Qt.ItemDataRole.UserRole)
        if data:
            self.show_detail(data)

    def _clear_layout(self, layout):
        """Recursively clear a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def show_detail(self, data):
        # Clear existing detail content
        for i in reversed(range(self.detail_layout.count())):
            item = self.detail_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        # Title
        title = QLabel(
            f"{data.get('gene','?')}  {data.get('cdna_change','?')}"
        )
        title.setStyleSheet(
            "color: #cdd6f4; font-size: 15px; font-weight: bold;"
        )
        self.detail_layout.addWidget(title)

        # Gel image if saved
        if data.get("gel_image"):
            try:
                img_data = base64.b64decode(data["gel_image"])
                pixmap   = QPixmap()
                pixmap.loadFromData(img_data)
                scaled   = pixmap.scaledToWidth(
                    380, Qt.TransformationMode.SmoothTransformation
                )
                gel_lbl = QLabel()
                gel_lbl.setPixmap(scaled)
                gel_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                gel_lbl.setStyleSheet(
                    "background: #11111b; border-radius: 6px; padding: 8px;"
                )
                self.detail_layout.addWidget(gel_lbl)
            except Exception as e:
                print(f"Could not load gel image: {e}")

        # Info fields
        fields = [
            ("Best Enzyme",         data.get("best_enzyme", "—")),
            ("Site Change",         data.get("change_type", "—").replace("_", " ")),
            ("WT Fragments",        str(data.get("wt_frags", "—"))),
            ("Mutant Fragments",    str(data.get("mut_frags", "—"))),
            ("Fragment Difference", str(data.get("frag_diff_bp", "—")) + " bp"),
            ("Gel Quality",         data.get("gel_quality", "—")),
            ("RFLP Score",          str(data.get("rflp_score", "—"))),
        ]
        for label, value in fields:
            row = QHBoxLayout()
            lbl = QLabel(label + ":")
            lbl.setStyleSheet("color: #6c7086; font-size: 12px;")
            lbl.setFixedWidth(160)
            val = QLabel(str(value))
            val.setStyleSheet(
                "color: #cdd6f4; font-size: 12px; font-weight: bold;"
            )
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            self.detail_layout.addLayout(row)

        # Export button
        export_btn = QPushButton("Export as CSV")
        export_btn.setStyleSheet(self._btn_style())
        export_btn.clicked.connect(lambda: self.export_single(data))
        self.detail_layout.addWidget(export_btn)
        self.detail_layout.addStretch()

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Result File",
            os.path.expanduser("~"),
            "JSON Files (*.json)"
        )
        if path:
            try:
                import shutil
                shutil.copy(path, self.saves_dir)
                self.refresh_list()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def clear_all(self):
        reply = QMessageBox.question(
            self, "Clear All",
            "Are you sure you want to delete all saved results?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for f in glob.glob(os.path.join(self.saves_dir, "*.json")):
                os.remove(f)
            self.refresh_list()

    def export_single(self, data):
        import pandas as pd
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Result",
            f"{data.get('gene','result')}.csv",
            "CSV Files (*.csv)"
        )
        if path:
            df = pd.DataFrame([{
                k: v for k, v in data.items()
                if k != "gel_image"
            }])
            df.to_csv(path, index=False)

    def _btn_style(self, bg="#313244", color="#cdd6f4"):
        return f"""
            QPushButton {{
                background: {bg};
                color: {color};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: #45475a; }}
        """