import dearpygui.dearpygui as dpg
import threading

from app.excel_reader import ExcelReader
from app.data_processing import process_data, FIT_MODELS
from app.theme import apply_theme, ALL_THEMES, Theme
from app.matplotlib import plot_with_matplotlib_actual, set_latest_plot_data

# --- Dictionary for p0 hints ---
P0_HINTS = {
    "Exponential": "a, b (e.g., 1e-9, 10)",
    "Linear": "m, c (e.g., 1.0, 0.5) - Optional", # Often not needed for linear
    "Logarithmic": "a, b for a*ln(x)+b (e.g., 1.0, 0.1)",
    "Power": "a, b, c for a*x^b+c (e.g., 1.0, 2.0, 0.0)",
    "Logistic": "L, k, x0 (e.g., max_y, 1.0, mid_x)",
    "Polynomial": "N/A (uses polyfit)",
    "Moving Average": "N/A (uses SavGol filter)",
    "None": "N/A"
}

def theme_selection_callback(sender, app_data, user_data):
    selected_theme_display_name: str = dpg.get_value(sender)
    selected_theme = next((t for t in Theme if t.display_name == selected_theme_display_name), None)
    if selected_theme:
        apply_theme(selected_theme)


def toggle_crosshair_callback(sender, app_data, user_data):
    plot_tag = user_data
    enable_crosshairs = dpg.get_value(sender)
    dpg.configure_item(plot_tag, crosshairs=enable_crosshairs)


def open_matplotlib_plot_callback(sender, app_data, user_data):
    print("GUI: open_matplotlib_plot_callback triggered")

    if dpg.does_item_exist("status_text"):
        dpg.set_value("status_text", "Opening Matplotlib plot...")

    print("GUI: About to start Matplotlib thread.")
    plot_thread = threading.Thread(target=plot_with_matplotlib_actual, daemon=True)
    plot_thread.start()
    print("GUI: Matplotlib thread started.")


def fit_model_selection_changed_callback(sender, app_data, user_data):
    selected_model = dpg.get_value(sender)

    # --- Visibility for model-specific parameters ---
    show_poly_group = selected_model == "Polynomial"
    show_mov_avg_group = selected_model == "Moving Average"

    if dpg.does_item_exist("poly_order_input_group"):
        dpg.configure_item("poly_order_input_group", show=show_poly_group)
    if dpg.does_item_exist("mov_avg_period_input_group"):
        dpg.configure_item("mov_avg_period_input_group", show=show_mov_avg_group)

    # --- Visibility and Hint for common advanced curve_fit options (p0, maxfev) ---
    models_using_curve_fit_adv_opts = ["Exponential", "Linear", "Logarithmic", "Power", "Logistic"]
    show_advanced_fit_opts = selected_model in models_using_curve_fit_adv_opts

    if dpg.does_item_exist("advanced_fit_options_group"):
        dpg.configure_item("advanced_fit_options_group", show=show_advanced_fit_opts)

    # --- Update p0 hint text ---
    if dpg.does_item_exist("p0_tooltip_text_item"):  # Check if the text item inside the tooltip exists
        if show_advanced_fit_opts:
            tooltip_hint = P0_HINTS.get(selected_model, "Enter comma-separated initial guesses for model parameters.")
            dpg.set_value("p0_tooltip_text_item", tooltip_hint)
            # Ensure the tooltip's parent (e.g., p0_input_text) is visible if tooltip should show
            if dpg.does_item_exist("p0_input_text_tooltip"):  # Check if tooltip item itself exists
                parent_of_tooltip = dpg.get_item_parent("p0_input_text_tooltip")
                if parent_of_tooltip and dpg.is_item_shown(parent_of_tooltip):
                    pass  # Tooltip will show when parent is hovered
        else:
            dpg.set_value("p0_tooltip_text_item", "")  # Clear tooltip text if not applicable


def update_plot_callback(sender, app_data, user_data):
    # ... (initializations and Excel reading as before) ...
    plot_title_text = "Y vs X"
    x_label_text = "X Axis (Unit)"
    y_label_text = "Y Axis (Unit)"

    # set_latest_plot_data(None) # For matplotlib
    if dpg.does_item_exist("matplotlib_button"):
        dpg.disable_item("matplotlib_button")
    if dpg.does_item_exist("status_text"):
        dpg.set_value("status_text", "Processing...")

    try:
        x_cell = dpg.get_value("x_cell")
        y_cell = dpg.get_value("y_cell")
        title_cell = dpg.get_value("title_cell")
        x_label_cell = dpg.get_value("x_label_cell")
        y_label_cell = dpg.get_value("y_label_cell")
        ending_row = int(dpg.get_value("ending_row"))
        num_samples = int(dpg.get_value("num_samples"))

        selected_fit_model = dpg.get_value("fit_model_combo")
        fit_parameters = {}  # Initialize

        # Model-specific parameters
        if selected_fit_model == "Polynomial":
            fit_parameters['poly_order'] = int(dpg.get_value("poly_order_input"))
        elif selected_fit_model == "Moving Average":
            fit_parameters['mov_avg_period'] = int(dpg.get_value("mov_avg_period_input"))
            if dpg.does_item_exist("mov_avg_poly_order_input"):  # Check if the field exists and is visible
                if dpg.is_item_shown("mov_avg_poly_order_input"):  # Redundant if group visibility is managed
                    fit_parameters['mov_avg_poly_order'] = int(dpg.get_value("mov_avg_poly_order_input"))

        # --- Read common advanced curve_fit options (p0, maxfev) ---
        # Only try to read them if the advanced_fit_options_group is shown
        if dpg.does_item_exist("advanced_fit_options_group") and dpg.is_item_shown("advanced_fit_options_group"):
            p0_text = dpg.get_value("p0_input_text").strip()  # New tag for p0 text input
            if p0_text:  # If user provided something
                try:
                    # Parse comma-separated string into a list of floats
                    p0_values = [float(p.strip()) for p in p0_text.split(',') if p.strip()]
                    if p0_values:  # Ensure not empty list after stripping
                        fit_parameters['p0'] = p0_values
                except ValueError:
                    raise ValueError(
                        f"Invalid format for p0: '{p0_text}'. Use comma-separated numbers (e.g., 1.0, 2e-5, 3).")

            maxfev_val = dpg.get_value("maxfev_input_int")  # New tag for maxfev int input
            if maxfev_val > 0:  # Or some other sensible check, maybe it can be None/0 to use default
                fit_parameters['maxfev'] = maxfev_val
        # --- End of reading advanced options ---

        # ... (Excel reading logic as before) ...
        reader = ExcelReader()
        if not reader.excel or not reader.wb or not reader.sheet:  # Check ExcelReader init
            msg = "Error: Excel not ready. Open data file and make it active."
            print(msg)
            if dpg.does_item_exist("status_text"): dpg.set_value("status_text", msg)
            return

        x_data = reader.read_column(x_cell, ending_row)
        y_data = reader.read_column(y_cell, ending_row)
        plot_title_text = reader.read_cell(title_cell) or plot_title_text
        x_label_text = reader.read_cell(x_label_cell) or x_label_text
        y_label_text = reader.read_cell(y_label_cell) or y_label_text

    except ValueError as ve:
        msg = f"Invalid input: {ve}"
        print(msg)
        if dpg.does_item_exist("status_text"): dpg.set_value("status_text", msg)
        return
    except Exception as e:
        msg = f"Error during input processing: {e}"
        print(msg)
        if dpg.does_item_exist("status_text"): dpg.set_value("status_text", msg)
        return

    # Call the updated process_data
    processed = process_data(x_data, y_data, num_samples,
                             fit_model_name=selected_fit_model,
                             fit_params=fit_parameters)

    # ... (rest of update_plot_callback: processing results, enabling buttons, DPG plotting) ...
    if processed[0] is None or not isinstance(processed[0], tuple) or processed[1][0] is None:
        msg = f"Data processing/fitting issue: {processed[3] if len(processed) == 4 else 'Unknown error in processing'}"
        print(msg)
        if dpg.does_item_exist("status_text"): dpg.set_value("status_text", msg)
        set_latest_plot_data(None)
        if dpg.does_item_exist("matplotlib_button"):
            dpg.disable_item("matplotlib_button")
        return

    (raw_x, raw_y), (interp_x, interp_y), (fit_x, fit_y), fit_label = processed

    current_plot_data_tuple = (
        (raw_x, raw_y), (interp_x, interp_y), (fit_x, fit_y),
        fit_label, plot_title_text, x_label_text, y_label_text
    )
    set_latest_plot_data(current_plot_data_tuple)
    if dpg.does_item_exist("matplotlib_button"):
        dpg.enable_item("matplotlib_button")
    if dpg.does_item_exist("status_text"):
        dpg.set_value("status_text", f"Plot updated with {selected_fit_model} fit.")

    # DPG Plotting
    dpg.delete_item("y_axis", children_only=True)
    dpg.set_item_label("plot", plot_title_text)
    dpg.set_item_label("x_axis", x_label_text)
    dpg.set_item_label("y_axis", y_label_text)

    try:
        if raw_x is not None and raw_y is not None and raw_x.size > 0 and raw_y.size > 0 and len(raw_x) == len(raw_y):
            dpg.add_line_series(raw_x.tolist(), raw_y.tolist(), label="Raw Data", parent="y_axis")
        if interp_x is not None and interp_y is not None and interp_x.size > 0 and interp_y.size > 0 and len(
                interp_x) == len(interp_y):
            dpg.add_line_series(interp_x.tolist(), interp_y.tolist(), label="Interpolated", parent="y_axis")

        if fit_x is not None and fit_y is not None and fit_x.size > 0 and fit_y.size > 0 and len(fit_x) == len(fit_y):
            dpg.add_line_series(fit_x.tolist(), fit_y.tolist(), label=fit_label, parent="y_axis")
        elif fit_label:
            dpg.add_line_series([0], [0], label=fit_label, show=False, parent="y_axis")
    except Exception as e:
        msg = f"Error during DPG plotting: {e}"
        print(msg)
        if dpg.does_item_exist("status_text"): dpg.set_value("status_text", msg)

    dpg.fit_axis_data("x_axis")
    dpg.fit_axis_data("y_axis")


def setup_gui():
    with dpg.window(label="Physics Data Plotter", tag="MainAppWindow", width=1000, height=600, no_close=True,
                    no_title_bar=True):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=300, height=-1, border=True, tag="settings_panel"):
                # ... (Data Source & Range collapsible header - unchanged) ...
                with dpg.collapsing_header(label="Data Source & Range", default_open=True):
                    dpg.add_input_text(label="Plot Title Cell", default_value="C1", tag="title_cell", width=120)
                    dpg.add_separator()
                    dpg.add_input_text(label="X Label Cell", default_value="A1", tag="x_label_cell", width=120)
                    dpg.add_input_text(label="X Data Start Cell", default_value="A2", tag="x_cell", width=120)
                    dpg.add_separator()
                    dpg.add_input_text(label="Y Label Cell", default_value="B1", tag="y_label_cell", width=120)
                    dpg.add_input_text(label="Y Data Start Cell", default_value="B2", tag="y_cell", width=120)
                    dpg.add_separator()
                    dpg.add_input_int(label="Data Ending Row", default_value=16, tag="ending_row", width=120,
                                      min_value=1, step=1)
                    dpg.add_input_int(label="Interpolation Samples", default_value=100, tag="num_samples", width=120,
                                      min_value=10, step=10)

                with dpg.collapsing_header(label="Fitting Model", default_open=True):
                    dpg.add_combo(items=FIT_MODELS, label="Model", tag="fit_model_combo",
                                  default_value="Exponential", width=160,
                                  callback=fit_model_selection_changed_callback)

                    # --- Model-Specific Parameters ---
                    with dpg.group(tag="poly_order_input_group", show=False, indent=10):
                        dpg.add_input_int(label="Polynomial Order", tag="poly_order_input", default_value=2, width=-1,
                                          min_value=0, max_value=10, step=1)
                    with dpg.group(tag="mov_avg_period_input_group", show=False, indent=10):
                        dpg.add_input_int(label="MA Period", tag="mov_avg_period_input", default_value=5, width=-1,
                                          min_value=3, step=2)
                        dpg.add_input_int(label="MA Poly Order", tag="mov_avg_poly_order_input", default_value=2,
                                          width=-1, min_value=0, step=1)

                    # --- Common Advanced Fit Options for curve_fit ---
                    with dpg.group(tag="advanced_fit_options_group", show=False):
                        dpg.add_input_text(label="Initial Guesses", tag="p0_input_text", width=160, hint="param1, param2, ...")
                        with dpg.tooltip(parent="p0_input_text", tag="p0_input_text_tooltip"):  # Create the tooltip item
                            dpg.add_text("Parameter details will appear here.", tag="p0_tooltip_text_item", wrap=250)

                        dpg.add_input_int(label="Max Func Evals", default_value=5000, tag="maxfev_input_int", width=160, min_value=0, step=1000)
                        with dpg.tooltip(parent="maxfev_input_int", tag="maxfev_tooltip"):
                            dpg.add_text("Maximum number of calls to the function by curve_fit. 0 or blank uses SciPy's default.")

                # ... (Plot Options, Appearance, Update Plot button, Status text - as before) ...
                with dpg.collapsing_header(label="Plot Options", default_open=False):
                    dpg.add_checkbox(label="Enable Crosshairs", tag="crosshair_checkbox", default_value=False,
                                     callback=toggle_crosshair_callback, user_data="plot")
                    dpg.add_separator()
                    dpg.add_button(label="Open in Matplotlib", tag="matplotlib_button",
                                   callback=open_matplotlib_plot_callback, enabled=False)

                with dpg.collapsing_header(label="Appearance", default_open=False):
                    dpg.add_combo(label="Theme", items=ALL_THEMES, default_value=Theme.DARK.display_name,
                                  # Assuming ALL_THEMES and Theme are from your theme.py
                                  callback=theme_selection_callback, tag="theme_selector", width=150)

                dpg.add_button(label="Update Plot", callback=update_plot_callback, width=-1, height=30)
                dpg.add_separator()
                dpg.add_text("Status: Idle", tag="status_text", wrap=280)

            # ... (Plot Area - unchanged) ...
            with dpg.child_window(width=-1, height=-1, border=True):
                with dpg.plot(label="Y vs X", height=-1, width=-1, tag="plot", crosshairs=False):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="X Axis (Unit)", tag="x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Y Axis (Unit)", tag="y_axis")


    if dpg.is_dearpygui_running():
        initial_fit_model = dpg.get_value("fit_model_combo")
        fit_model_selection_changed_callback("fit_model_combo", initial_fit_model, None)
    else:
        def _initial_setup_callback(user_data=None):
            if dpg.does_item_exist("fit_model_combo"):
                initial_fit_model = dpg.get_value("fit_model_combo")
                fit_model_selection_changed_callback("fit_model_combo", initial_fit_model, None)

        dpg.set_frame_callback(1, _initial_setup_callback, user_data=None)