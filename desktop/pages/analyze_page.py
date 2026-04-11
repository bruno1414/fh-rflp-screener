import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
import base64
from app.core.pipeline import run_full_analysis


class AnalysisWorker(QThread):
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, gene, cdna, chrom, pos, ref, alt):
        super().__init__()
        self.gene  = gene
        self.cdna  = cdna
        self.chrom = chrom
        self.pos   = pos
        self.ref   = ref
        self.alt   = alt

    def run(self):
        try:
            self.progress.emit("Fetching sequence from Ensembl...")
            result = run_full_analysis(
                self.gene, self.cdna,
                self.chrom, self.pos,
                self.ref, self.alt
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AnalyzePage(QWidget):
    def __init__(self):
        super().__init__()
        self.worker       = None
        self.current_data = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Run Analysis")
        title.setStyleSheet(
            "color: #cdd6f4; font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title)

        subtitle = QLabel(
            "Submit any FH mutation to scan 623 restriction enzymes "
            "and generate a gel simulation."
        )
        subtitle.setStyleSheet("color: #6c7086; font-size: 12px;")
        layout.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(16)

        # ── Left: input form ──────────────────────────────────
        form_widget = QWidget()
        form_widget.setFixedWidth(320)
        form_widget.setStyleSheet("background: #181825; border-radius: 8px;")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(12)

        form_title = QLabel("Mutation Input")
        form_title.setStyleSheet(
            "color: #cdd6f4; font-size: 14px; font-weight: bold;"
        )
        form_layout.addWidget(form_title)

        form_layout.addWidget(self._field_label("Gene"))
        self.gene_combo = QComboBox()
        self.gene_combo.addItems(["LDLR", "APOB", "PCSK9"])
        self.gene_combo.setStyleSheet(self._input_style())
        form_layout.addWidget(self.gene_combo)

        form_layout.addWidget(self._field_label("cDNA Change"))
        self.cdna_input = QLineEdit()
        self.cdna_input.setPlaceholderText("e.g. c.408C>G")
        self.cdna_input.setStyleSheet(self._input_style())
        form_layout.addWidget(self.cdna_input)

        row1 = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(self._field_label("Chromosome"))
        self.chrom_input = QLineEdit()
        self.chrom_input.setPlaceholderText("e.g. 19")
        self.chrom_input.setStyleSheet(self._input_style())
        col1.addWidget(self.chrom_input)
        row1.addLayout(col1)

        col2 = QVBoxLayout()
        col2.addWidget(self._field_label("Position (GRCh38)"))
        self.pos_input = QLineEdit()
        self.pos_input.setPlaceholderText("e.g. 11105314")
        self.pos_input.setStyleSheet(self._input_style())
        col2.addWidget(self.pos_input)
        row1.addLayout(col2)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        col3 = QVBoxLayout()
        col3.addWidget(self._field_label("Reference allele"))
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("e.g. C")
        self.ref_input.setMaxLength(1)
        self.ref_input.setStyleSheet(self._input_style())
        col3.addWidget(self.ref_input)
        row2.addLayout(col3)

        col4 = QVBoxLayout()
        col4.addWidget(self._field_label("Alternate allele"))
        self.alt_input = QLineEdit()
        self.alt_input.setPlaceholderText("e.g. G")
        self.alt_input.setMaxLength(1)
        self.alt_input.setStyleSheet(self._input_style())
        col4.addWidget(self.alt_input)
        row2.addLayout(col4)
        form_layout.addLayout(row2)

        self.run_btn = QPushButton("Run Analysis")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #b4befe; }
            QPushButton:disabled { background: #45475a; color: #6c7086; }
        """)
        self.run_btn.clicked.connect(self.run_analysis)
        form_layout.addWidget(self.run_btn)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6c7086; font-size: 11px;")
        self.status_label.setWordWrap(True)
        form_layout.addWidget(self.status_label)

        examples_label = QLabel("Quick examples:")
        examples_label.setStyleSheet(
            "color: #6c7086; font-size: 11px; margin-top: 8px;"
        )
        form_layout.addWidget(examples_label)

        examples = [
            ("LDLR c.408C>G",  "LDLR", "c.408C>G",  "19", "11105314", "C", "G"),
            ("LDLR c.1865A>T", "LDLR", "c.1865A>T", "19", "11120111", "A", "T"),
            ("APOB c.9721G>T", "APOB", "c.9721G>T", "2",  "21085170", "G", "T"),
        ]
        for label, *vals in examples:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background: #313244;
                    color: #89b4fa;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 11px;
                    text-align: left;
                }
                QPushButton:hover { background: #45475a; }
            """)
            btn.clicked.connect(lambda _, v=vals: self.fill_example(*v))
            form_layout.addWidget(btn)

        form_layout.addStretch()
        content.addWidget(form_widget)

        # ── Right: results ────────────────────────────────────
        self.results_widget = QWidget()
        self.results_widget.setStyleSheet(
            "background: #181825; border-radius: 8px;"
        )
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setContentsMargins(16, 16, 16, 16)

        self.idle_label = QLabel(
            "Fill in the mutation details and\nclick Run Analysis to see results."
        )
        self.idle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.idle_label.setStyleSheet("color: #45475a; font-size: 13px;")
        self.results_layout.addWidget(
            self.idle_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.results_layout.addStretch()
        content.addWidget(self.results_widget)
        layout.addLayout(content)

        self.save_btn = QPushButton("Save This Result")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #16a34a;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover { background: #15803d; }
            QPushButton:disabled { background: #45475a; color: #6c7086; }
        """)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_result)
        layout.addWidget(self.save_btn)

    def fill_example(self, gene, cdna, chrom, pos, ref, alt):
        self.gene_combo.setCurrentText(gene)
        self.cdna_input.setText(cdna)
        self.chrom_input.setText(chrom)
        self.pos_input.setText(pos)
        self.ref_input.setText(ref)
        self.alt_input.setText(alt)

    def run_analysis(self):
        gene  = self.gene_combo.currentText()
        cdna  = self.cdna_input.text().strip()
        chrom = self.chrom_input.text().strip()
        pos   = self.pos_input.text().strip()
        ref   = self.ref_input.text().strip()
        alt   = self.alt_input.text().strip()

        if not all([cdna, chrom, pos, ref, alt]):
            self.status_label.setText("Please fill in all fields.")
            self.status_label.setStyleSheet("color: #f38ba8; font-size: 11px;")
            return

        self.run_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.status_label.setText("Fetching sequence from Ensembl...")
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 11px;")

        self.worker = AnalysisWorker(gene, cdna, chrom, pos, ref, alt)
        self.worker.finished.connect(self.show_results)
        self.worker.progress.connect(lambda msg: self.status_label.setText(msg))
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def show_results(self, data):
        self.run_btn.setEnabled(True)
        self.current_data = data

        if "error" in data:
            self.show_error(data["error"])
            return

        self.status_label.setText("Analysis complete!")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 11px;")

        for i in reversed(range(self.results_layout.count())):
            w = self.results_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        title = QLabel(f"{data['gene']}  {data['cdna_change']}")
        title.setStyleSheet(
            "color: #cdd6f4; font-size: 15px; font-weight: bold;"
        )
        self.results_layout.addWidget(title)

        fields = [
            ("Best Enzyme",         data["best_enzyme"]),
            ("Site Change",         data["change_type"].replace("_", " ")),
            ("WT Fragments",        ", ".join(str(x) for x in data["wt_frags"]) + " bp"),
            ("Mutant Fragments",    ", ".join(str(x) for x in data["mut_frags"]) + " bp"),
            ("Fragment Difference", str(data["frag_diff_bp"]) + " bp"),
            ("Gel Quality",         data["gel_quality"]),
            ("Enzymes Found",       str(data["n_enzymes"])),
        ]
        for label, value in fields:
            row = QHBoxLayout()
            lbl = QLabel(label + ":")
            lbl.setStyleSheet("color: #6c7086; font-size: 12px;")
            lbl.setFixedWidth(150)
            val = QLabel(value)
            val.setStyleSheet(
                "color: #cdd6f4; font-size: 12px; font-weight: bold;"
            )
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            self.results_layout.addLayout(row)

        gel_title = QLabel("Gel Simulation")
        gel_title.setStyleSheet("color: #6c7086; font-size: 11px; margin-top: 8px;")
        self.results_layout.addWidget(gel_title)

        img_data = base64.b64decode(data["gel_image"])
        pixmap   = QPixmap()
        pixmap.loadFromData(img_data)
        scaled   = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
        gel_lbl  = QLabel()
        gel_lbl.setPixmap(scaled)
        gel_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gel_lbl.setStyleSheet(
            "background: #11111b; border-radius: 6px; padding: 8px;"
        )
        self.results_layout.addWidget(gel_lbl)
        self.results_layout.addStretch()
        self.save_btn.setEnabled(True)

    def show_error(self, msg):
        self.run_btn.setEnabled(True)
        self.status_label.setText(f"Error: {msg}")
        self.status_label.setStyleSheet("color: #f38ba8; font-size: 11px;")

    def save_result(self):
        if not self.current_data:
            return

        saves_dir = os.path.join(os.path.expanduser("~"), "FH_RFLP_Saves")
        os.makedirs(saves_dir, exist_ok=True)

        gene       = self.current_data.get("gene", "result")
        cdna       = self.current_data.get("cdna_change", "")
        cdna_clean = cdna.replace(">", "-").replace(":", "_").replace("/", "_").replace(" ", "_")
        filename   = f"{gene}_{cdna_clean}_result.json"
        path       = os.path.join(saves_dir, filename)

        save_data = {k: v for k, v in self.current_data.items()}
        with open(path, "w") as f:
            json.dump(save_data, f, indent=2)

        QMessageBox.information(
            self, "Saved",
            f"Result saved!\n\nView it in the Saved Results tab."
        )

    def _field_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #6c7086; font-size: 11px;")
        return lbl

    def _input_style(self):
        return """
            QLineEdit, QComboBox {
                background: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 7px 10px;
                color: #cdd6f4;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #89b4fa; }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { color: #6c7086; }
        """