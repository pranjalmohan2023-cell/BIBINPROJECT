"""Professional SI-unit input interface for the Turbojet Engine Designer.

The PyCycle backend continues to receive its original imperial inputs.  All
conversion is deliberately isolated in ``build_*_backend_inputs`` below.
"""

import sys
import os

from PySide6.QtCore import QElapsedTimer, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication, QDoubleSpinBox, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QMainWindow, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from gui import EngineWindow
from t3 import run_engine


METRES_PER_FOOT = 0.3048
NEWTONS_PER_LBF = 4.4482216152605
KELVIN_PER_DEGR = 5.0 / 9.0


class InputWindow(QMainWindow):
    """Gather design/off-design inputs and launch the unchanged PyCycle model."""

    def __init__(self):
        super().__init__()
        self._launching_output = False
        self.output = None
        self.last_setup_file = "last_setup.txt"
        self.elapsed = QElapsedTimer()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stopwatch)

        self.setWindowTitle("Turbojet Engine Designer")
        self.resize(1340, 790)
        self.setMinimumSize(1010, 650)
        self.apply_styles()
        self.build_ui()

    def apply_styles(self):
        """Use one coherent engineering-workstation stylesheet for the window."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #15171A;
                color: #E8EAED;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 15px;
            }
            QLabel {
                background: transparent;
            }
            QFrame#header, QFrame#statusBar {
                background: #1A1D21;
                border: 1px solid #343A40;
                border-radius: 8px;
            }
            QLabel#appTitle { font-size: 25px; font-weight: 700; letter-spacing: 0.5px; }
            QLabel#subtitle { color: #9AA0A6; font-size: 15px; }
            QLabel#sectionHint { color: #9AA0A6; font-size: 12.5px; }
            QLabel#statusIndicator { font-weight: 700; }
            QGroupBox {
                background: #1D2024;
                border: 1px solid #343A40;
                border-radius: 8px;
                margin-top: 14px;
                padding: 15px 14px 14px 14px;
                font-size: 13px;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 13px;
                padding: 0 5px;
                color: #E8EAED;
            }
            QLabel#subsection { color: #9AA0A6; font-size: 15px; font-weight: 700; padding-top: 5px; }
            QDoubleSpinBox {
                min-height: 30px;
                padding: 2px 8px;
                background: #25292E;
                border: 1px solid #343A40;
                border-radius: 5px;
                color: #E8EAED;
                selection-background-color: #3B82F6;
            }
            QDoubleSpinBox:hover { border-color: #56616C; }
            QDoubleSpinBox:focus { border: 1px solid #3B82F6; }
            QTableWidget {
                background: #202328;
                alternate-background-color: #25292E;
                border: 1px solid #343A40;
                border-radius: 6px;
                gridline-color: #343A40;
                selection-background-color: #244C7C;
                selection-color: #FFFFFF;
                color: #E8EAED;
            }
            QTableWidget::item { padding: 6px 8px; border-bottom: 1px solid #2D3339; }
            QHeaderView::section {
                background: #2A2E34;
                color: #E8EAED;
                border: none;
                border-bottom: 1px solid #3E464F;
                padding: 8px;
                font-weight: 700;
            }
            QPushButton {
                min-height: 30px;
                padding: 3px 12px;
                background: #2A2E34;
                border: 1px solid #414952;
                border-radius: 5px;
                color: #E8EAED;
                font-weight: 600;
            }
            QPushButton:hover { background: #343A40; border-color: #65717D; }
            QPushButton:pressed { background: #202328; }
            QPushButton#deleteButton { color: #FFB4AB; }
            QPushButton#deleteButton:hover { background: #42262A; border-color: #A9575D; }
            QPushButton#runButton {
                min-height: 42px;
                padding: 4px 22px;
                background: #2563B8;
                border: 1px solid #4A93ED;
                border-radius: 6px;
                color: white;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#runButton:hover { background: #3B82F6; }
            QPushButton#runButton:pressed { background: #1E4F91; }
            QPushButton#runButton:disabled { background: #283542; color: #8C9AA8; border-color: #364350; }
            QMessageBox { background: #1D2024; }
        """)

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(20, 18, 20, 18)
        main.setSpacing(15)

        main.addWidget(self.create_header())

        content = QHBoxLayout()
        content.setSpacing(16)
        main.addLayout(content, 1)
        content.addWidget(self.create_design_panel(), 0)
        content.addWidget(self.create_off_design_panel(), 1)

        main.addWidget(self.create_status_bar())

    def create_header(self):
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 13, 18, 13)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("TURBOJET ENGINE DESIGNER")
        title.setObjectName("appTitle")
        subtitle = QLabel("Preliminary Engine Performance Analysis")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)
        layout.addStretch()
        self.header_status = QLabel()
        self.header_status.setObjectName("statusIndicator")
        self.set_status("READY")
        layout.addWidget(self.header_status)
        return header

    def create_design_panel(self):
        panel = QGroupBox("DESIGN POINT")
        layout = QVBoxLayout(panel)
        layout.setSpacing(9)
        hint = QLabel("Flight & engine conditions")
        hint.setObjectName("sectionHint")
        layout.addWidget(hint)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(9)
        layout.addWidget(self.section_label("FLIGHT CONDITIONS"))

        self.altitude = self.spin(0, 16000, 0.0, 0.0, 1, " m", "Flight altitude at the design point.\nInput in metres.")
        self.mach = self.spin(0, 2, 0.100, 0.001, 3, "", "Freestream Mach number at the design point.")
        self.fn = self.spin(1, 25000, 1000.0, 10.0, 1, " N", "Required net engine thrust.\nInput in Newtons.")
        form.addRow("Altitude", self.altitude)
        form.addRow("Mach Number", self.mach)
        form.addRow("Target Thrust", self.fn)

        layout.addLayout(form)
        layout.addSpacing(6)
        layout.addWidget(self.section_label("CYCLE PARAMETERS"))

        cycle_form = QFormLayout()
        cycle_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        cycle_form.setHorizontalSpacing(16)
        cycle_form.setVerticalSpacing(9)
        self.t4 = self.spin(300, 2500, 949.1, 1.0, 1, " °C", "Turbine inlet temperature.\nInput in Celsius.")
        self.pr = self.spin(1.01, 20, 4.00, 0.05, 2, "", "Overall compressor pressure ratio.")
        self.compEff = self.spin(50, 100, 83.0, 0.5, 1, " %", "Isentropic compressor efficiency.")
        self.turbEff = self.spin(50, 100, 86.0, 0.5, 1, " %", "Isentropic turbine efficiency.")
        cycle_form.addRow("Turbine Inlet Temperature", self.t4)
        cycle_form.addRow("Pressure Ratio", self.pr)
        cycle_form.addRow("Compressor Efficiency", self.compEff)
        cycle_form.addRow("Turbine Efficiency", self.turbEff)
        layout.addLayout(cycle_form)
        layout.addStretch()
        return panel

    def create_off_design_panel(self):
        panel = QGroupBox("OFF-DESIGN OPERATING POINTS")
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        hint = QLabel("Operating conditions evaluated after the design-point solution")
        hint.setObjectName("sectionHint")
        layout.addWidget(hint)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Mach", "Altitude (ft)", "T4 (°C)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.verticalHeader().setMinimumWidth(35)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setMinimumWidth(540)
        self.table.setToolTip("Editable off-design operating conditions in SI units.")
        layout.addWidget(self.table, 1)

        controls = QHBoxLayout()
        self.addBtn = QPushButton("＋ Add Point")
        self.delBtn = QPushButton("− Delete Point")
        self.duplicateBtn = QPushButton("⧉ Duplicate Point")
        self.delBtn.setObjectName("deleteButton")
        self.addBtn.setToolTip("Add an off-design operating point.")
        self.delBtn.setToolTip("Remove the selected operating point.")
        controls.addWidget(self.addBtn)
        controls.addWidget(self.duplicateBtn)
        controls.addWidget(self.delBtn)
        controls.addStretch()
        layout.addLayout(controls)
        self.addBtn.clicked.connect(self.add_row)
        self.duplicateBtn.clicked.connect(self.duplicate_row)
        self.delBtn.clicked.connect(self.delete_row)

        # The former ft/degR defaults are shown in SI units for this UI.
        if os.path.exists(self.last_setup_file):
            with open(self.last_setup_file, "r") as f:
                for line in f:
                    values = line.strip().split(",")
                    if len(values) == 3:
                        self.add_row(
                            float(values[0]),
                            float(values[1]),
                            float(values[2])
                        )
        else:
            for mach, altitude_m in (
                    (0.05, 0),
                    (0.075, 61),
                    (0.10, 122),
                    (0.15, 183),
                    (0.175, 244),
                    (0.20, 305),
                    (0.25, 366),
                    (0.30, 427),
                    (0.35, 488),
                    (0.40, 549)
            ):
                self.add_row(mach, altitude_m, 949.1)
        return panel

    def create_status_bar(self):
        bar = QFrame()
        bar.setObjectName("statusBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 10, 8)
        self.status = QLabel()
        self.status.setObjectName("statusIndicator")
        self.stopwatch = QLabel("Elapsed: 0.00 s")
        self.runBtn = QPushButton("▶  RUN ENGINE")
        self.runBtn.setObjectName("runButton")
        self.runBtn.clicked.connect(self.run_clicked)
        layout.addWidget(self.status)
        layout.addStretch()
        layout.addWidget(self.stopwatch)
        layout.addSpacing(18)
        layout.addWidget(self.runBtn)
        return bar

    @staticmethod
    def section_label(text):
        label = QLabel(text)
        label.setObjectName("subsection")
        return label

    @staticmethod
    def spin(minimum, maximum, value, step, decimals, suffix, tooltip):
        control = QDoubleSpinBox()
        control.setRange(minimum, maximum)
        control.setValue(value)
        control.setSingleStep(step)
        control.setDecimals(decimals)
        control.setSuffix(suffix)
        control.setMinimumWidth(170)
        control.setToolTip(tooltip)
        return control

    def set_status(self, state):
        colors = {"READY": "#22C55E", "RUNNING": "#F59E0B", "CONVERGED": "#22C55E", "FAILED": "#EF4444"}
        text = {"READY": "Ready", "RUNNING": "Running...", "CONVERGED": "Converged", "FAILED": "Failed"}[state]
        rich_text = f'<span style="color:{colors[state]}">●</span> {state}'
        if hasattr(self, "header_status"):
            self.header_status.setText(rich_text)
        if hasattr(self, "status"):
            self.status.setText(f'<span style="color:{colors[state]}">●</span> Status: {text}')

    def add_row(self, mach=0.0, altitude_m=0.0, t4_k=949.1):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Point index starts from 0
        index_item = QTableWidgetItem(str(row))
        index_item.setTextAlignment(Qt.AlignCenter)
        self.table.setVerticalHeaderItem(row, index_item)

        values = (mach, altitude_m, t4_k)

        for column, value in enumerate(values):
            item = QTableWidgetItem(
                f"{value:.3f}" if column == 0 else f"{value:.1f}"
            )
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, column, item)

        self.table.setRowHeight(row, 32)

    def duplicate_row(self):
        row = self.table.currentRow()

        if row < 0:
            self.show_validation_error(
                "Select an off-design point to duplicate.",
                "No Point Selected"
            )
            return

        values = []

        for column in range(self.table.columnCount()):
            item = self.table.item(row, column)

            if item is None:
                return

            values.append(item.text())

        try:
            mach = float(values[0])
            altitude = float(values[1])
            t4 = float(values[2])
        except ValueError:
            self.show_validation_error(
                "The selected point contains invalid data.",
                "Invalid Point"
            )
            return

        # Insert immediately below the selected point
        new_row = row + 1
        self.table.insertRow(new_row)

        # Re-create the index
        index_item = QTableWidgetItem(str(new_row))
        index_item.setTextAlignment(Qt.AlignCenter)
        self.table.setVerticalHeaderItem(new_row, index_item)

        new_values = (mach, altitude, t4)

        for column, value in enumerate(new_values):
            item = QTableWidgetItem(
                f"{value:.3f}" if column == 0 else f"{value:.1f}"
            )

            item.setTextAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )

            self.table.setItem(new_row, column, item)

        self.table.setRowHeight(new_row, 32)

        # Re-index everything after insertion
        for i in range(self.table.rowCount()):
            index_item = QTableWidgetItem(str(i))
            index_item.setTextAlignment(Qt.AlignCenter)
            self.table.setVerticalHeaderItem(i, index_item)

        self.table.selectRow(new_row)

        self.save_last_setup()
    def delete_row(self):
        row = self.table.currentRow()

        if row >= 0:
            self.table.removeRow(row)

            # Re-index remaining points from 0
            for i in range(self.table.rowCount()):
                index_item = QTableWidgetItem(str(i))
                index_item.setTextAlignment(Qt.AlignCenter)
                self.table.setVerticalHeaderItem(i, index_item)

    def build_design_backend_inputs(self):
        """Convert SI display values to the units expected by the unchanged backend."""
        return {
            "alt": self.altitude.value() / METRES_PER_FOOT,
            "mach": self.mach.value(),
            "Fn": self.fn.value() / NEWTONS_PER_LBF,
            "T4": (self.t4.value() + 273.15) / KELVIN_PER_DEGR,
            "PR": self.pr.value(),
            "comp_eff": self.compEff.value() / 100.0,
            "turb_eff": self.turbEff.value() / 100.0,
        }

    def build_off_design_backend_inputs(self):
        points = []
        for row in range(self.table.rowCount()):
            try:
                mach = float(self.table.item(row, 0).text())
                altitude_ft = float(self.table.item(row, 1).text())
                t4_k = float(self.table.item(row, 2).text())
                if not 0 <= mach <= 2 or altitude_ft < 0 or t4_k <= 0:
                    raise ValueError
            except (AttributeError, ValueError):
                raise ValueError(f"Off-design point {row + 1} contains invalid SI data.")
            points.append({
                "mach": mach,
                "alt": altitude_ft,
                "T4": (t4_k + 273.15) / KELVIN_PER_DEGR
            })
        return points

    def update_stopwatch(self):
        self.stopwatch.setText(f"Elapsed: {self.elapsed.elapsed() / 1000:.2f} s")

    def run_clicked(self):
        if self.pr.value() <= 1:
            self.show_validation_error("Pressure Ratio must be greater than 1.")
            return
        if self.compEff.value() > 100 or self.turbEff.value() > 100:
            self.show_validation_error("Efficiency cannot exceed 100%.")
            return
        try:
            design_inputs = self.build_design_backend_inputs()
            od_inputs = self.build_off_design_backend_inputs()
        except ValueError as error:
            self.show_validation_error(str(error), "Invalid Off-Design Point")
            return

        self.runBtn.setEnabled(False)
        self.runBtn.setText("RUNNING...")
        self.set_status("RUNNING")
        QApplication.processEvents()
        self.elapsed.start()
        self.timer.start(100)
        try:
            self.save_setup()
            prob, od_pts = run_engine(design_inputs, od_inputs)
        except Exception as error:
            self.timer.stop()
            self.runBtn.setEnabled(True)
            self.runBtn.setText("▶  RUN ENGINE")
            self.set_status("FAILED")
            QMessageBox.critical(self, "Solver Error", str(error)) #dsfs
            return

        self.timer.stop()
        elapsed = self.elapsed.elapsed() / 1000
        self.stopwatch.setText(f"Completed: {elapsed:.2f} s")
        self.runBtn.setEnabled(True)
        self.runBtn.setText("▶  RUN ENGINE")
        self.set_status("CONVERGED")
        self.output = EngineWindow(prob, od_pts)
        self.output.showMaximized()

        self._launching_output = True
        self.output.raise_()
        self.output.activateWindow()
    def show_validation_error(self, message, title="Invalid Input"):
        QMessageBox.warning(self, title, message)

    def closeEvent(self, event):

        if self._launching_output:
            event.accept()
            return

        reply = QMessageBox.question(
            self,
            "Exit",
            "Exit Turbojet Designer?",
            QMessageBox.Yes |
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def save_setup(self):
        with open(self.last_setup_file, "w") as f:
            for row in range(self.table.rowCount()):
                values = [
                    self.table.item(row, col).text()
                    for col in range(3)
                ]
                f.write(",".join(values) + "\n")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#15171A"))
    palette.setColor(QPalette.WindowText, QColor("#E8EAED"))
    app.setPalette(palette)
    window = InputWindow()
    window.show()
    sys.exit(app.exec())
