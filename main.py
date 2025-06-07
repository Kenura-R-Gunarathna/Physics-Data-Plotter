import sys
import os
import dearpygui.dearpygui as dpg

from app.gui import setup_gui

def main():

    log_path = os.path.join(os.path.dirname(__file__), 'output.log')
    sys.stdout = open(log_path, 'w')
    sys.stderr = sys.stdout

    dpg.create_context()
    setup_gui()
    dpg.set_primary_window("MainAppWindow", True)
    dpg.create_viewport(title="Physics Data Plotter (PDP)", width=1000, height=700)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
