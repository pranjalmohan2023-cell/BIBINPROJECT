# Turbojet Designer

Run this application with the project interpreter:

```powershell
..\..\.venv\Scripts\python.exe input_gui.py
```

In the IDE, select `C:\Users\ACER\OneDrive\Desktop\bibin project\.venv\Scripts\python.exe` as the Python interpreter. It has PySide6, OpenMDAO, pyCycle, and Matplotlib installed. Selecting the older `venv` environment will show unresolved-import errors because it contains only pip and setuptools.

After solving, click **Open analysis & plots**. The analysis window supplies pressure-temperature station plots, T4 versus thrust/RPM, thrust versus altitude, mass-flow/area/diameter results, and station temperature/Mach plots. **Export analysis CSV** saves the numerical summary to `input_gui_out/analysis/turbojet_analysis.csv`.
