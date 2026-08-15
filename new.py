import sys

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from t3 import run_engine
from gui import EngineWindow


class InputWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.output = None

        self.setWindowTitle("Turbojet Designer")

        self.resize(1350, 850)

        self.elapsed = QElapsedTimer()

        self.timer = QTimer()

        self.timer.timeout.connect(self.update_stopwatch)

        self.build_ui()

    ###########################################################

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        main = QVBoxLayout()

        central.setLayout(main)

        #########################################################

        title = QLabel("Turbojet Engine Designer")

        font = title.font()

        font.setPointSize(18)

        font.setBold(True)

        title.setFont(font)

        title.setAlignment(Qt.AlignCenter)

        main.addWidget(title)

        #########################################################

        middle = QHBoxLayout()

        main.addLayout(middle)

        #########################################################
        # LEFT SIDE
        #########################################################

        left = QGroupBox("Design Point")

        middle.addWidget(left)

        form = QFormLayout()

        left.setLayout(form)

        self.altitude = QDoubleSpinBox()
        self.altitude.setRange(0, 15000)
        self.altitude.setValue(0)
        self.altitude.setSuffix(" m")

        self.mach = QDoubleSpinBox()
        self.mach.setRange(0, 2)
        self.mach.setDecimals(3)
        self.mach.setValue(0.10)

        self.fn = QDoubleSpinBox()
        self.fn.setRange(1, 50000)
        self.fn.setValue(1000)
        self.fn.setSuffix(" N")

        self.t4 = QDoubleSpinBox()
        self.t4.setRange(300, 2500)
        self.t4.setValue(1222)
        self.t4.setSuffix(" K")

        self.pr = QDoubleSpinBox()
        self.pr.setRange(1, 20)
        self.pr.setValue(8)

        self.compEff = QDoubleSpinBox()
        self.compEff.setRange(0.5, 1.0)
        self.compEff.setDecimals(3)
        self.compEff.setValue(0.83)

        self.turbEff = QDoubleSpinBox()
        self.turbEff.setRange(0.5, 1.0)
        self.turbEff.setDecimals(3)
        self.turbEff.setValue(0.86)

        form.addRow("Altitude", self.altitude)
        form.addRow("Mach", self.mach)
        form.addRow("Target Thrust", self.fn)

        form.addRow("T4 ★", self.t4)
        form.addRow("Pressure Ratio ★", self.pr)
        form.addRow("Compressor Eff ★", self.compEff)
        form.addRow("Turbine Eff ★", self.turbEff)

        #########################################################
        # RIGHT SIDE
        #########################################################

        right = QGroupBox("Off Design Points")

        middle.addWidget(right)

        rightLayout = QVBoxLayout()

        right.setLayout(rightLayout)

        self.table = QTableWidget()

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(
            [
                "Mach",
                "Altitude (m)",
                "T4 (K)"
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        rightLayout.addWidget(self.table)

        #########################################################

        btns = QHBoxLayout()

        rightLayout.addLayout(btns)

        self.addBtn = QPushButton("+ Add Row")

        self.delBtn = QPushButton("- Delete Row")

        btns.addWidget(self.addBtn)

        btns.addWidget(self.delBtn)

        #########################################################

        self.addBtn.clicked.connect(self.add_row)

        self.delBtn.clicked.connect(self.delete_row)

        #########################################################

        defaults = [

            (0.05, 0, 1222),
            (0.075, 60, 1222),
            (0.10, 120, 1222),
            (0.15, 180, 1222),
            (0.175, 240, 1222),
            (0.20, 300, 1222),
            (0.25, 360, 1222),
            (0.30, 420, 1222),
            (0.35, 480, 1222),
            (0.40, 540, 1222),

        ]

        for m, a, t in defaults:
            self.add_row(m, a, t)

        #########################################################

        bottom = QHBoxLayout()

        main.addLayout(bottom)

        self.status = QLabel("Status : Ready")

        self.stopwatch = QLabel("Elapsed : 0.00 s")

        self.runBtn = QPushButton("RUN ENGINE")

        self.runBtn.setMinimumHeight(45)

        font = self.runBtn.font()

        font.setPointSize(12)

        font.setBold(True)

        self.runBtn.setFont(font)

        bottom.addWidget(self.status)

        bottom.addStretch()

        bottom.addWidget(self.stopwatch)

        bottom.addSpacing(30)

        bottom.addWidget(self.runBtn)

        #########################################################

        self.runBtn.clicked.connect(self.run_clicked)

    ###########################################################

    def add_row(self, mach=0, alt=0, t4=2200):

        row = self.table.rowCount()

        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(str(mach)))

        self.table.setItem(row, 1, QTableWidgetItem(str(alt)))

        self.table.setItem(row, 2, QTableWidgetItem(str(t4)))

    ###########################################################

    def delete_row(self):

        row = self.table.currentRow()

        if row >= 0:
            self.table.removeRow(row)

    def get_table_data(self):

        data = []

        for row in range(self.table.rowCount()):
            data.append({

                "mach": float(self.table.item(row, 0).text()),

                "alt": float(self.table.item(row, 1).text()),

                "T4": float(self.table.item(row, 2).text())

            })

        return data

    ###########################################################

    def update_stopwatch(self):

        t = self.elapsed.elapsed() / 1000

        self.stopwatch.setText(f"Elapsed : {t:.2f} s")

    ###########################################################

    ###########################################################
    # RUN BUTTON
    ###########################################################

    def run_clicked(self):

        # ----------------------------
        # Validate Design Inputs
        # ----------------------------

        if self.pr.value() <= 1:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Pressure Ratio must be greater than 1."
            )
            return

        if self.compEff.value() > 1:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Compressor efficiency cannot exceed 1."
            )
            return

        if self.turbEff.value() > 1:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Turbine efficiency cannot exceed 1."
            )
            return

        # ----------------------------
        # Build Design Dictionary
        # ----------------------------

        FT_PER_M = 3.28084
        LBF_PER_N = 0.224809
        DEGR_PER_K = 1.8

        design_inputs = {

            "alt": self.altitude.value() * FT_PER_M,

            "mach": self.mach.value(),

            "Fn": self.fn.value() * LBF_PER_N,

            "T4": self.t4.value() * DEGR_PER_K,

            "PR": self.pr.value(),

            "comp_eff": self.compEff.value(),

            "turb_eff": self.turbEff.value()

        }

        # ----------------------------
        # Build Off Design List
        # ----------------------------

        od_inputs = []

        for row in range(self.table.rowCount()):

            try:

                mach = float(self.table.item(row, 0).text())

                alt = float(self.table.item(row, 1).text())

                t4 = float(self.table.item(row, 2).text())

            except Exception:

                QMessageBox.warning(

                    self,

                    "Invalid Row",

                    f"Off Design Row {row + 1} contains invalid data."

                )

                return

            od_inputs.append({

                "mach": mach,

                "alt": alt * FT_PER_M,

                "T4": t4 * DEGR_PER_K

            })

        # ----------------------------
        # Disable Run Button
        # ----------------------------

        self.runBtn.setEnabled(False)

        self.status.setText("Status : Running...")

        QApplication.processEvents()

        # ----------------------------
        # Stopwatch
        # ----------------------------

        self.elapsed.start()

        self.timer.start(100)

        # ----------------------------
        # Run PyCycle
        # ----------------------------

        try:

            prob, od_pts = run_engine(

                design_inputs,

                od_inputs

            )

        except Exception as e:

            self.timer.stop()

            self.runBtn.setEnabled(True)

            self.status.setText("Status : Failed")

            QMessageBox.critical(

                self,

                "Solver Error",

                str(e)

            )

            return

        # ----------------------------
        # Solver Finished
        # ----------------------------

        self.timer.stop()

        elapsed = self.elapsed.elapsed() / 1000

        self.stopwatch.setText(

            f"Completed : {elapsed:.2f} s"

        )

        self.status.setText(

            "Status : Converged"

        )

        self.runBtn.setEnabled(True)

        # ----------------------------
        # Launch Output GUI
        # ----------------------------

        self.output = EngineWindow(

            prob,

            od_pts

        )

        self.output.show()

        self.close()

    ###########################################################

    def closeEvent(self, event):

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


app = QApplication(sys.argv)

window = InputWindow()

window.show()

sys.exit(app.exec())
