import matplotlib
matplotlib.use('TkAgg')

import dearpygui.dearpygui as dpg
import matplotlib.pyplot as plt

_shared_plot_data = None

def set_latest_plot_data(data_tuple):
    global _shared_plot_data
    _shared_plot_data = data_tuple

    if data_tuple is None:
        print("MATPLOTLIB_MODULE_DEBUG: set_latest_plot_data CALLED with None")
    else:
        try:
            title = data_tuple[4]
            print(f"MATPLOTLIB_MODULE_DEBUG: set_latest_plot_data CALLED with data. Title: '{title}'")
        except (IndexError, TypeError):
            print("MATPLOTLIB_MODULE_DEBUG: set_latest_plot_data CALLED with non-None data, but couldn't get title.")
    # --- END OF ADDED PRINT ---

def plot_with_matplotlib_actual():
    global _shared_plot_data
    # --- ADD PRINT HERE TO SEE VALUE AT THE MOMENT OF CHECKING ---
    print(f"MATPLOTLIB_MODULE_DEBUG: plot_with_matplotlib_actual checking _shared_plot_data. Is None? {_shared_plot_data is None}")
    if _shared_plot_data is None:
        print("Matplotlib module: No data available to plot.")
        return

    # Unpack the data stored in _shared_plot_data
    (raw_x, raw_y), (interp_x, interp_y), (fit_x, fit_y), \
    fit_label, plot_title, x_label, y_label = _shared_plot_data

    try:
        plt.figure()
        if raw_x is not None and raw_y is not None and len(raw_x) > 0:
            plt.plot(raw_x, raw_y, label="Raw Data", marker='o', linestyle='None', markersize=4)
        if interp_x is not None and interp_y is not None and len(interp_x) > 0:
            plt.plot(interp_x, interp_y, label="Interpolated", linestyle='--')
        if fit_x is not None and fit_y is not None and len(fit_x) > 0:
            plt.plot(fit_x, fit_y, label=fit_label)

        plt.title(plot_title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.legend()
        plt.grid(True)
        print("Matplotlib module: Showing plot...") # Debug
        plt.show()
        print("Matplotlib module: Plot window closed.") # Debug
    except Exception as e:
        print(f"Matplotlib module: Error plotting with Matplotlib: {e}")
