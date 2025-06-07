import dearpygui.dearpygui as dpg

from app.classes.app_theme import Theme

ALL_THEMES = [theme.display_name for theme in Theme]

_classic_theme_id: int | str | None = None


def apply_theme(theme: Theme):
    global _classic_theme_id
    print(f"Applying theme: {theme}")

    if theme == Theme.DARK:
        if _classic_theme_id and dpg.does_item_exist(_classic_theme_id):
            dpg.delete_item(_classic_theme_id)
            _classic_theme_id = None
        dpg.bind_theme(0)
        print("Theme applied: DARK")

    elif theme == Theme.LIGHT:
        if _classic_theme_id and dpg.does_item_exist(_classic_theme_id):
            dpg.delete_item(_classic_theme_id)
            _classic_theme_id = None

        with dpg.theme() as classic_theme_object:
            _classic_theme_id = classic_theme_object

            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 0, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (216, 216, 216, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (216, 216, 216, 255))
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (216, 216, 216, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (128, 128, 128, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 255, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (230, 230, 230, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (200, 200, 200, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (180, 180, 180, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (150, 150, 150, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (180, 180, 180, 150))
                dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (216, 216, 216, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (216, 216, 216, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (128, 128, 128, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (100, 100, 100, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (70, 70, 70, 255))
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (0, 0, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (128, 128, 128, 255))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (70, 70, 70, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (240, 240, 240, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (190, 190, 190, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (160, 160, 160, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (200, 200, 200, 255))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (170, 170, 170, 255))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (140, 140, 140, 255))
                dpg.add_theme_color(dpg.mvPlotCol_PlotBg, (255, 255, 255, 255), category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_LegendBg, (235, 235, 235, 200), category=dpg.mvThemeCat_Plots)

                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 0, category=dpg.mvThemeCat_Core)

        dpg.bind_theme(_classic_theme_id)
        print("Theme applied: LIGHT")

