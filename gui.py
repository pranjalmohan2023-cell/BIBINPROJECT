import csv
import os
import sys
from pathlib import Path

# Keep Matplotlib's cache with the project so it can run without needing to
# write into the user's profile directory.
os.environ["MPLCONFIGDIR"] = str(Path(__file__).resolve().parent / ".matplotlib")

from PySide6.QtWidgets import *

from PySide6.QtGui import *

from PySide6.QtCore import *

#from t3 import run_engine

from PySide6.QtGui import QPainter, QColor, QPen
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


STATIONS = ["fc.Fl_O", "inlet.Fl_O", "comp.Fl_O", "burner.Fl_O", "turb.Fl_O", "nozz.Fl_O"]
STATION_LABELS = ["Freestream", "Inlet", "Compressor", "Burner (T4)", "Turbine", "Nozzle"]


def scalar(prob, name, units=None):
    """Return an OpenMDAO value as a plain float."""
    value = prob.get_val(name, units=units) if units else prob.get_val(name)
    return float(value.item())


class AnalysisWindow(QMainWindow):
    """Plot and export the data produced by the most recent engine run."""

    def __init__(self, prob, points):
        super().__init__()
        self.prob = prob
        self.points = points
        self.rows = self.collect_rows()
        self.setWindowTitle("Turbojet Performance Analysis")
        self.resize(1450, 920)
        self.build_ui()

    def collect_rows(self):
        rows = []
        for point in self.points:
            row = {
                "point": point,
                "altitude_ft": scalar(self.prob, f"{point}.fc.alt", "ft"),
                "freestream_mach": scalar(self.prob, f"{point}.fc.Fl_O:stat:MN"),
                "rpm": scalar(self.prob, f"{point}.Nmech", "rpm"),
                "thrust_lbf": scalar(self.prob, f"{point}.perf.Fn", "lbf"),
                "mass_flow_kg_s": scalar(self.prob, f"{point}.inlet.Fl_O:stat:W", "kg/s"),
                "t4_degR": scalar(self.prob, f"{point}.burner.Fl_O:tot:T", "degR"),
                "inlet_area_m2": scalar(self.prob, f"{point}.inlet.Fl_O:stat:area", "m**2"),
                "compressor_exit_area_m2": scalar(self.prob, f"{point}.comp.Fl_O:stat:area", "m**2"),
            }
            row["impeller_diameter_m"] = (4.0 * row["compressor_exit_area_m2"] / 3.141592653589793) ** 0.5
            row["station_temps_degR"] = [scalar(self.prob, f"{point}.{station}:tot:T", "degR") for station in STATIONS]
            row["station_pressures_psi"] = [scalar(self.prob, f"{point}.{station}:tot:P", "psi") for station in STATIONS]
            row["station_machs"] = [scalar(self.prob, f"{point}.{station}:stat:MN") for station in STATIONS]
            rows.append(row)
        return rows

    def build_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        intro = QLabel(
            "Plots use converged solver values. Area-derived impeller diameter is an equivalent circular-flow-area estimate, "
            "not a mechanical blade-tip diameter."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        tabs = QTabWidget()
        layout.addWidget(tabs)
        tabs.addTab(self.make_pressure_temperature_plot(), "1. Pressure vs Temperature")
        tabs.addTab(self.make_t4_thrust_plot(), "2. T4 vs Thrust")
        tabs.addTab(self.make_t4_rpm_plot(), "3. T4 vs RPM")
        tabs.addTab(self.make_thrust_altitude_plot(), "4. Thrust vs Altitude")
        tabs.addTab(self.make_area_plot(), "5. Flow / Area / Diameter")
        tabs.addTab(self.make_station_plot(), "6. Stations / Altitude")

        export_button = QPushButton("Export analysis CSV")
        export_button.clicked.connect(self.export_csv)
        layout.addWidget(export_button)

    def canvas(self, figure):
        canvas = FigureCanvas(figure)
        canvas.setMinimumSize(850, 600)
        return canvas

    def figure(self, title):
        fig = Figure(layout="constrained")
        fig.suptitle(title, fontsize=14, fontweight="bold")
        return fig

    def make_pressure_temperature_plot(self):
        fig = self.figure("Total Pressure versus Total Temperature at Every Station")
        ax = fig.add_subplot(111)
        for index, label in enumerate(STATION_LABELS):
            ax.plot([r["station_temps_degR"][index] for r in self.rows],
                    [r["station_pressures_psi"][index] for r in self.rows], "o-", label=label)
        ax.set(xlabel="Total temperature (degR)", ylabel="Total pressure (psi)")
        ax.grid(True, alpha=.3)
        ax.legend(ncol=2)
        return self.canvas(fig)

    def make_t4_thrust_plot(self):
        fig = self.figure("Maximum Cycle Temperature (T4) versus Net Thrust")
        ax = fig.add_subplot(111)
        x = [r["thrust_lbf"] for r in self.rows]
        y = [r["t4_degR"] for r in self.rows]
        scatter = ax.scatter(x, y, c=[r["rpm"] for r in self.rows], cmap="viridis", s=70)
        ax.set(xlabel="Net thrust (lbf)", ylabel="T4 / burner-exit total temperature (degR)")
        ax.grid(True, alpha=.3)
        fig.colorbar(scatter, ax=ax, label="Shaft speed (rpm)")
        return self.canvas(fig)

    def make_t4_rpm_plot(self):
        fig = self.figure("Maximum Cycle Temperature (T4) versus Shaft Speed")
        ax = fig.add_subplot(111)
        ax.plot([r["rpm"] for r in self.rows], [r["t4_degR"] for r in self.rows], "o-", color="#bf4b17")
        ax.set(xlabel="Shaft speed, Nmech (rpm)", ylabel="T4 / burner-exit total temperature (degR)")
        ax.grid(True, alpha=.3)
        return self.canvas(fig)

    def make_thrust_altitude_plot(self):
        fig = self.figure("Net Thrust at the Evaluated Operating Altitudes")
        ax = fig.add_subplot(111)
        ax.plot([r["altitude_ft"] for r in self.rows], [r["thrust_lbf"] for r in self.rows], "o-", color="#1769aa")
        ax.set(xlabel="Altitude (ft)", ylabel="Net thrust (lbf)")
        ax.grid(True, alpha=.3)
        return self.canvas(fig)

    def make_area_plot(self):
        fig = self.figure("Mass Flow, Flow Areas, and Equivalent Compressor Diameter")
        ax1 = fig.add_subplot(111)
        x = [r["mass_flow_kg_s"] for r in self.rows]
        ax1.plot(x, [r["inlet_area_m2"] for r in self.rows], "o-", label="Inlet area")
        ax1.plot(x, [r["compressor_exit_area_m2"] for r in self.rows], "s-", label="Compressor outlet area")
        ax1.set(xlabel="Mass flow (kg/s)", ylabel="Flow area (m²)")
        ax1.grid(True, alpha=.3)
        ax2 = ax1.twinx()
        ax2.plot(x, [r["impeller_diameter_m"] for r in self.rows], "^-", color="#bf4b17", label="Equivalent outlet diameter")
        ax2.set_ylabel("Equivalent circular diameter (m)")
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc="best")
        return self.canvas(fig)

    def make_station_plot(self):
        fig = self.figure("Station Temperatures and Mach Number for Each Operating Altitude")
        ax_temp, ax_mach = fig.subplots(1, 2)
        station_x = range(len(STATIONS))
        for row in self.rows:
            label = f"{row['point']}: {row['altitude_ft']:.0f} ft"
            ax_temp.plot(station_x, row["station_temps_degR"], "o-", label=label)
            ax_mach.plot(station_x, row["station_machs"], "o-", label=label)
        for ax, ylabel in ((ax_temp, "Total temperature (degR)"), (ax_mach, "Static Mach number (-)")):
            ax.set_xticks(list(station_x), STATION_LABELS, rotation=35, ha="right")
            ax.set_ylabel(ylabel)
            ax.grid(True, alpha=.3)
        ax_temp.legend(fontsize=8)
        return self.canvas(fig)

    def export_csv(self):
        output_dir = Path(__file__).resolve().parent / "input_gui_out" / "analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / "turbojet_analysis.csv"
        fields = ["point", "altitude_ft", "freestream_mach", "rpm", "thrust_lbf", "mass_flow_kg_s",
                  "t4_degR", "inlet_area_m2", "compressor_exit_area_m2", "impeller_diameter_m"]
        with destination.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows({field: row[field] for field in fields} for row in self.rows)
        QMessageBox.information(self, "Analysis exported", f"Saved: {destination}")


class EngineWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.window = parent

        self.pix = QPixmap(str(Path(__file__).resolve().parent / "Turbojet_operation-centrifugal_flow-fr.png"))

        self.setMinimumSize(900, 350)

        # x,y coordinates of stations
        self.stations = {

            "fc.Fl_O": (90,175),

            "comp.Fl_O": (260,175),

            "burner.Fl_O": (430,175),

            "turb.Fl_O": (620,175),

            "nozz.Fl_O": (830,175)

        }
        self.selected = "fc.Fl_O"

    #####################################################

    def paintEvent(self, event):

        super().paintEvent(event)

        painter = QPainter(self)

        painter.drawPixmap(
            self.rect(),
            self.pix,
            self.pix.rect()
        )

        for i, (name, (x, y)) in enumerate(self.stations.items()):

            if name == self.selected:

                pen = QPen(QColor(0, 255, 0), 3)
                painter.setPen(pen)
                painter.setBrush(QColor(0, 255, 0))

            else:

                pen = QPen(QColor(255, 0, 0), 3)
                painter.setPen(pen)
                painter.setBrush(QColor(255, 255, 255))

            painter.drawEllipse(x - 10, y - 10, 20, 20)

            painter.drawText(x - 4, y + 4, str(i))

    #####################################################

    def mousePressEvent(self,event):



        x = event.position().x()
        y = event.position().y()

        for name, (cx, cy) in self.stations.items():

            if (x - cx) ** 2 + (y - cy) ** 2 <= 15 ** 2:
                self.selected = name  # remember the selected station

                self.update()  # redraw circles

                self.window.update_station(name)

                break

class EngineWindow(QMainWindow):

    def __init__(self,prob,od_pts):

        super().__init__()

        self.setWindowTitle("PyCycle Turbojet Viewer")

        self.resize(1650,950)

        self.prob = prob

        self.od_pts = od_pts

        self.current_pt = "DESIGN"

        self.build_ui()

        self.update_performance()

        self.update_station("fc.Fl_O")

    ###################################################

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        layout = QVBoxLayout()

        central.setLayout(layout)

        ##################################################

        top = QHBoxLayout()

        layout.addLayout(top)

        top.addWidget(QLabel("Design Point"))

        self.combo = QComboBox()

        self.combo.addItem("DESIGN")

        self.combo.addItems(self.od_pts)

        self.combo.currentTextChanged.connect(self.change_point)

        top.addWidget(self.combo)

        self.analysis_button = QPushButton("Open analysis & plots")
        self.analysis_button.clicked.connect(self.open_analysis)
        top.addWidget(self.analysis_button)

        top.addStretch()

        ##################################################

        middle = QHBoxLayout()

        layout.addLayout(middle)

        ##################################################

        self.engine = EngineWidget(self)

        middle.addWidget(self.engine)

        ##################################################



        ###################################################

        right = QVBoxLayout()

        middle.addLayout(right)

        ##################################################

        self.performance = QTableWidget()

        self.performance.setColumnCount(2)

        self.performance.setHorizontalHeaderLabels(
            ["Parameter","Value"]
        )

        right.addWidget(self.performance)

        ##################################################

        self.station = QTableWidget()

        self.station.setColumnCount(3)

        self.station.setHorizontalHeaderLabels(
            ["Property","Unit","Value"]
        )

        layout.addWidget(self.station)

        self.stationLabel = QLabel("Flow Station : Flight Conditions")

        font = self.stationLabel.font()
        font.setPointSize(12)
        font.setBold(True)

        self.stationLabel.setFont(font)

        layout.addWidget(self.stationLabel)
        layout.addWidget(self.station)
    ###################################################

    def change_point(self,text):

        self.current_pt=text

        self.update_performance()

        self.update_station("fc.Fl_O")

    def open_analysis(self):
        self.analysis = AnalysisWindow(self.prob, ["DESIGN"] + self.od_pts)
        self.analysis.show()

    ###################################################

    def update_performance(self):

        pt=self.current_pt

        data=[

            ("Mach",
             self.prob.get_val(f"{pt}.fc.Fl_O:stat:MN")),

            ("Altitude (ft)",
             self.prob.get_val(f"{pt}.fc.alt",units="ft")),

            ("Mass Flow (kg/s)",
             self.prob.get_val(f"{pt}.inlet.Fl_O:stat:W",units="kg/s")),

            ("Fn (kN)",
             self.prob.get_val(f"{pt}.perf.Fn",units="kN")),

            ("Fg (kN)",
             self.prob.get_val(f"{pt}.perf.Fg",units="kN")),

            ("Ram Drag (kN)",
             self.prob.get_val(f"{pt}.inlet.F_ram",units="kN")),

            ("OPR",
             self.prob.get_val(f"{pt}.perf.OPR")),

            ("TSFC",
             self.prob.get_val(f"{pt}.perf.TSFC",units="kg/N/s"))

        ]

        self.performance.setRowCount(len(data))

        for r,(a,b) in enumerate(data):

            self.performance.setItem(r,0,QTableWidgetItem(a))

            self.performance.setItem(r,1,QTableWidgetItem(str(float(b))))

    ###################################################

    def update_station(self,station):

        names = {

            "fc.Fl_O": "Flight Conditions",

            "comp.Fl_O": "Compressor Exit",

            "burner.Fl_O": "Burner Exit",

            "turb.Fl_O": "Turbine Exit",

            "nozz.Fl_O": "Nozzle Exit"

        }

        self.stationLabel.setText(
            f"Flow Station : {names[station]}"
        )

        pt=self.current_pt

        props=[

            ("Pt : Total Pressure","kPa","tot:P"),

            ("Tt : Total Temperature","K","tot:T"),

            ("ht : Total Enthalpy","kJ/kg","tot:h"),

            ("St : Total Entropy","J/kg/K","tot:S"),

            ("Ps : Static Pressure","kPa","stat:P"),

            ("Ts : Static Temperature","K","stat:T"),

            ("hs : Static Enthalpy","kJ/kg","stat:h"),

            ("Ss : Static Entropy","J/kg/K","stat:S"),

            ("Mach","-","stat:MN"),

            ("Velocity","m/s","stat:V"),

            ("Mass Flow","kg/s","stat:W")

        ]

        unit_options = {

            "tot:P": ["kPa", "bar", "atm"],

            "stat:P": ["kPa", "bar", "atm"],

            "tot:T": ["K", "degC", "degF"],

            "stat:T": ["K", "degC", "degF"],

            "stat:V": ["m/s", "km/h", "mph", "kn"],

        }

        self.station.setRowCount(len(props))

        for i, (name, unit, var) in enumerate(props):

            combo = QComboBox()

            if var in unit_options:

                combo.addItems(unit_options[var])

                combo.setCurrentText(unit)

            else:

                combo.addItem(unit)

                combo.setEnabled(False)

            self.station.setItem(i, 0, QTableWidgetItem(name))

            self.station.setCellWidget(i, 1, combo)

            value = self.get_station_value(station, var, combo.currentText())

            self.station.setItem(i, 2, QTableWidgetItem(f"{value:.3f}"))

            combo.currentTextChanged.connect(

                lambda _, r=i, s=station, v=var, c=combo:

                self.change_unit(r, s, v, c)

            )

##########################################################
    def get_station_value(self, station, var, unit):

        pt = self.current_pt

        if unit in ("-", "", None):
            value = self.prob.get_val(f"{pt}.{station}:{var}")
        else:
            value = self.prob.get_val(
                f"{pt}.{station}:{var}",
                units=unit
            )

        return float(value.item())

    def change_unit(self, row, station, var, combo):

        unit = combo.currentText()

        value = self.get_station_value(station, var, unit)

        self.station.setItem(

            row,

            2,

            QTableWidgetItem(f"{value:.3f}")

        )
if __name__ == "__main__":

    app = QApplication(sys.argv)

    QMessageBox.information(

        None,

        "Info",

        "Please launch this GUI from input_gui.py"

    )

    sys.exit(app.exec())
