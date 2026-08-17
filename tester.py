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
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # ============================================================
        # TOP TITLE
        # ============================================================

        title = QLabel("OUTPUT WINDOW")

        font = title.font()
        font.setPointSize(15)
        font.setBold(True)
        title.setFont(font)

        layout.addWidget(title)

        # ============================================================
        # UPPER SECTION
        # ENGINE DIAGRAM + PERFORMANCE TABLE
        # ============================================================

        middle = QHBoxLayout()
        middle.setSpacing(10)

        layout.addLayout(middle, stretch=1)

        # ---------------- ENGINE ----------------

        self.engine = EngineWidget(self)

        middle.addWidget(self.engine, stretch=7)

        # ---------------- PERFORMANCE TABLE ----------------

        self.performance = QTableWidget()

        self.performance.setColumnCount(2)

        self.performance.setHorizontalHeaderLabels(
            ["Parameter", "Value"]
        )

        self.performance.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        performance_header = self.performance.horizontalHeader()

        performance_header.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        performance_header.setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )

        middle.addWidget(self.performance)

        # ============================================================
        # ANALYSIS PLOTS
        # ============================================================

        tabs = QTabWidget()

        tabs.addTab(
            self.make_pressure_temperature_plot(),
            "Pressure vs Temperature"
        )

        tabs.addTab(
            self.make_t4_thrust_plot(),
            "T4 vs Thrust"
        )

        tabs.addTab(
            self.make_t4_rpm_plot(),
            "T4 vs RPM"
        )

        tabs.addTab(
            self.make_thrust_altitude_plot(),
            "Thrust vs Altitude"
        )

        tabs.addTab(
            self.make_area_plot(),
            "Mass Flow & Area"
        )

        tabs.addTab(
            self.make_station_plot(),
            "Station Analysis"
        )

        layout.addWidget(tabs, stretch=1)

        # Export button
        export_button = QPushButton("Export Analysis CSV")
        export_button.clicked.connect(self.export_csv)

        layout.addWidget(export_button)

        # ============================================================
        # LOWER SECTION
        # FLOW STATION TABLE + OPERATING POINT CONTROLS
        # ============================================================

        bottom = QHBoxLayout()
        bottom.setSpacing(15)

        layout.addLayout(bottom, stretch=0)

        # ============================================================
        # LEFT SIDE — FLOW STATION
        # ============================================================

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

        self.station.setColumnCount(3)

        self.station.setHorizontalHeaderLabels(
            ["Property", "Unit", "Value"]
        )

        self.station.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        station_header = self.station.horizontalHeader()

        station_header.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        station_header.setSectionResizeMode(
            1,
            QHeaderView.Fixed
        )

        station_header.resizeSection(1, 190)

        station_header.setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )

        station_left.addWidget(self.station)

        # Flow station occupies the large green region
        bottom.addLayout(station_left, stretch=7)

        # # ============================================================
        # # RIGHT SIDE — OPERATING POINT CONTROLS
        # # ============================================================
        #
        # controls = QVBoxLayout()
        # controls.setSpacing(10)
        #
        # # Operating Point label
        # operating_label = QLabel("Operating Point")
        #
        # font = operating_label.font()
        # font.setPointSize(12)
        # font.setBold(True)
        # operating_label.setFont(font)
        #
        # controls.addWidget(operating_label)
        #
        # # Design / Off-Design dropdown
        # self.combo = QComboBox()
        #
        # self.combo.addItem("DESIGN")
        # self.combo.addItems(self.points[1:])
        #
        # self.combo.setMinimumWidth(250)
        # self.combo.setMinimumHeight(45)
        #
        # self.combo.currentTextChanged.connect(
        #     self.change_point
        # )
        #
        # controls.addWidget(self.combo)
        #
        # # Open Analysis Plots button
        # self.analysis_button = QPushButton(
        #     "Open Analysis Plots"
        # )
        #
        # self.analysis_button.setMinimumWidth(250)
        # self.analysis_button.setMinimumHeight(45)
        #
        # self.analysis_button.clicked.connect(
        #     self.open_analysis
        # )
        #
        # controls.addWidget(self.analysis_button)
        #
        # # Keep controls toward the top of the red region
        # controls.addStretch()
        #
        # # Red region
        # bottom.addLayout(controls, stretch=3)

    def canvas(self, figure, hover_specs=None):
        """Return a widget containing a Matplotlib canvas and navigation toolbar.

        The toolbar provides pan/zoom/reset/save controls.  hover_specs is a list of
        dictionaries describing plotted artists and the text to show when the mouse
        is over a data point.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        canvas = FigureCanvas(figure)
        canvas.setMinimumSize(850, 600)
        toolbar = NavigationToolbar2QT(canvas, container)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        if hover_specs:
            self.add_hover_annotations(canvas, hover_specs)

        return container

    @staticmethod
    def figure(title):
        fig = Figure()
        fig.subplots_adjust(
            left=0.07,
            right=0.98,
            bottom=0.12,
            top=0.90
        )
        fig.suptitle(title, fontsize=14, fontweight="bold")
        return fig

    @staticmethod
    def c_to_kpa_pressure(pressure_psi):
        return pressure_psi * 6.894757293168

    @staticmethod
    def degr_to_c(temp_degR):
        return temp_degR / 1.8 - 273.15

    @staticmethod
    def lbf_to_kn(thrust_lbf):
        return thrust_lbf * 0.0044482216152605

    def add_hover_annotations(self, canvas, hover_specs):
        """Attach hover labels to Matplotlib line/scatter artists.

        Each spec must contain:
            artist: Matplotlib Line2D or PathCollection
            texts:  list of strings, one per plotted data point
        """
        annotations = {}
        for spec in hover_specs:
            ax = spec["artist"].axes
            if ax not in annotations:
                annotation = ax.annotate(
                    "",
                    xy=(0, 0),
                    xytext=(12, 12),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.35", alpha=0.92),
                    arrowprops=dict(arrowstyle="->", color="0.35"),
                )
                annotation.set_visible(False)
                annotations[ax] = annotation

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

            visible_annotation = annotations.get(event.inaxes)
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

                if hasattr(artist, "get_offsets"):
                    xy = artist.get_offsets()[index]
                else:
                    xy = (artist.get_xdata()[index], artist.get_ydata()[index])

                visible_annotation.xy = (float(xy[0]), float(xy[1]))
                visible_annotation.set_text(texts[index])
                visible_annotation.set_visible(True)
                found = True
                break

            if not found and visible_annotation.get_visible():
                visible_annotation.set_visible(False)

            canvas.draw_idle()

        canvas.mpl_connect("motion_notify_event", on_move)

        def on_scroll(event):
            if event.inaxes is None:
                return

            ax = event.inaxes

            # Zoom factor
            if event.button == "up":
                scale = 0.8       # zoom in
            elif event.button == "down":
                scale = 1.25      # zoom out
            else:
                return

            # Current axis limits
            x_left, x_right = ax.get_xlim()
            y_bottom, y_top = ax.get_ylim()

            # Mouse position in data coordinates
            x_mouse = event.xdata
            y_mouse = event.ydata

            # Zoom relative to mouse position
            ax.set_xlim(
                x_mouse - (x_mouse - x_left) * scale,
                x_mouse + (x_right - x_mouse) * scale
            )

            ax.set_ylim(
                y_mouse - (y_mouse - y_bottom) * scale,
                y_mouse + (y_top - y_mouse) * scale
            )

            canvas.draw_idle()

        canvas.mpl_connect("scroll_event", on_scroll)

    def make_pressure_temperature_plot(self):
        fig = self.figure("Total Pressure versus Total Temperature at Every Station")
        ax = fig.add_subplot(111)
        hover_specs = []

        for index, label in enumerate(STATION_LABELS):
            # Convert only for display/plotting.  The values stored in self.rows
            # remain the native pyCycle output units (degR and psi).
            x = np.array([self.degr_to_c(r["station_temps_degR"][index]) for r in self.rows])
            y = np.array([self.c_to_kpa_pressure(r["station_pressures_psi"][index]) for r in self.rows])

            # Sort by temperature so the connecting curve is visually ordered.
            order = np.argsort(x)
            xs = x[order]
            ys = y[order]

            line, = ax.plot(xs, ys, "o-", label=label, linewidth=1.6, markersize=5)
            hover_specs.append({
                "artist": line,
                "texts": [
                    f"{label}\n"
                    f"Altitude: {self.rows[int(order[i])]['altitude_ft']:.0f} ft\n"
                    f"Tt: {xs[i]:.2f} °C\n"
                    f"Pt: {ys[i]:.2f} kPa"
                    for i in range(len(xs))
                ],
            })

            # Linear trend line, extended slightly beyond the first/last point.
            if len(xs) >= 2 and np.ptp(xs) > 1e-12:
                slope, intercept = np.polyfit(xs, ys, 1)
                margin = max(np.ptp(xs) * 0.08, 1.0)
                trend_x = np.linspace(xs.min() - margin, xs.max() + margin, 100)
                trend_y = slope * trend_x + intercept
                ax.plot(trend_x, trend_y, "--", linewidth=1.1, alpha=0.55)

        ax.set(xlabel="Total temperature (°C)", ylabel="Total pressure (kPa)")
        ax.grid(True, alpha=.3)
        ax.margins(x=0.08, y=0.08)
        ax.legend(ncol=2)
        return self.canvas(fig, hover_specs)

    def make_t4_thrust_plot(self):
        fig = self.figure("Maximum Cycle Temperature (T4) versus Net Thrust")
        ax = fig.add_subplot(111)
        x = np.array([self.lbf_to_kn(r["thrust_lbf"]) for r in self.rows])
        y = np.array([self.degr_to_c(r["t4_degR"]) for r in self.rows])

        scatter = ax.scatter(x, y, s=70)
        hover_specs = [{
            "artist": scatter,
            "texts": [
                f"Altitude: {r['altitude_ft']:.0f} ft\n"
                f"T4: {self.degr_to_c(r['t4_degR']):.2f} °C\n"
                f"Net thrust: {self.lbf_to_kn(r['thrust_lbf']):.3f} kN\n"
                f"Shaft speed: {r['rpm']:.0f} rpm"
                for r in self.rows
            ],
        }]
        ax.set(xlabel="Net thrust (kN)", ylabel="T4 / burner-exit total temperature (°C)")
        ax.grid(True, alpha=.3)
        ax.margins(x=0.08, y=0.08)
        return self.canvas(fig, hover_specs)

    def make_t4_rpm_plot(self):
        fig = self.figure("Maximum Cycle Temperature (T4) versus Shaft Speed")
        ax = fig.add_subplot(111)
        x = np.array([r["rpm"] for r in self.rows])
        y = np.array([self.degr_to_c(r["t4_degR"]) for r in self.rows])
        line, = ax.plot(x, y, "o-", linewidth=1.6, markersize=5)
        hover_specs = [{
            "artist": line,
            "texts": [
                f"Altitude: {r['altitude_ft']:.0f} ft\n"
                f"Shaft speed: {r['rpm']:.0f} rpm\n"
                f"T4: {self.degr_to_c(r['t4_degR']):.2f} °C\n"
                f"Net thrust: {self.lbf_to_kn(r['thrust_lbf']):.3f} kN"
                for r in self.rows
            ],
        }]
        ax.set(xlabel="Shaft speed, Nmech (rpm)", ylabel="T4 / burner-exit total temperature (°C)")
        ax.grid(True, alpha=.3)
        ax.margins(x=0.08, y=0.08)
        return self.canvas(fig, hover_specs)

    def make_thrust_altitude_plot(self):
        fig = self.figure("Net Thrust at the Evaluated Operating Altitudes")
        ax = fig.add_subplot(111)
        x = np.array([r["altitude_ft"] for r in self.rows])
        y = np.array([self.lbf_to_kn(r["thrust_lbf"]) for r in self.rows])
        line, = ax.plot(x, y, "o-", linewidth=1.6, markersize=5)
        hover_specs = [{
            "artist": line,
            "texts": [
                f"Altitude: {r['altitude_ft']:.0f} ft\n"
                f"Net thrust: {self.lbf_to_kn(r['thrust_lbf']):.3f} kN\n"
                f"T4: {self.degr_to_c(r['t4_degR']):.2f} °C\n"
                f"Shaft speed: {r['rpm']:.0f} rpm"
                for r in self.rows
            ],
        }]
        ax.set(xlabel="Altitude (ft)", ylabel="Net thrust (kN)")
        ax.grid(True, alpha=.3)
        ax.margins(x=0.08, y=0.08)
        return self.canvas(fig, hover_specs)

    def make_area_plot(self):
        fig = self.figure("Mass Flow, Flow Areas, and Equivalent Compressor Diameter")
        ax1 = fig.add_subplot(111)
        x = np.array([r["mass_flow_kg_s"] for r in self.rows])
        y_inlet = np.array([r["inlet_area_m2"] for r in self.rows])
        y_comp = np.array([r["compressor_exit_area_m2"] for r in self.rows])
        y_diam = np.array([r["impeller_diameter_m"] for r in self.rows])

        line1, = ax1.plot(x, y_inlet, "o-", label="Inlet area")
        line2, = ax1.plot(x, y_comp, "s-", label="Compressor outlet area")
        ax1.set(xlabel="Mass flow (kg/s)", ylabel="Flow area (m²)")
        ax1.grid(True, alpha=.3)
        ax1.margins(x=0.08, y=0.08)

        ax2 = ax1.twinx()
        line3, = ax2.plot(x, y_diam, "^-", label="Equivalent outlet diameter")
        ax2.set_ylabel("Equivalent circular diameter (m)")

        hover_specs = [
            {
                "artist": line1,
                "texts": [
                    f"Mass flow: {r['mass_flow_kg_s']:.4f} kg/s\n"
                    f"Inlet area: {r['inlet_area_m2']:.5f} m²\n"
                    f"Altitude: {r['altitude_ft']:.0f} ft"
                    for r in self.rows
                ],
            },
            {
                "artist": line2,
                "texts": [
                    f"Mass flow: {r['mass_flow_kg_s']:.4f} kg/s\n"
                    f"Compressor outlet area: {r['compressor_exit_area_m2']:.5f} m²\n"
                    f"Altitude: {r['altitude_ft']:.0f} ft"
                    for r in self.rows
                ],
            },
            {
                "artist": line3,
                "texts": [
                    f"Mass flow: {r['mass_flow_kg_s']:.4f} kg/s\n"
                    f"Equivalent diameter: {r['impeller_diameter_m']:.5f} m\n"
                    f"Altitude: {r['altitude_ft']:.0f} ft"
                    for r in self.rows
                ],
            },
        ]
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc="best")
        return self.canvas(fig, hover_specs)

    def make_station_plot(self):
        fig = self.figure("Station Temperatures and Mach Number for Each Operating Altitude")
        ax_temp, ax_mach = fig.subplots(1, 2)
        station_x = np.arange(len(STATIONS))
        hover_specs = []

        for row in self.rows:
            label = f"{row['point']}: {row['altitude_ft']:.0f} ft"
            temp_c = [self.degr_to_c(value) for value in row["station_temps_degR"]]

            temp_line, = ax_temp.plot(station_x, temp_c, "o-", label=label)
            mach_line, = ax_mach.plot(station_x, row["station_machs"], "o-", label=label)

            hover_specs.append({
                "artist": temp_line,
                "texts": [
                    f"{STATION_LABELS[i]}\n"
                    f"Altitude: {row['altitude_ft']:.0f} ft\n"
                    f"Total temperature: {temp_c[i]:.2f} °C\n"
                    f"Mach: {row['station_machs'][i]:.3f}"
                    for i in range(len(STATIONS))
                ],
            })
            hover_specs.append({
                "artist": mach_line,
                "texts": [
                    f"{STATION_LABELS[i]}\n"
                    f"Altitude: {row['altitude_ft']:.0f} ft\n"
                    f"Total temperature: {temp_c[i]:.2f} °C\n"
                    f"Mach: {row['station_machs'][i]:.3f}"
                    for i in range(len(STATIONS))
                ],
            })

        for ax, ylabel in ((ax_temp, "Total temperature (°C)"), (ax_mach, "Static Mach number (-)")):
            ax.set_xticks(list(station_x), STATION_LABELS, rotation=35, ha="right")
            ax.set_ylabel(ylabel)
            ax.grid(True, alpha=.3)
            ax.margins(x=0.08, y=0.08)
        ax_temp.legend(fontsize=8)
        return self.canvas(fig, hover_specs)

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
