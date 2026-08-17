#
# import csv
# import os
# import sys
# from pathlib import Path
#
# # Keep Matplotlib's cache with the project so it can run without needing to
# # write into the user's profile directory.
# os.environ["MPLCONFIGDIR"] = str(Path(__file__).resolve().parent / ".matplotlib")
#
# from PySide6.QtWidgets import *
#
# from PySide6.QtGui import *
#
# from PySide6.QtCore import *
#
# #from t3 import run_engine
#
# from PySide6.QtGui import QPainter, QColor, QPen
# from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
# import numpy as np
# from matplotlib.figure import Figure
#
#
# STATIONS = ["fc.Fl_O", "inlet.Fl_O", "comp.Fl_O", "burner.Fl_O", "turb.Fl_O", "nozz.Fl_O"]
# STATION_LABELS = ["Freestream", "Inlet", "Compressor", "Burner (T4)", "Turbine", "Nozzle"]
#
#
# def scalar(prob, name, units=None):
#     """Return an OpenMDAO value as a plain float."""
#     value = prob.get_val(name, units=units) if units else prob.get_val(name)
#     return float(value.item())
#
#
# class AnalysisWindow(QMainWindow):
#     """Plot and export the data produced by the most recent engine run."""
#
#     def __init__(self, prob, points):
#         super().__init__()
#
#         self.prob = prob
#         self.points = points
#         self.rows = self.collect_rows()
#
#         self.setWindowTitle("Turbojet Performance Analysis")
#         self.resize(1450, 920)
#
#         self.build_ui()
#
#     # ============================================================
#     # DATA COLLECTION
#     # ============================================================
#
#     def collect_rows(self):
#
#         rows = []
#
#         for point in self.points:
#
#             row = {
#                 "point": point,
#
#                 "altitude_ft":
#                     scalar(
#                         self.prob,
#                         f"{point}.fc.alt",
#                         "ft"
#                     ),
#
#                 "freestream_mach":
#                     scalar(
#                         self.prob,
#                         f"{point}.fc.Fl_O:stat:MN"
#                     ),
#
#                 "rpm":
#                     scalar(
#                         self.prob,
#                         f"{point}.Nmech",
#                         "rpm"
#                     ),
#
#                 "thrust_lbf":
#                     scalar(
#                         self.prob,
#                         f"{point}.perf.Fn",
#                         "lbf"
#                     ),
#
#                 "mass_flow_kg_s":
#                     scalar(
#                         self.prob,
#                         f"{point}.inlet.Fl_O:stat:W",
#                         "kg/s"
#                     ),
#
#                 "t4_degR":
#                     scalar(
#                         self.prob,
#                         f"{point}.burner.Fl_O:tot:T",
#                         "degR"
#                     ),
#
#                 "inlet_area_m2":
#                     scalar(
#                         self.prob,
#                         f"{point}.inlet.Fl_O:stat:area",
#                         "m**2"
#                     ),
#
#                 "compressor_exit_area_m2":
#                     scalar(
#                         self.prob,
#                         f"{point}.comp.Fl_O:stat:area",
#                         "m**2"
#                     ),
#             }
#
#             row["impeller_diameter_m"] = (
#                 4.0 *
#                 row["compressor_exit_area_m2"] /
#                 3.141592653589793
#             ) ** 0.5
#
#             row["station_temps_degR"] = [
#                 scalar(
#                     self.prob,
#                     f"{point}.{station}:tot:T",
#                     "degR"
#                 )
#                 for station in STATIONS
#             ]
#
#             row["station_pressures_psi"] = [
#                 scalar(
#                     self.prob,
#                     f"{point}.{station}:tot:P",
#                     "psi"
#                 )
#                 for station in STATIONS
#             ]
#
#             row["station_machs"] = [
#                 scalar(
#                     self.prob,
#                     f"{point}.{station}:stat:MN"
#                 )
#                 for station in STATIONS
#             ]
#
#             rows.append(row)
#
#         return rows
#
#     # ============================================================
#     # ORIGINAL ANALYSIS WINDOW UI
#     # ============================================================
#
#     def build_ui(self):
#
#         central = QWidget()
#         layout = QVBoxLayout(central)
#
#         self.setCentralWidget(central)
#
#         # Keep original window spacing/style
#         layout.setContentsMargins(10, 8, 10, 8)
#         layout.setSpacing(6)
#
#         # --------------------------------------------------------
#         # ORIGINAL INTRO TEXT
#         # --------------------------------------------------------
#
#         intro = QLabel(
#             "Plots use converged solver values. "
#             "Area-derived impeller diameter is an equivalent "
#             "circular-flow-area estimate, not a mechanical "
#             "blade-tip diameter."
#         )
#
#         intro.setWordWrap(True)
#
#         layout.addWidget(intro)
#
#         # --------------------------------------------------------
#         # TABS
#         # --------------------------------------------------------
#
#         tabs = QTabWidget()
#
#         layout.addWidget(tabs)
#
#         tabs.addTab(
#             self.make_pressure_temperature_plot(),
#             "1. Pressure vs Temperature"
#         )
#
#         tabs.addTab(
#             self.make_t4_thrust_plot(),
#             "2. T4 vs Thrust"
#         )
#
#         tabs.addTab(
#             self.make_t4_rpm_plot(),
#             "3. T4 vs RPM"
#         )
#
#         tabs.addTab(
#             self.make_thrust_altitude_plot(),
#             "4. Thrust vs Altitude"
#         )
#
#         tabs.addTab(
#             self.make_area_plot(),
#             "5. Flow / Area / Diameter"
#         )
#
#         tabs.addTab(
#             self.make_station_plot(),
#             "6. Stations / Altitude"
#         )
#
#         # --------------------------------------------------------
#         # EXPORT
#         # --------------------------------------------------------
#
#         export_button = QPushButton(
#             "Export analysis CSV"
#         )
#
#         export_button.clicked.connect(
#             self.export_csv
#         )
#
#         layout.addWidget(export_button)
#
#     # ============================================================
#     # MATPLOTLIB CANVAS + TOOLBAR + HOVER + SCROLL ZOOM
#     # ============================================================
#
#     def canvas(self, figure, hover_specs=None):
#
#         container = QWidget()
#
#         layout = QVBoxLayout(container)
#
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(0)
#
#         canvas = FigureCanvas(figure)
#
#         canvas.setMinimumSize(850, 600)
#
#         toolbar = NavigationToolbar2QT(
#             canvas,
#             container
#         )
#
#         layout.addWidget(toolbar)
#         layout.addWidget(canvas)
#
#         # Hover functionality
#         if hover_specs:
#
#             self.add_hover_annotations(
#                 canvas,
#                 hover_specs
#             )
#
#         return container
#
#     # ============================================================
#     # FIGURE
#     # ============================================================
#
#     @staticmethod
#     def figure(title):
#
#         # IMPORTANT:
#         # Do NOT use layout="constrained" here.
#         # The hover annotation can cause constrained_layout
#         # to resize/reposition the graph while hovering.
#
#         fig = Figure()
#
#         fig.subplots_adjust(
#             left=0.07,
#             right=0.98,
#             bottom=0.12,
#             top=0.90
#         )
#
#         fig.suptitle(
#             title,
#             fontsize=14,
#             fontweight="bold"
#         )
#
#         return fig
#
#     # ============================================================
#     # UNIT CONVERSIONS
#     # ============================================================
#
#     @staticmethod
#     def c_to_kpa_pressure(pressure_psi):
#
#         return pressure_psi * 6.894757293168
#
#     @staticmethod
#     def degr_to_c(temp_degR):
#
#         return temp_degR / 1.8 - 273.15
#
#     @staticmethod
#     def lbf_to_kn(thrust_lbf):
#
#         return thrust_lbf * 0.0044482216152605
#
#     # ============================================================
#     # HOVER ANNOTATIONS
#     # ============================================================
#
#     def add_hover_annotations(
#         self,
#         canvas,
#         hover_specs
#     ):
#         """
#         Add hover information to plotted data points.
#
#         hover_specs:
#             [
#                 {
#                     "artist": matplotlib artist,
#                     "texts": [text for each point]
#                 }
#             ]
#         """
#
#         annotations = {}
#
#         # One annotation per axis
#         for spec in hover_specs:
#
#             ax = spec["artist"].axes
#
#             if ax not in annotations:
#
#                 annotation = ax.annotate(
#                     "",
#                     xy=(0, 0),
#                     xytext=(12, 12),
#                     textcoords="offset points",
#
#                     bbox=dict(
#                         boxstyle="round,pad=0.4",
#                         fc="white",
#                         ec="0.35",
#                         alpha=0.92
#                     ),
#
#                     arrowprops=dict(
#                         arrowstyle="->",
#                         color="0.35"
#                     )
#                 )
#
#                 annotation.set_visible(False)
#
#                 annotations[ax] = annotation
#
#         # --------------------------------------------------------
#         # MOUSE MOVE
#         # --------------------------------------------------------
#
#         def on_move(event):
#
#             if event.inaxes is None:
#
#                 changed = False
#
#                 for annotation in annotations.values():
#
#                     if annotation.get_visible():
#
#                         annotation.set_visible(False)
#                         changed = True
#
#                 if changed:
#                     canvas.draw_idle()
#
#                 return
#
#             visible_annotation = annotations.get(
#                 event.inaxes
#             )
#
#             if visible_annotation is None:
#                 return
#
#             found = False
#
#             for spec in hover_specs:
#
#                 artist = spec["artist"]
#
#                 if artist.axes is not event.inaxes:
#                     continue
#
#                 contains, info = artist.contains(event)
#
#                 if not contains:
#                     continue
#
#                 indices = info.get("ind", [])
#
#                 if len(indices) == 0:
#                     continue
#
#                 index = int(indices[0])
#
#                 texts = spec["texts"]
#
#                 if index >= len(texts):
#                     continue
#
#                 # Scatter
#                 if hasattr(
#                     artist,
#                     "get_offsets"
#                 ):
#
#                     xy = artist.get_offsets()[index]
#
#                 # Line
#                 else:
#
#                     xy = (
#                         artist.get_xdata()[index],
#                         artist.get_ydata()[index]
#                     )
#
#                 visible_annotation.xy = (
#                     float(xy[0]),
#                     float(xy[1])
#                 )
#
#                 visible_annotation.set_text(
#                     texts[index]
#                 )
#
#                 visible_annotation.set_visible(
#                     True
#                 )
#
#                 found = True
#
#                 break
#
#             if not found:
#
#                 if visible_annotation.get_visible():
#
#                     visible_annotation.set_visible(
#                         False
#                     )
#
#             canvas.draw_idle()
#
#         canvas.mpl_connect(
#             "motion_notify_event",
#             on_move
#         )
#
#         # --------------------------------------------------------
#         # MOUSE WHEEL ZOOM
#         # --------------------------------------------------------
#
#         def on_scroll(event):
#
#             if event.inaxes is None:
#                 return
#
#             ax = event.inaxes
#
#             # Scroll UP = zoom IN
#             if event.button == "up":
#
#                 scale = 0.8
#
#             # Scroll DOWN = zoom OUT
#             elif event.button == "down":
#
#                 scale = 1.25
#
#             else:
#
#                 return
#
#             # Current limits
#             x_left, x_right = ax.get_xlim()
#             y_bottom, y_top = ax.get_ylim()
#
#             # Mouse location in data coordinates
#             x_mouse = event.xdata
#             y_mouse = event.ydata
#
#             if (
#                 x_mouse is None
#                 or y_mouse is None
#             ):
#                 return
#
#             # Zoom around mouse position
#             ax.set_xlim(
#                 x_mouse -
#                 (x_mouse - x_left) * scale,
#
#                 x_mouse +
#                 (x_right - x_mouse) * scale
#             )
#
#             ax.set_ylim(
#                 y_mouse -
#                 (y_mouse - y_bottom) * scale,
#
#                 y_mouse +
#                 (y_top - y_mouse) * scale
#             )
#
#             canvas.draw_idle()
#
#         canvas.mpl_connect(
#             "scroll_event",
#             on_scroll
#         )
#
#         return canvas
#
#     # ============================================================
#     # 1. PRESSURE vs TEMPERATURE
#     # ============================================================
#
#     def make_pressure_temperature_plot(self):
#
#         fig = self.figure(
#             "Total Pressure versus Total Temperature at Every Station"
#         )
#
#         ax = fig.add_subplot(111)
#
#         hover_specs = []
#
#         for index, label in enumerate(STATION_LABELS):
#
#             # Convert native pyCycle values
#             # degR -> °C
#             # psi  -> kPa
#
#             # X = Total Pressure (kPa)
#             x = np.array([
#                 self.c_to_kpa_pressure(
#                     r["station_pressures_psi"][index]
#                 )
#                 for r in self.rows
#             ])
#
#             # Y = Total Temperature (°C)
#             y = np.array([
#                 self.degr_to_c(
#                     r["station_temps_degR"][index]
#                 )
#                 for r in self.rows
#             ])
#
#             # Sort for clean connecting line
#             order = np.argsort(x)
#
#             xs = x[order]
#             ys = y[order]
#
#             line, = ax.plot(
#                 xs,
#                 ys,
#                 "o-",
#                 label=label,
#                 linewidth=1.6,
#                 markersize=5
#             )
#
#             hover_specs.append({
#                 "artist": line,
#
#                 "texts": [
#                     f"{label}\n"
#                     f"Altitude: "
#                     f"{self.rows[int(order[i])]['altitude_ft']:.0f} ft\n"
#                     f"Tt: {xs[i]:.2f} °C\n"
#                     f"Pt: {ys[i]:.2f} kPa"
#
#                     for i in range(len(xs))
#                 ]
#             })
#
#             # Trend line
#             if (
#                 len(xs) >= 2
#                 and np.ptp(xs) > 1e-12
#             ):
#
#                 slope, intercept = np.polyfit(
#                     xs,
#                     ys,
#                     1
#                 )
#
#                 margin = max(
#                     np.ptp(xs) * 0.08,
#                     1.0
#                 )
#
#                 trend_x = np.linspace(
#                     xs.min() - margin,
#                     xs.max() + margin,
#                     100
#                 )
#
#                 trend_y = (
#                     slope * trend_x
#                     + intercept
#                 )
#
#                 ax.plot(
#                     trend_x,
#                     trend_y,
#                     "--",
#                     linewidth=1.1,
#                     alpha=0.55
#                 )
#
#         ax.set(
#             xlabel="Total pressure (kPa)",
#             ylabel="Total temperature (°C)"
#         )
#         ax.set_xlim(0, 1000)
#         ax.grid(True, alpha=0.3)
#
#         ax.margins(
#             x=0.08,
#             y=0.08
#         )
#
#         ax.legend(
#             ncol=2
#         )
#
#         return self.canvas(
#             fig,
#             hover_specs
#         )
#
#     # ============================================================
#     # 2. T4 vs THRUST
#     # ============================================================
#
#     def make_t4_thrust_plot(self):
#
#         fig = self.figure(
#             "Maximum Cycle Temperature (T4) versus Net Thrust"
#         )
#
#         ax = fig.add_subplot(111)
#
#         x = np.array([
#             self.lbf_to_kn(
#                 r["thrust_lbf"]
#             )
#             for r in self.rows
#         ])
#
#         y = np.array([
#             self.degr_to_c(
#                 r["t4_degR"]
#             )
#             for r in self.rows
#         ])
#
#         # Keep the original plot style:
#         # scatter + RPM colour coding
#
#         scatter = ax.scatter(
#             x,
#             y,
#             c=[
#                 r["rpm"]
#                 for r in self.rows
#             ],
#             cmap="viridis",
#             s=70
#         )
#
#         hover_specs = [{
#             "artist": scatter,
#
#             "texts": [
#                 f"Altitude: {r['altitude_ft']:.0f} ft\n"
#                 f"T4: {self.degr_to_c(r['t4_degR']):.2f} °C\n"
#                 f"Net thrust: "
#                 f"{self.lbf_to_kn(r['thrust_lbf']):.3f} kN\n"
#                 f"Shaft speed: {r['rpm']:.0f} rpm"
#
#                 for r in self.rows
#             ]
#         }]
#
#         ax.set(
#             xlabel="Net thrust (kN)",
#             ylabel=(
#                 "T4 / burner-exit "
#                 "total temperature (°C)"
#             )
#         )
#
#         ax.grid(True, alpha=0.3)
#
#         ax.margins(
#             x=0.08,
#             y=0.08
#         )
#
#         fig.colorbar(
#             scatter,
#             ax=ax,
#             label="Shaft speed (rpm)"
#         )
#
#         return self.canvas(
#             fig,
#             hover_specs
#         )
#
#     # ============================================================
#     # 3. T4 vs RPM
#     # ============================================================
#
#     def make_t4_rpm_plot(self):
#
#         fig = self.figure(
#             "Maximum Cycle Temperature (T4) versus Shaft Speed"
#         )
#
#         ax = fig.add_subplot(111)
#
#         x = np.array([
#             r["rpm"]
#             for r in self.rows
#         ])
#
#         y = np.array([
#             self.degr_to_c(
#                 r["t4_degR"]
#             )
#             for r in self.rows
#         ])
#
#         line, = ax.plot(
#             x,
#             y,
#             "o-",
#             color="#bf4b17",
#             linewidth=1.6,
#             markersize=5
#         )
#
#         hover_specs = [{
#             "artist": line,
#
#             "texts": [
#                 f"Altitude: {r['altitude_ft']:.0f} ft\n"
#                 f"Shaft speed: {r['rpm']:.0f} rpm\n"
#                 f"T4: {self.degr_to_c(r['t4_degR']):.2f} °C\n"
#                 f"Net thrust: "
#                 f"{self.lbf_to_kn(r['thrust_lbf']):.3f} kN"
#
#                 for r in self.rows
#             ]
#         }]
#
#         ax.set(
#             xlabel="Shaft speed, Nmech (rpm)",
#             ylabel=(
#                 "T4 / burner-exit "
#                 "total temperature (°C)"
#             )
#         )
#
#         ax.grid(True, alpha=0.3)
#
#         ax.margins(
#             x=0.08,
#             y=0.08
#         )
#
#         return self.canvas(
#             fig,
#             hover_specs
#         )
#
#     # ============================================================
#     # 4. THRUST vs ALTITUDE
#     # ============================================================
#
#     def make_thrust_altitude_plot(self):
#
#         fig = self.figure(
#             "Net Thrust at the Evaluated Operating Altitudes"
#         )
#
#         ax = fig.add_subplot(111)
#
#         x = np.array([
#             r["altitude_ft"]
#             for r in self.rows
#         ])
#
#         y = np.array([
#             self.lbf_to_kn(r["thrust_lbf"])
#             for r in self.rows
#         ])
#
#         line, = ax.plot(
#             x,
#             y,
#             "o-",
#             color="#1769aa",
#             linewidth=1.6,
#             markersize=5
#         )
#
#         hover_specs = [{
#             "artist": line,
#
#             "texts": [
#                 f"Altitude: "
#                 f"{r['altitude_ft']:.0f} ft\n"
#                 f"Net thrust: "
#                 f"{self.lbf_to_kn(r['thrust_lbf']):.3f} kN\n"
#                 f"T4: "
#                 f"{self.degr_to_c(r['t4_degR']):.2f} °C\n"
#                 f"Shaft speed: "
#                 f"{r['rpm']:.0f} rpm"
#
#                 for r in self.rows
#             ]
#         }]
#
#         ax.set(
#             xlabel="Altitude (ft)",
#             ylabel="Net thrust (kN)"
#         )
#         ax.grid(True, alpha=0.3)
#
#         ax.margins(
#             x=0.08,
#             y=0.08
#         )
#
#         return self.canvas(
#             fig,
#             hover_specs
#         )
#
#     # ============================================================
#     # 5. MASS FLOW / AREA / DIAMETER
#     # ============================================================
#
#     def make_area_plot(self):
#
#         fig = self.figure(
#             "Mass Flow, Flow Areas, and Equivalent Compressor Diameter"
#         )
#
#         ax1 = fig.add_subplot(111)
#
#         x = np.array([
#             r["mass_flow_kg_s"]
#             for r in self.rows
#         ])
#
#         y_inlet = np.array([
#             r["inlet_area_m2"]
#             for r in self.rows
#         ])
#
#         y_comp = np.array([
#             r["compressor_exit_area_m2"]
#             for r in self.rows
#         ])
#
#         y_diam = np.array([
#             r["impeller_diameter_m"]
#             for r in self.rows
#         ])
#
#         line1, = ax1.plot(
#             x,
#             y_inlet,
#             "o-",
#             label="Inlet area"
#         )
#
#         line2, = ax1.plot(
#             x,
#             y_comp,
#             "s-",
#             label="Compressor outlet area"
#         )
#
#         ax1.set(
#             xlabel="Mass flow (kg/s)",
#             ylabel="Flow area (m²)"
#         )
#
#         ax1.grid(True, alpha=0.3)
#
#         ax1.margins(
#             x=0.08,
#             y=0.08
#         )
#
#         ax2 = ax1.twinx()
#
#         line3, = ax2.plot(
#             x,
#             y_diam,
#             "^-",
#             color="#bf4b17",
#             label="Equivalent outlet diameter"
#         )
#
#         ax2.set_ylabel(
#             "Equivalent circular diameter (m)"
#         )
#
#         hover_specs = [
#
#             {
#                 "artist": line1,
#
#                 "texts": [
#                     f"Mass flow: "
#                     f"{r['mass_flow_kg_s']:.4f} kg/s\n"
#                     f"Inlet area: "
#                     f"{r['inlet_area_m2']:.5f} m²\n"
#                     f"Altitude: "
#                     f"{r['altitude_ft']:.0f} ft"
#
#                     for r in self.rows
#                 ]
#             },
#
#             {
#                 "artist": line2,
#
#                 "texts": [
#                     f"Mass flow: "
#                     f"{r['mass_flow_kg_s']:.4f} kg/s\n"
#                     f"Compressor outlet area: "
#                     f"{r['compressor_exit_area_m2']:.5f} m²\n"
#                     f"Altitude: "
#                     f"{r['altitude_ft']:.0f} ft"
#
#                     for r in self.rows
#                 ]
#             },
#
#             {
#                 "artist": line3,
#
#                 "texts": [
#                     f"Mass flow: "
#                     f"{r['mass_flow_kg_s']:.4f} kg/s\n"
#                     f"Equivalent diameter: "
#                     f"{r['impeller_diameter_m']:.5f} m\n"
#                     f"Altitude: "
#                     f"{r['altitude_ft']:.0f} ft"
#
#                     for r in self.rows
#                 ]
#             }
#         ]
#
#         lines1, labels1 = (
#             ax1.get_legend_handles_labels()
#         )
#
#         lines2, labels2 = (
#             ax2.get_legend_handles_labels()
#         )
#
#         ax1.legend(
#             lines1 + lines2,
#             labels1 + labels2,
#             loc="best"
#         )
#
#         return self.canvas(
#             fig,
#             hover_specs
#         )
#
#     # ============================================================
#     # 6. STATION ANALYSIS
#     # ============================================================
#
#     def make_station_plot(self):
#
#         fig = self.figure(
#             "Station Temperatures and Mach Number for Each Operating Altitude"
#         )
#
#         ax_temp, ax_mach = fig.subplots(
#             1,
#             2
#         )
#
#         station_x = np.arange(
#             len(STATIONS)
#         )
#
#         hover_specs = []
#
#         for row in self.rows:
#
#             label = (
#                 f"{row['point']}: "
#                 f"{row['altitude_ft']:.0f} ft"
#             )
#
#             temp_c = [
#                 self.degr_to_c(value)
#                 for value in row[
#                     "station_temps_degR"
#                 ]
#             ]
#
#             temp_line, = ax_temp.plot(
#                 station_x,
#                 temp_c,
#                 "o-",
#                 label=label
#             )
#
#             mach_line, = ax_mach.plot(
#                 station_x,
#                 row["station_machs"],
#                 "o-",
#                 label=label
#             )
#
#             # Temperature hover
#             hover_specs.append({
#
#                 "artist": temp_line,
#
#                 "texts": [
#                     f"{STATION_LABELS[i]}\n"
#                     f"Altitude: "
#                     f"{row['altitude_ft']:.0f} ft\n"
#                     f"Total temperature: "
#                     f"{temp_c[i]:.2f} °C\n"
#                     f"Mach: "
#                     f"{row['station_machs'][i]:.3f}"
#
#                     for i in range(len(STATIONS))
#                 ]
#             })
#
#             # Mach hover
#             hover_specs.append({
#
#                 "artist": mach_line,
#
#                 "texts": [
#                     f"{STATION_LABELS[i]}\n"
#                     f"Altitude: "
#                     f"{row['altitude_ft']:.0f} ft\n"
#                     f"Total temperature: "
#                     f"{temp_c[i]:.2f} °C\n"
#                     f"Mach: "
#                     f"{row['station_machs'][i]:.3f}"
#
#                     for i in range(len(STATIONS))
#                 ]
#             })
#
#         for ax, ylabel in (
#
#             (
#                 ax_temp,
#                 "Total temperature (°C)"
#             ),
#
#             (
#                 ax_mach,
#                 "Static Mach number (-)"
#             )
#
#         ):
#
#             ax.set_xticks(
#                 list(station_x),
#                 STATION_LABELS,
#                 rotation=35,
#                 ha="right"
#             )
#
#             ax.set_ylabel(
#                 ylabel
#             )
#
#             ax.grid(
#                 True,
#                 alpha=0.3
#             )
#
#             ax.margins(
#                 x=0.08,
#                 y=0.08
#             )
#
#         ax_temp.legend(
#             fontsize=8
#         )
#
#         return self.canvas(
#             fig,
#             hover_specs
#         )
#
#     # ============================================================
#     # CSV EXPORT
#     # ============================================================
#
#     def export_csv(self):
#
#         output_dir = (
#             Path(__file__).resolve().parent
#             / "input_gui_out"
#             / "analysis"
#         )
#
#         output_dir.mkdir(
#             parents=True,
#             exist_ok=True
#         )
#
#         destination = (
#             output_dir
#             / "turbojet_analysis.csv"
#         )
#
#         fields = [
#             "point",
#             "altitude_ft",
#             "freestream_mach",
#             "rpm",
#             "thrust_lbf",
#             "mass_flow_kg_s",
#             "t4_degR",
#             "inlet_area_m2",
#             "compressor_exit_area_m2",
#             "impeller_diameter_m"
#         ]
#
#         with destination.open(
#             "w",
#             newline="",
#             encoding="utf-8"
#         ) as file:
#
#             writer = csv.DictWriter(
#                 file,
#                 fieldnames=fields
#             )
#
#             writer.writeheader()
#
#             writer.writerows(
#                 {
#                     field: row[field]
#                     for field in fields
#                 }
#                 for row in self.rows
#             )
#
#         QMessageBox.information(
#             self,
#             "Analysis exported",
#             f"Saved: {destination}"
#         )
#
# class EngineWidget(QWidget):
#
#     def __init__(self, parent=None):
#
#         super().__init__(parent)
#
#         self.window = parent
#
#         self.pix = QPixmap(str(Path(__file__).resolve().parent / "Turbojet_operation-centrifugal_flow-fr.png"))
#
#         self.setFixedSize(900, 350)
#
#         # x,y coordinates of stations
#         self.stations = {
#
#             "fc.Fl_O": (90,175),
#
#             "comp.Fl_O": (260,175),
#
#             "burner.Fl_O": (430,175),
#
#             "turb.Fl_O": (620,175),
#
#             "nozz.Fl_O": (830,175)
#
#         }
#         self.selected = "fc.Fl_O"
#
#     #####################################################
#
#     def paintEvent(self, event):
#
#         super().paintEvent(event)
#
#         painter = QPainter(self)
#
#         # Stretch image horizontally only
#         scaled_width = int(self.width() * 0.95)
#         scaled_height = int(self.pix.height() * 0.40)
#
#         x = 0
#         y = (self.height() - scaled_height) // 2
#
#         target_rect = QRect(
#             x,
#             y,
#             scaled_width,
#             scaled_height
#         )
#
#         painter.drawPixmap(
#             target_rect,
#             self.pix,
#             self.pix.rect()
#         )
#
#         for i, (name, (x, y)) in enumerate(self.stations.items()):
#
#             if name == self.selected:
#
#                 pen = QPen(QColor(0, 255, 0), 3)
#                 painter.setPen(pen)
#                 painter.setBrush(QColor(0, 255, 0))
#
#             else:
#
#                 pen = QPen(QColor(255, 0, 0), 3)
#                 painter.setPen(pen)
#                 painter.setBrush(QColor(255, 255, 255))
#
#             painter.drawEllipse(x - 10, y - 10, 20, 20)
#
#             painter.drawText(x - 4, y + 4, str(i))
#
#     #####################################################
#
#     def mousePressEvent(self,event):
#
#
#
#         x = event.position().x()
#         y = event.position().y()
#
#         for name, (cx, cy) in self.stations.items():
#
#             if (x - cx) ** 2 + (y - cy) ** 2 <= 15 ** 2:
#                 self.selected = name  # remember the selected station
#
#                 self.update()  # redraw circles
#
#                 self.window.update_station(name)
#
#                 break
#
# class EngineWindow(QMainWindow):
#
#     def __init__(self,prob,od_pts):
#
#         super().__init__()
#
#         self.setWindowTitle("PyCycle Turbojet Viewer")
#
#         self.showMaximized()
#
#         self.prob = prob
#
#         self.od_pts = od_pts
#
#         self.current_pt = "DESIGN"
#
#         self.build_ui()
#
#         self.update_performance()
#
#         self.update_station("fc.Fl_O")
#
#     ###################################################
#
#     def build_ui(self):
#
#         central = QWidget()
#         self.setCentralWidget(central)
#
#         layout = QVBoxLayout(central)
#         layout.setContentsMargins(10, 8, 10, 8)
#         layout.setSpacing(6)
#
#         # ==========================================================
#         # HEADER
#         # ==========================================================
#
#         title = QLabel("OUTPUT WINDOW")
#
#         font = title.font()
#         font.setPointSize(15)
#         font.setBold(True)
#         title.setFont(font)
#
#         layout.addWidget(title)
#
#         # ==========================================================
#         # UPPER SECTION
#         # ENGINE DIAGRAM + PERFORMANCE TABLE
#         # ==========================================================
#
#         middle = QHBoxLayout()
#         middle.setSpacing(10)
#
#         layout.addLayout(middle, stretch=1)
#
#         # ---------------- ENGINE DIAGRAM ----------------
#
#         self.engine = EngineWidget(self)
#
#         middle.addWidget(self.engine)
#
#         # ---------------- PERFORMANCE TABLE ----------------
#
#         self.performance = QTableWidget()
#
#         self.performance.setColumnCount(2)
#
#         self.performance.setHorizontalHeaderLabels(
#             ["Parameter", "Value"]
#         )
#
#         self.performance.setSizePolicy(
#             QSizePolicy.Expanding,
#             QSizePolicy.Fixed
#         )
#
#         self.performance.setFixedHeight(350)
#
#         performance_header = self.performance.horizontalHeader()
#
#         performance_header.setSectionResizeMode(
#             0, QHeaderView.Stretch
#         )
#
#         performance_header.setSectionResizeMode(
#             1, QHeaderView.Stretch
#         )
#
#         middle.addWidget(
#             self.performance,
#             stretch=5
#         )
#
#         # ==========================================================
#         # LOWER SECTION
#         # FLOW STATION + OPERATING POINT CONTROLS
#         # ==========================================================
#
#         bottom = QHBoxLayout()
#         bottom.setSpacing(15)
#
#         layout.addLayout(bottom)
#
#         # ==========================================================
#         # LEFT — FLOW STATION TABLE
#         # ==========================================================
#
#         station_left = QVBoxLayout()
#         station_left.setSpacing(4)
#
#         self.stationLabel = QLabel(
#             "Flow Station : Flight Conditions"
#         )
#
#         font = self.stationLabel.font()
#         font.setPointSize(12)
#         font.setBold(True)
#         self.stationLabel.setFont(font)
#
#         station_left.addWidget(self.stationLabel)
#
#         self.station = QTableWidget()
#
#         self.station.setVerticalScrollBarPolicy(
#             Qt.ScrollBarAlwaysOff
#         )
#
#         self.station.setHorizontalScrollBarPolicy(
#             Qt.ScrollBarAlwaysOff
#         )
#
#         self.station.verticalHeader().setDefaultSectionSize(30)
#
#         # 11 rows + header
#         self.station.setFixedHeight(365)
#
#         self.station.setColumnCount(3)
#
#         self.station.setHorizontalHeaderLabels(
#             ["Property", "Unit", "Value"]
#         )
#
#         self.station.setSizePolicy(
#             QSizePolicy.Expanding,
#             QSizePolicy.Fixed
#         )
#
#         station_header = self.station.horizontalHeader()
#
#         # Property
#         station_header.setSectionResizeMode(
#             0, QHeaderView.Stretch
#         )
#
#         # Unit
#         station_header.setSectionResizeMode(
#             1, QHeaderView.Fixed
#         )
#         station_header.resizeSection(1, 190)
#
#         # Value
#         station_header.setSectionResizeMode(
#             2, QHeaderView.Stretch
#         )
#
#         station_left.addWidget(self.station)
#
#         # Green area
#         bottom.addLayout(
#             station_left,
#             stretch=7
#         )
#
#         # ==========================================================
#         # RIGHT — OPERATING POINT CONTROLS
#         # ==========================================================
#
#         controls = QVBoxLayout()
#         controls.setSpacing(10)
#
#         operating_label = QLabel(
#             "Operating Point"
#         )
#
#         font = operating_label.font()
#         font.setPointSize(19)
#         font.setBold(True)
#         operating_label.setFont(font)
#
#         controls.addWidget(
#             operating_label
#         )
#
#         # Design / Off-Design selector
#         self.combo = QComboBox()
#
#         self.combo.addItem("DESIGN")
#         self.combo.addItems(self.od_pts)
#
#         self.combo.setMinimumWidth(250)
#         self.combo.setMinimumHeight(45)
#
#         self.combo.currentTextChanged.connect(
#             self.change_point
#         )
#
#         controls.addWidget(
#             self.combo
#         )
#
#         # Analysis button
#         self.analysis_button = QPushButton(
#             "Open Analysis Plots"
#         )
#
#         self.analysis_button.setMinimumWidth(250)
#         self.analysis_button.setMinimumHeight(45)
#
#         self.analysis_button.clicked.connect(
#             self.open_analysis
#         )
#
#         controls.addWidget(
#             self.analysis_button
#         )
#
#         # Keep controls toward the top of the red region
#         controls.addStretch()
#
#         # Red area
#         bottom.addLayout(
#             controls,
#             stretch=3
#         )
#     ###################################################
#
#     def change_point(self,text):
#
#         self.current_pt=text
#
#         self.update_performance()
#
#         self.update_station("fc.Fl_O")
#
#     def open_analysis(self):
#         try:
#             points = ["DESIGN"] + list(self.od_pts)
#
#             self.analysis = AnalysisWindow(self.prob, points)
#
#             self.analysis.setWindowFlags(Qt.Window)
#             self.analysis.showMaximized()
#             self.analysis.raise_()
#             self.analysis.activateWindow()
#
#         except Exception as error:
#             print("ANALYSIS WINDOW ERROR:", repr(error))
#             QMessageBox.critical(
#                 self,
#                 "Analysis Error",
#                 f"Could not open Analysis Plots:\n\n{error}"
#             )
#     ###################################################
#
#     def update_performance(self):
#
#         pt=self.current_pt
#
#         data=[
#
#             ("Mach",
#              self.prob.get_val(f"{pt}.fc.Fl_O:stat:MN")),
#
#             ("Altitude (ft)",
#              self.prob.get_val(f"{pt}.fc.alt",units="ft")),
#
#             ("Mass Flow (kg/s)",
#              self.prob.get_val(f"{pt}.inlet.Fl_O:stat:W",units="kg/s")),
#
#             ("Fn (kN)",
#              self.prob.get_val(f"{pt}.perf.Fn",units="kN")),
#
#             ("Fg (kN)",
#              self.prob.get_val(f"{pt}.perf.Fg",units="kN")),
#
#             ("Ram Drag (kN)",
#              self.prob.get_val(f"{pt}.inlet.F_ram",units="kN")),
#
#             ("OPR",
#              self.prob.get_val(f"{pt}.perf.OPR")),
#
#             ("TSFC",
#              self.prob.get_val(f"{pt}.perf.TSFC",units="kg/N/s"))
#
#         ]
#
#         self.performance.setRowCount(len(data))
#
#         for r,(a,b) in enumerate(data):
#
#             self.performance.setItem(r,0,QTableWidgetItem(a))
#
#             self.performance.setItem(r,1,QTableWidgetItem(str(float(b))))
#
#     ###################################################
#
#     def update_station(self,station):
#
#         names = {
#
#             "fc.Fl_O": "Flight Conditions",
#
#             "comp.Fl_O": "Compressor Exit",
#
#             "burner.Fl_O": "Burner Exit",
#
#             "turb.Fl_O": "Turbine Exit",
#
#             "nozz.Fl_O": "Nozzle Exit"
#
#         }
#
#         self.stationLabel.setText(
#             f"Flow Station : {names[station]}"
#         )
#
#         pt=self.current_pt
#
#         props=[
#
#             ("Pt : Total Pressure","kPa","tot:P"),
#
#             ("Tt : Total Temperature","K","tot:T"),
#
#             ("ht : Total Enthalpy","kJ/kg","tot:h"),
#
#             ("St : Total Entropy","J/kg/K","tot:S"),
#
#             ("Ps : Static Pressure","kPa","stat:P"),
#
#             ("Ts : Static Temperature","K","stat:T"),
#
#             ("hs : Static Enthalpy","kJ/kg","stat:h"),
#
#             ("Ss : Static Entropy","J/kg/K","stat:S"),
#
#             ("Mach","-","stat:MN"),
#
#             ("Velocity","m/s","stat:V"),
#
#             ("Mass Flow","kg/s","stat:W")
#
#         ]
#
#         unit_options = {
#
#             "tot:P": ["kPa", "bar", "atm"],
#
#             "stat:P": ["kPa", "bar", "atm"],
#
#             "tot:T": ["K", "degC", "degF"],
#
#             "stat:T": ["K", "degC", "degF"],
#
#             "stat:V": ["m/s", "km/h", "mph", "kn"],
#
#         }
#
#         self.station.setRowCount(len(props))
#
#         for i, (name, unit, var) in enumerate(props):
#
#             combo = QComboBox()
#
#             if var in unit_options:
#
#                 combo.addItems(unit_options[var])
#
#                 combo.setCurrentText(unit)
#
#             else:
#
#                 combo.addItem(unit)
#
#                 combo.setEnabled(False)
#
#             self.station.setItem(i, 0, QTableWidgetItem(name))
#
#             self.station.setCellWidget(i, 1, combo)
#
#             value = self.get_station_value(station, var, combo.currentText())
#
#             self.station.setItem(i, 2, QTableWidgetItem(f"{value:.3f}"))
#
#             combo.currentTextChanged.connect(
#
#                 lambda _, r=i, s=station, v=var, c=combo:
#
#                 self.change_unit(r, s, v, c)
#
#             )
#
# ##########################################################
#     def get_station_value(self, station, var, unit):
#
#         pt = self.current_pt
#
#         if unit in ("-", "", None):
#             value = self.prob.get_val(f"{pt}.{station}:{var}")
#         else:
#             value = self.prob.get_val(
#                 f"{pt}.{station}:{var}",
#                 units=unit
#             )
#
#         return float(value.item())
#
#     def change_unit(self, row, station, var, combo):
#
#         unit = combo.currentText()
#
#         value = self.get_station_value(station, var, unit)
#
#         self.station.setItem(
#
#             row,
#
#             2,
#
#             QTableWidgetItem(f"{value:.3f}")
#
#         )
# if __name__ == "__main__":
#
#     app = QApplication(sys.argv)
#
#     QMessageBox.information(
#
#         None,
#
#         "Info",
#
#         "Please launch this GUI from input_gui.py"
#
#     )
#
#     sys.exit(app.exec())



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
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
import numpy as np
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

    # ============================================================
    # DATA COLLECTION
    # ============================================================

    def collect_rows(self):

        rows = []

        for point in self.points:

            row = {
                "point": point,

                "altitude_ft":
                    scalar(
                        self.prob,
                        f"{point}.fc.alt",
                        "ft"
                    ),

                "freestream_mach":
                    scalar(
                        self.prob,
                        f"{point}.fc.Fl_O:stat:MN"
                    ),

                "rpm":
                    scalar(
                        self.prob,
                        f"{point}.Nmech",
                        "rpm"
                    ),

                "thrust_lbf":
                    scalar(
                        self.prob,
                        f"{point}.perf.Fn",
                        "lbf"
                    ),

                "mass_flow_kg_s":
                    scalar(
                        self.prob,
                        f"{point}.inlet.Fl_O:stat:W",
                        "kg/s"
                    ),

                "t4_degR":
                    scalar(
                        self.prob,
                        f"{point}.burner.Fl_O:tot:T",
                        "degR"
                    ),

                "inlet_area_m2":
                    scalar(
                        self.prob,
                        f"{point}.inlet.Fl_O:stat:area",
                        "m**2"
                    ),

                "compressor_exit_area_m2":
                    scalar(
                        self.prob,
                        f"{point}.comp.Fl_O:stat:area",
                        "m**2"
                    ),
            }

            row["impeller_diameter_m"] = (
                4.0 *
                row["compressor_exit_area_m2"] /
                3.141592653589793
            ) ** 0.5

            row["station_temps_degR"] = [
                scalar(
                    self.prob,
                    f"{point}.{station}:tot:T",
                    "degR"
                )
                for station in STATIONS
            ]

            row["station_pressures_psi"] = [
                scalar(
                    self.prob,
                    f"{point}.{station}:tot:P",
                    "psi"
                )
                for station in STATIONS
            ]

            row["station_machs"] = [
                scalar(
                    self.prob,
                    f"{point}.{station}:stat:MN"
                )
                for station in STATIONS
            ]

            rows.append(row)

        return rows

    # ============================================================
    # ORIGINAL ANALYSIS WINDOW UI
    # ============================================================

    def build_ui(self):

        central = QWidget()
        layout = QVBoxLayout(central)

        self.setCentralWidget(central)

        # Keep original window spacing/style
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # --------------------------------------------------------
        # ORIGINAL INTRO TEXT
        # --------------------------------------------------------

        intro = QLabel(
            "Plots use converged solver values. "
            "Area-derived impeller diameter is an equivalent "
            "circular-flow-area estimate, not a mechanical "
            "blade-tip diameter."
        )

        intro.setWordWrap(True)

        layout.addWidget(intro)

        # --------------------------------------------------------
        # TABS
        # --------------------------------------------------------

        tabs = QTabWidget()

        layout.addWidget(tabs)

        tabs.addTab(
            self.make_pressure_temperature_plot(),
            "1. Pressure vs Temperature"
        )

        tabs.addTab(
            self.make_t4_thrust_plot(),
            "2. T4 vs Thrust"
        )

        tabs.addTab(
            self.make_t4_rpm_plot(),
            "3. T4 vs RPM"
        )

        tabs.addTab(
            self.make_thrust_altitude_plot(),
            "4. Thrust vs Altitude"
        )

        tabs.addTab(
            self.make_area_plot(),
            "5. Flow / Area / Diameter"
        )

        tabs.addTab(
            self.make_station_plot(),
            "6. Stations / Altitude"
        )

        # --------------------------------------------------------
        # EXPORT
        # --------------------------------------------------------

        export_button = QPushButton(
            "Export analysis CSV"
        )

        export_button.clicked.connect(
            self.export_csv
        )

        layout.addWidget(export_button)

    # ============================================================
    # MATPLOTLIB CANVAS + TOOLBAR + HOVER + SCROLL ZOOM
    # ============================================================

    def canvas(self, figure, hover_specs=None):

        container = QWidget()

        layout = QVBoxLayout(container)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        canvas = FigureCanvas(figure)

        canvas.setMinimumSize(850, 600)

        toolbar = NavigationToolbar2QT(
            canvas,
            container
        )

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        # Hover functionality
        if hover_specs:

            self.add_hover_annotations(
                canvas,
                hover_specs
            )

        return container

    # ============================================================
    # FIGURE
    # ============================================================

    @staticmethod
    def figure(title):

        # IMPORTANT:
        # Do NOT use layout="constrained" here.
        # The hover annotation can cause constrained_layout
        # to resize/reposition the graph while hovering.

        fig = Figure()

        fig.subplots_adjust(
            left=0.07,
            right=0.98,
            bottom=0.12,
            top=0.90
        )

        fig.suptitle(
            title,
            fontsize=14,
            fontweight="bold"
        )

        return fig

    # ============================================================
    # UNIT CONVERSIONS
    # ============================================================

    @staticmethod
    def c_to_kpa_pressure(pressure_psi):

        return pressure_psi * 6.894757293168

    @staticmethod
    def degr_to_c(temp_degR):

        return temp_degR / 1.8 - 273.15

    @staticmethod
    def lbf_to_kn(thrust_lbf):

        return thrust_lbf * 0.0044482216152605

    # ============================================================
    # HOVER ANNOTATIONS
    # ============================================================

    def add_hover_annotations(
        self,
        canvas,
        hover_specs
    ):
        """
        Add hover information to plotted data points.

        hover_specs:
            [
                {
                    "artist": matplotlib artist,
                    "texts": [text for each point]
                }
            ]
        """

        annotations = {}

        # One annotation per axis
        for spec in hover_specs:

            ax = spec["artist"].axes

            if ax not in annotations:

                annotation = ax.annotate(
                    "",
                    xy=(0, 0),
                    xytext=(12, 12),
                    textcoords="offset points",

                    bbox=dict(
                        boxstyle="round,pad=0.4",
                        fc="white",
                        ec="0.35",
                        alpha=0.92
                    ),

                    arrowprops=dict(
                        arrowstyle="->",
                        color="0.35"
                    )
                )

                annotation.set_visible(False)

                annotations[ax] = annotation

        # --------------------------------------------------------
        # MOUSE MOVE
        # --------------------------------------------------------

        def on_move(event):

            if event.inaxes is None:

                changed = False

                for annotation in annotations.values():

                    if annotation.get_visible():

                        annotation.set_visible(False)
                        changed = True

                if changed:
                    canvas.draw_idle()

                return

            visible_annotation = annotations.get(
                event.inaxes
            )

            if visible_annotation is None:
                return

            found = False

            for spec in hover_specs:

                artist = spec["artist"]

                if artist.axes is not event.inaxes:
                    continue

                contains, info = artist.contains(event)

                if not contains:
                    continue

                indices = info.get("ind", [])

                if len(indices) == 0:
                    continue

                index = int(indices[0])

                texts = spec["texts"]

                if index >= len(texts):
                    continue

                # Scatter
                if hasattr(
                    artist,
                    "get_offsets"
                ):

                    xy = artist.get_offsets()[index]

                # Line
                else:

                    xy = (
                        artist.get_xdata()[index],
                        artist.get_ydata()[index]
                    )

                visible_annotation.xy = (
                    float(xy[0]),
                    float(xy[1])
                )

                visible_annotation.set_text(
                    texts[index]
                )

                visible_annotation.set_visible(
                    True
                )

                found = True

                break

            if not found:

                if visible_annotation.get_visible():

                    visible_annotation.set_visible(
                        False
                    )

            canvas.draw_idle()

        canvas.mpl_connect(
            "motion_notify_event",
            on_move
        )

        # --------------------------------------------------------
        # MOUSE WHEEL ZOOM
        # --------------------------------------------------------

        def on_scroll(event):

            if event.inaxes is None:
                return

            ax = event.inaxes

            # Scroll UP = zoom IN
            if event.button == "up":

                scale = 0.8

            # Scroll DOWN = zoom OUT
            elif event.button == "down":

                scale = 1.25

            else:

                return

            # Current limits
            x_left, x_right = ax.get_xlim()
            y_bottom, y_top = ax.get_ylim()

            # Mouse location in data coordinates
            x_mouse = event.xdata
            y_mouse = event.ydata

            if (
                x_mouse is None
                or y_mouse is None
            ):
                return

            # Zoom around mouse position
            ax.set_xlim(
                x_mouse -
                (x_mouse - x_left) * scale,

                x_mouse +
                (x_right - x_mouse) * scale
            )

            ax.set_ylim(
                y_mouse -
                (y_mouse - y_bottom) * scale,

                y_mouse +
                (y_top - y_mouse) * scale
            )

            canvas.draw_idle()

        canvas.mpl_connect(
            "scroll_event",
            on_scroll
        )

        return canvas


    # ============================================================
    # DESIGN / OFF-DESIGN POINT MARKERS
    # ============================================================

    def add_design_offdesign_markers(
            self,
            ax,
            x,
            y,
            *,
            colors=None,
            size=80,
            zorder=6,
            design_marker="*",
            offdesign_marker="o",
    ):
        """
        DESIGN point = star
        OFF-DESIGN points = circles
        """

        x = np.asarray(x)
        y = np.asarray(y)

        # Convert colour information safely
        if colors is not None:
            colors_array = np.asarray(colors)
        else:
            colors_array = None

        for i, row in enumerate(self.rows):

            is_design = (
                    str(row["point"]).upper() == "DESIGN"
            )

            # Determine colour safely
            if colors_array is None:
                color = None

            elif colors_array.ndim == 0:
                # Single colour, e.g. "#bf4b17"
                color = colors_array.item()

            elif colors_array.ndim == 1:
                # RGB/RGBA tuple OR list of colours
                if len(colors_array) in (3, 4):
                    color = tuple(colors_array.tolist())
                else:
                    color = colors_array[i]

            else:
                # Array of RGBA colours, e.g. RPM colour map
                color = colors_array[i]

            if is_design:

                ax.scatter(
                    x[i],
                    y[i],
                    marker=design_marker,
                    s=size * 2.0,
                    color=color,
                    edgecolors="black",
                    linewidths=0.8,
                    zorder=zorder + 1,
                )

            else:

                ax.scatter(
                    x[i],
                    y[i],
                    marker=offdesign_marker,
                    s=size,
                    color=color,
                    edgecolors="black",
                    linewidths=0.6,
                    zorder=zorder,
                )

    # ============================================================
    # 1. PRESSURE vs TEMPERATURE
    # ============================================================

    def make_pressure_temperature_plot(self):

        fig = self.figure(
            "Total Pressure versus Total Temperature at Every Station"
        )

        ax = fig.add_subplot(111)

        hover_specs = []

        for index, label in enumerate(STATION_LABELS):

            # Convert native pyCycle values
            # degR -> °C
            # psi  -> kPa

            # X = Total Pressure (kPa)
            x = np.array([
                self.c_to_kpa_pressure(
                    r["station_pressures_psi"][index]
                )
                for r in self.rows
            ])

            # Y = Total Temperature (°C)
            y = np.array([
                self.degr_to_c(
                    r["station_temps_degR"][index]
                )
                for r in self.rows
            ])

            # Sort for clean connecting line
            order = np.argsort(x)

            xs = x[order]
            ys = y[order]

            line, = ax.plot(
                xs,
                ys,
                "-",
                label=label,
                linewidth=1.6
            )

            hover_specs.append({
                "artist": line,

                "texts": [
                    f"{label}\n"
                    f"Altitude: "
                    f"{self.rows[int(order[i])]['altitude_ft']:.0f} ft\n"
                    f"Tt: {xs[i]:.2f} °C\n"
                    f"Pt: {ys[i]:.2f} kPa"

                    for i in range(len(xs))
                ]
            })

            # Design = star, off-design = circle.
            sorted_rows = [self.rows[int(i)] for i in order]
            marker_colors = [line.get_color()] * len(xs)

            self.add_design_offdesign_markers(
                ax,
                xs,
                ys,
                colors=marker_colors,
                size=55
            )

            # Trend line
            if (
                len(xs) >= 2
                and np.ptp(xs) > 1e-12
            ):

                slope, intercept = np.polyfit(
                    xs,
                    ys,
                    1
                )

                margin = max(
                    np.ptp(xs) * 0.08,
                    1.0
                )

                trend_x = np.linspace(
                    xs.min() - margin,
                    xs.max() + margin,
                    100
                )

                trend_y = (
                    slope * trend_x
                    + intercept
                )

                ax.plot(
                    trend_x,
                    trend_y,
                    "--",
                    linewidth=1.1,
                    alpha=0.55
                )

        ax.set(
            xlabel="Total pressure (kPa)",
            ylabel="Total temperature (°C)"
        )
        ax.set_xlim(0, 1000)
        ax.grid(True, alpha=0.3)

        ax.margins(
            x=0.08,
            y=0.08
        )

        ax.legend(
            ncol=2
        )

        return self.canvas(
            fig,
            hover_specs
        )

    # ============================================================
    # 2. T4 vs THRUST
    # ============================================================

    def make_t4_thrust_plot(self):

        fig = self.figure(
            "Maximum Cycle Temperature (T4) versus Net Thrust"
        )

        ax = fig.add_subplot(111)

        x = np.array([
            self.lbf_to_kn(
                r["thrust_lbf"]
            )
            for r in self.rows
        ])

        y = np.array([
            self.degr_to_c(
                r["t4_degR"]
            )
            for r in self.rows
        ])

        # Keep the original plot style:
        # scatter + RPM colour coding

        scatter = ax.scatter(
            x,
            y,
            c=[
                r["rpm"]
                for r in self.rows
            ],
            cmap="viridis",
            s=70
        )

        # Mark the design point with a star while keeping all off-design
        # points as circles.  Colour still represents shaft speed.
        rpm_values = np.asarray([r["rpm"] for r in self.rows])
        marker_colors = scatter.cmap(scatter.norm(rpm_values))

        self.add_design_offdesign_markers(
            ax,
            x,
            y,
            colors=marker_colors,
            size=70
        )

        hover_specs = [{
            "artist": scatter,

            "texts": [
                f"Altitude: {r['altitude_ft']:.0f} ft\n"
                f"T4: {self.degr_to_c(r['t4_degR']):.2f} °C\n"
                f"Net thrust: "
                f"{self.lbf_to_kn(r['thrust_lbf']):.3f} kN\n"
                f"Shaft speed: {r['rpm']:.0f} rpm"

                for r in self.rows
            ]
        }]

        ax.set(
            xlabel="Net thrust (kN)",
            ylabel=(
                "T4 / burner-exit "
                "total temperature (°C)"
            )
        )

        ax.grid(True, alpha=0.3)

        ax.margins(
            x=0.08,
            y=0.08
        )

        fig.colorbar(
            scatter,
            ax=ax,
            label="Shaft speed (rpm)"
        )

        return self.canvas(
            fig,
            hover_specs
        )

    # ============================================================
    # 3. T4 vs RPM
    # ============================================================

    def make_t4_rpm_plot(self):

        fig = self.figure(
            "Maximum Cycle Temperature (T4) versus Shaft Speed"
        )

        ax = fig.add_subplot(111)

        x = np.array([
            r["rpm"]
            for r in self.rows
        ])

        y = np.array([
            self.degr_to_c(
                r["t4_degR"]
            )
            for r in self.rows
        ])

        line, = ax.plot(
            x[1:],
            y[1:],
            "-",
            color="#bf4b17",
            linewidth=1.6
        )

        self.add_design_offdesign_markers(
            ax,
            x,
            y,
            colors="#bf4b17",
            size=70
        )

        hover_specs = [{
            "artist": line,

            "texts": [
                f"Altitude: {r['altitude_ft']:.0f} ft\n"
                f"Shaft speed: {r['rpm']:.0f} rpm\n"
                f"T4: {self.degr_to_c(r['t4_degR']):.2f} °C\n"
                f"Net thrust: "
                f"{self.lbf_to_kn(r['thrust_lbf']):.3f} kN"

                for r in self.rows
            ]
        }]

        ax.set(
            xlabel="Shaft speed, Nmech (rpm)",
            ylabel=(
                "T4 / burner-exit "
                "total temperature (°C)"
            )
        )

        ax.grid(True, alpha=0.3)

        ax.margins(
            x=0.08,
            y=0.08
        )

        return self.canvas(
            fig,
            hover_specs
        )

    # ============================================================
    # 4. THRUST vs ALTITUDE
    # ============================================================

    def make_thrust_altitude_plot(self):

        fig = self.figure(
            "Net Thrust at the Evaluated Operating Altitudes"
        )

        ax = fig.add_subplot(111)

        x = np.array([
            r["altitude_ft"]
            for r in self.rows
        ])

        y = np.array([
            self.lbf_to_kn(r["thrust_lbf"])
            for r in self.rows
        ])

        line, = ax.plot(
            x[1:],
            y[1:],
            "-",
            color="#1769aa",
            linewidth=1.6
        )

        self.add_design_offdesign_markers(
            ax,
            x,
            y,
            colors="#1769aa",
            size=70
        )

        hover_specs = [{
            "artist": line,

            "texts": [
                f"Altitude: "
                f"{r['altitude_ft']:.0f} ft\n"
                f"Net thrust: "
                f"{self.lbf_to_kn(r['thrust_lbf']):.3f} kN\n"
                f"T4: "
                f"{self.degr_to_c(r['t4_degR']):.2f} °C\n"
                f"Shaft speed: "
                f"{r['rpm']:.0f} rpm"

                for r in self.rows
            ]
        }]

        ax.set(
            xlabel="Altitude (ft)",
            ylabel="Net thrust (kN)"
        )
        ax.grid(True, alpha=0.3)

        ax.margins(
            x=0.08,
            y=0.08
        )

        return self.canvas(
            fig,
            hover_specs
        )

    # ============================================================
    # 5. MASS FLOW / AREA / DIAMETER
    # ============================================================

    def make_area_plot(self):

        fig = self.figure(
            "Mass Flow, Flow Areas, and Equivalent Compressor Diameter"
        )

        ax1 = fig.add_subplot(111)

        x = np.array([
            r["mass_flow_kg_s"]
            for r in self.rows
        ])

        y_inlet = np.array([
            r["inlet_area_m2"]
            for r in self.rows
        ])

        y_comp = np.array([
            r["compressor_exit_area_m2"]
            for r in self.rows
        ])

        y_diam = np.array([
            r["impeller_diameter_m"]
            for r in self.rows
        ])

        line1, = ax1.plot(
            x[1:],
            y_inlet[1:],
            "-",
            label="Inlet area"
        )

        line2, = ax1.plot(
            x[1:],
            y_comp[1:],
            "-",
            label="Compressor outlet area"
        )

        self.add_design_offdesign_markers(
            ax1,
            x,
            y_inlet,
            colors=line1.get_color(),
            size=55
        )

        self.add_design_offdesign_markers(
            ax1,
            x,
            y_comp,
            colors=line2.get_color(),
            size=55
        )

        ax1.set(
            xlabel="Mass flow (kg/s)",
            ylabel="Flow area (m²)"
        )

        ax1.grid(True, alpha=0.3)

        ax1.margins(
            x=0.08,
            y=0.08
        )

        ax2 = ax1.twinx()

        line3, = ax2.plot(
            x[1:],
            y_diam[1:],
            "-",
            color="#bf4b17",
            label="Equivalent outlet diameter"
        )

        self.add_design_offdesign_markers(
            ax2,
            x,
            y_diam,
            colors="#bf4b17",
            size=55
        )

        ax2.set_ylabel(
            "Equivalent circular diameter (m)"
        )

        hover_specs = [

            {
                "artist": line1,

                "texts": [
                    f"Mass flow: "
                    f"{r['mass_flow_kg_s']:.4f} kg/s\n"
                    f"Inlet area: "
                    f"{r['inlet_area_m2']:.5f} m²\n"
                    f"Altitude: "
                    f"{r['altitude_ft']:.0f} ft"

                    for r in self.rows
                ]
            },

            {
                "artist": line2,

                "texts": [
                    f"Mass flow: "
                    f"{r['mass_flow_kg_s']:.4f} kg/s\n"
                    f"Compressor outlet area: "
                    f"{r['compressor_exit_area_m2']:.5f} m²\n"
                    f"Altitude: "
                    f"{r['altitude_ft']:.0f} ft"

                    for r in self.rows
                ]
            },

            {
                "artist": line3,

                "texts": [
                    f"Mass flow: "
                    f"{r['mass_flow_kg_s']:.4f} kg/s\n"
                    f"Equivalent diameter: "
                    f"{r['impeller_diameter_m']:.5f} m\n"
                    f"Altitude: "
                    f"{r['altitude_ft']:.0f} ft"

                    for r in self.rows
                ]
            }
        ]

        lines1, labels1 = (
            ax1.get_legend_handles_labels()
        )

        lines2, labels2 = (
            ax2.get_legend_handles_labels()
        )

        ax1.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc="best"
        )

        return self.canvas(
            fig,
            hover_specs
        )

    # ============================================================
    # 6. STATION ANALYSIS
    # ============================================================

    def make_station_plot(self):

        fig = self.figure(
            "Station Temperatures and Mach Number for Each Operating Altitude"
        )

        ax_temp, ax_mach = fig.subplots(
            1,
            2
        )

        station_x = np.arange(
            len(STATIONS)
        )

        hover_specs = []

        for row in self.rows:

            label = (
                f"{row['point']}: "
                f"{row['altitude_ft']:.0f} ft"
            )

            temp_c = [
                self.degr_to_c(value)
                for value in row[
                    "station_temps_degR"
                ]
            ]

            temp_line, = ax_temp.plot(
                station_x,
                temp_c,
                "-",
                label=label
            )

            mach_line, = ax_mach.plot(
                station_x,
                row["station_machs"],
                "-",
                label=label
            )

            # Consistent marker convention:
            # DESIGN = star, OFF-DESIGN = circle.
            marker = "*" if str(row["point"]).upper() == "DESIGN" else "o"
            marker_size = 110 if marker == "*" else 55

            ax_temp.scatter(
                station_x,
                temp_c,
                marker=marker,
                s=marker_size,
                c=temp_line.get_color(),
                edgecolors="black",
                linewidths=0.7,
                zorder=6
            )

            ax_mach.scatter(
                station_x,
                row["station_machs"],
                marker=marker,
                s=marker_size,
                c=mach_line.get_color(),
                edgecolors="black",
                linewidths=0.7,
                zorder=6
            )

            # Temperature hover
            hover_specs.append({

                "artist": temp_line,

                "texts": [
                    f"{STATION_LABELS[i]}\n"
                    f"Altitude: "
                    f"{row['altitude_ft']:.0f} ft\n"
                    f"Total temperature: "
                    f"{temp_c[i]:.2f} °C\n"
                    f"Mach: "
                    f"{row['station_machs'][i]:.3f}"

                    for i in range(len(STATIONS))
                ]
            })

            # Mach hover
            hover_specs.append({

                "artist": mach_line,

                "texts": [
                    f"{STATION_LABELS[i]}\n"
                    f"Altitude: "
                    f"{row['altitude_ft']:.0f} ft\n"
                    f"Total temperature: "
                    f"{temp_c[i]:.2f} °C\n"
                    f"Mach: "
                    f"{row['station_machs'][i]:.3f}"

                    for i in range(len(STATIONS))
                ]
            })

        for ax, ylabel in (

            (
                ax_temp,
                "Total temperature (°C)"
            ),

            (
                ax_mach,
                "Static Mach number (-)"
            )

        ):

            ax.set_xticks(
                list(station_x),
                STATION_LABELS,
                rotation=35,
                ha="right"
            )

            ax.set_ylabel(
                ylabel
            )

            ax.grid(
                True,
                alpha=0.3
            )

            ax.margins(
                x=0.08,
                y=0.08
            )

        ax_temp.legend(
            fontsize=8
        )

        return self.canvas(
            fig,
            hover_specs
        )

    # ============================================================
    # CSV EXPORT
    # ============================================================

    def export_csv(self):

        output_dir = (
            Path(__file__).resolve().parent
            / "input_gui_out"
            / "analysis"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        destination = (
            output_dir
            / "turbojet_analysis.csv"
        )

        fields = [
            "point",
            "altitude_ft",
            "freestream_mach",
            "rpm",
            "thrust_lbf",
            "mass_flow_kg_s",
            "t4_degR",
            "inlet_area_m2",
            "compressor_exit_area_m2",
            "impeller_diameter_m"
        ]

        with destination.open(
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fields
            )

            writer.writeheader()

            writer.writerows(
                {
                    field: row[field]
                    for field in fields
                }
                for row in self.rows
            )

        QMessageBox.information(
            self,
            "Analysis exported",
            f"Saved: {destination}"
        )

class EngineWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.window = parent

        self.pix = QPixmap(str(Path(__file__).resolve().parent / "Turbojet_operation-centrifugal_flow-fr.png"))

        self.setFixedSize(900, 350)

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

        # Stretch image horizontally only
        scaled_width = int(self.width() * 0.95)
        scaled_height = int(self.pix.height() * 0.40)

        x = 0
        y = (self.height() - scaled_height) // 2

        target_rect = QRect(
            x,
            y,
            scaled_width,
            scaled_height
        )

        painter.drawPixmap(
            target_rect,
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

        self.showMaximized()

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

        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # ==========================================================
        # HEADER
        # ==========================================================

        title = QLabel("OUTPUT WINDOW")

        font = title.font()
        font.setPointSize(15)
        font.setBold(True)
        title.setFont(font)

        layout.addWidget(title)

        # ==========================================================
        # UPPER SECTION
        # ENGINE DIAGRAM + PERFORMANCE TABLE
        # ==========================================================

        middle = QHBoxLayout()
        middle.setSpacing(10)

        layout.addLayout(middle, stretch=1)

        # ---------------- ENGINE DIAGRAM ----------------

        self.engine = EngineWidget(self)

        middle.addWidget(self.engine)

        # ---------------- PERFORMANCE TABLE ----------------

        self.performance = QTableWidget()

        self.performance.setColumnCount(2)

        self.performance.setHorizontalHeaderLabels(
            ["Parameter", "Value"]
        )

        self.performance.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.performance.setFixedHeight(350)

        performance_header = self.performance.horizontalHeader()

        performance_header.setSectionResizeMode(
            0, QHeaderView.Stretch
        )

        performance_header.setSectionResizeMode(
            1, QHeaderView.Stretch
        )

        middle.addWidget(
            self.performance,
            stretch=5
        )

        # ==========================================================
        # LOWER SECTION
        # FLOW STATION + OPERATING POINT CONTROLS
        # ==========================================================

        bottom = QHBoxLayout()
        bottom.setSpacing(15)

        layout.addLayout(bottom)

        # ==========================================================
        # LEFT — FLOW STATION TABLE
        # ==========================================================

        station_left = QVBoxLayout()
        station_left.setSpacing(4)

        self.stationLabel = QLabel(
            "Flow Station : Flight Conditions"
        )

        font = self.stationLabel.font()
        font.setPointSize(12)
        font.setBold(True)
        self.stationLabel.setFont(font)

        station_left.addWidget(self.stationLabel)

        self.station = QTableWidget()

        self.station.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.station.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.station.verticalHeader().setDefaultSectionSize(30)

        # 11 rows + header
        self.station.setFixedHeight(365)

        self.station.setColumnCount(3)

        self.station.setHorizontalHeaderLabels(
            ["Property", "Unit", "Value"]
        )

        self.station.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        station_header = self.station.horizontalHeader()

        # Property
        station_header.setSectionResizeMode(
            0, QHeaderView.Stretch
        )

        # Unit
        station_header.setSectionResizeMode(
            1, QHeaderView.Fixed
        )
        station_header.resizeSection(1, 190)

        # Value
        station_header.setSectionResizeMode(
            2, QHeaderView.Stretch
        )

        station_left.addWidget(self.station)

        # Green area
        bottom.addLayout(
            station_left,
            stretch=7
        )

        # ==========================================================
        # RIGHT — OPERATING POINT CONTROLS
        # ==========================================================

        controls = QVBoxLayout()
        controls.setSpacing(10)

        operating_label = QLabel(
            "Operating Point"
        )

        font = operating_label.font()
        font.setPointSize(19)
        font.setBold(True)
        operating_label.setFont(font)

        controls.addWidget(
            operating_label
        )

        # Design / Off-Design selector
        self.combo = QComboBox()

        self.combo.addItem("DESIGN")
        self.combo.addItems(self.od_pts)

        self.combo.setMinimumWidth(250)
        self.combo.setMinimumHeight(45)

        self.combo.currentTextChanged.connect(
            self.change_point
        )

        controls.addWidget(
            self.combo
        )

        # Analysis button
        self.analysis_button = QPushButton(
            "Open Analysis Plots"
        )

        self.analysis_button.setMinimumWidth(250)
        self.analysis_button.setMinimumHeight(45)

        self.analysis_button.clicked.connect(
            self.open_analysis
        )

        controls.addWidget(
            self.analysis_button
        )

        # Keep controls toward the top of the red region
        controls.addStretch()

        # Red area
        bottom.addLayout(
            controls,
            stretch=3
        )
    ###################################################

    def change_point(self,text):

        self.current_pt=text

        self.update_performance()

        self.update_station("fc.Fl_O")

    def open_analysis(self):
        try:
            points = ["DESIGN"] + list(self.od_pts)

            self.analysis = AnalysisWindow(self.prob, points)

            self.analysis.setWindowFlags(Qt.Window)
            self.analysis.showMaximized()
            self.analysis.raise_()
            self.analysis.activateWindow()

        except Exception as error:
            print("ANALYSIS WINDOW ERROR:", repr(error))
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Could not open Analysis Plots:\n\n{error}"
            )
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
