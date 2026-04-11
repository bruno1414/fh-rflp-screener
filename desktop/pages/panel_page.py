import os
import sys
import json
import base64
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor
from app.core.panel import get_panel_summary, get_mutation_detail, search_panel


class GelWorker(QThread):
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, cdna_change):
        super().__init__()
        self.cdna_change = cdna_change

    def run(self):
        try:
            result = get_mutation_detail(self.cdna_change)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class PanelPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_worker = None
        self.current_data   = None
        self.setup_ui()
        self.load_panel()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Panel Lookup")
        title.setStyleSheet(
            "color: #cdd6f4; font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title)

        subtitle = QLabel(
            "Search and explore the recommended FH RFLP screening panel. "
            "Click any row to view gel simulation."
        )
        subtitle.setStyleSheet("color: #6c7086; font-size: 12px;")
        layout.addWidget(subtitle)

        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "Search by gene, mutation, or enzyme..."
        )
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
                color: #cdd6f4;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
        """)
        self.search_box.textChanged.connect(self.handle_search)
        search_layout.addWidget(self.search_box)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(self._btn_style())
        clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_btn)
        layout.addLayout(search_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #313244; }")

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Gene", "cDNA Change", "Enzyme",
            "Site Change", "Diff (bp)", "Quality", "Score"
        ])
        self.table.setStyleSheet("""
            QTableWidget {
                background: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                gridline-color: #313244;
                color: #cdd6f4;
                font-size: 12px;
            }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected {
                background: #313244;
                color: #cdd6f4;
            }
            QHeaderView::section {
                background: #11111b;
                color: #6c7086;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #313244;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        splitter.addWidget(self.table)

        self.detail_panel = self._make_detail_panel()
        splitter.addWidget(self.detail_panel)
        splitter.setSizes([550, 350])
        layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Result")
        save_btn.setStyleSheet(self._btn_style("#16a34a"))
        save_btn.clicked.connect(self.save_result)
        btn_layout.addWidget(save_btn)

        export_btn = QPushButton("Export Panel CSV")
        export_btn.setStyleSheet(self._btn_style())
        export_btn.clicked.connect(self.export_csv)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _make_detail_panel(self):
        panel = QWidget()
        panel.setStyleSheet("background: #181825; border-radius: 8px;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)

        self.detail_title = QLabel("Select a mutation to view details")
        self.detail_title.setStyleSheet(
            "color: #cdd6f4; font-size: 14px; font-weight: bold;"
        )
        layout.addWidget(self.detail_title)

        self.detail_loading = QLabel("Loading gel simulation...")
        self.detail_loading.setStyleSheet("color: #6c7086; font-size: 12px;")
        self.detail_loading.hide()
        layout.addWidget(self.detail_loading)

        self.gel_label = QLabel()
        self.gel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gel_label.setStyleSheet(
            "background: #11111b; border-radius: 6px; padding: 8px;"
        )
        self.gel_label.setMinimumHeight(200)
        layout.addWidget(self.gel_label)

        self.info_labels = {}
        fields = [
            ("enzyme",    "Best Enzyme"),
            ("change",    "Site Change"),
            ("wt_frags",  "WT Fragments"),
            ("mut_frags", "Mutant Fragments"),
            ("diff",      "Fragment Diff"),
            ("score",     "RFLP Score"),
        ]
        for key, label in fields:
            row = QHBoxLayout()
            lbl = QLabel(label + ":")
            lbl.setStyleSheet("color: #6c7086; font-size: 12px;")
            lbl.setFixedWidth(120)
            val = QLabel("—")
            val.setStyleSheet("color: #cdd6f4; font-size: 12px;")
            self.info_labels[key] = val
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            layout.addLayout(row)

        layout.addStretch()
        return panel

    def load_panel(self):
        try:
            self.mutations = get_panel_summary()
            self.populate_table(self.mutations)
        except Exception as e:
            print(f"Error loading panel: {e}")

    def populate_table(self, mutations):
        self.table.setRowCount(len(mutations))
        for i, m in enumerate(mutations):
            gene_item = QTableWidgetItem(m["gene"])
            gene_item.setForeground(QColor("#89b4fa"))
            self.table.setItem(i, 0, gene_item)

            cdna_item = QTableWidgetItem(m["cdna_change"])
            cdna_item.setForeground(QColor("#cdd6f4"))
            self.table.setItem(i, 1, cdna_item)

            self.table.setItem(i, 2, QTableWidgetItem(m["best_enzyme"]))

            change = m["change_type"].replace("_", " ").title()
            self.table.setItem(i, 3, QTableWidgetItem(change))

            diff_item = QTableWidgetItem(str(m["frag_diff_bp"]) + " bp")
            diff_item.setForeground(QColor("#a6e3a1"))
            self.table.setItem(i, 4, diff_item)

            qual_item = QTableWidgetItem(m["gel_quality"])
            qual_item.setForeground(QColor("#a6e3a1"))
            self.table.setItem(i, 5, qual_item)

            score_item = QTableWidgetItem(str(m["rflp_score"]))
            score_item.setForeground(QColor("#f9e2af"))
            self.table.setItem(i, 6, score_item)

    def handle_search(self, query):
        if not query.strip():
            self.populate_table(self.mutations)
            return
        results = search_panel(query)
        self.populate_table(results)

    def clear_search(self):
        self.search_box.clear()
        self.populate_table(self.mutations)

    def on_row_selected(self):
        if not self.table.selectedItems():
            return
        row  = self.table.currentRow()
        cdna = self.table.item(row, 1).text()
        self.load_detail(cdna)

    def load_detail(self, cdna_change):
        self.detail_title.setText(cdna_change)
        self.detail_loading.show()
        self.gel_label.clear()

        self.current_worker = GelWorker(cdna_change)
        self.current_worker.finished.connect(self.show_detail)
        self.current_worker.error.connect(
            lambda e: self.detail_loading.setText(f"Error: {e}")
        )
        self.current_worker.start()

    def show_detail(self, data):
        self.detail_loading.hide()
        self.current_data = data

        img_data = base64.b64decode(data["gel_image"])
        pixmap   = QPixmap()
        pixmap.loadFromData(img_data)
        scaled   = pixmap.scaledToWidth(
            320, Qt.TransformationMode.SmoothTransformation
        )
        self.gel_label.setPixmap(scaled)

        self.info_labels["enzyme"].setText(data["best_enzyme"])
        self.info_labels["change"].setText(
            data["change_type"].replace("_", " ")
        )
        self.info_labels["wt_frags"].setText(
            ", ".join(str(x) for x in data["wt_frags"]) + " bp"
        )
        self.info_labels["mut_frags"].setText(
            ", ".join(str(x) for x in data["mut_frags"]) + " bp"
        )
        self.info_labels["diff"].setText(str(data["frag_diff_bp"]) + " bp")
        self.info_labels["score"].setText(str(data["rflp_score"]))

    def save_result(self):
        if not self.current_data:
            QMessageBox.warning(
                self, "No Result",
                "Please select a mutation first."
            )
            return

        saves_dir = os.path.join(
            os.path.expanduser("~"), "FH_RFLP_Saves"
        )
        os.makedirs(saves_dir, exist_ok=True)

        gene       = self.current_data.get("gene", "result")
        cdna       = self.current_data.get("cdna_change", "")
        cdna_clean = cdna.replace(">", "-").replace(":", "_").replace("/", "_").replace(" ", "_")
        filename   = f"{gene}_{cdna_clean}.json"
        path       = os.path.join(saves_dir, filename)

        # Keep full payload (including gel_image) so Saved Results can preview gel.
        with open(path, "w") as f:
            json.dump(self.current_data, f, indent=2)

        QMessageBox.information(
            self, "Saved",
            f"Result saved!\n\nView it in the Saved Results tab."
        )

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Panel", "fh_panel.csv", "CSV Files (*.csv)"
        )
        if path:
            df = pd.DataFrame(self.mutations)
            df.to_csv(path, index=False)

    def _btn_style(self, bg="#313244"):
        return f"""
            QPushButton {{
                background: {bg};
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: #45475a; }}
        """