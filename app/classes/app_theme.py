from enum import Enum

class Theme(Enum):
    DARK = ("dark_theme", "Dark Theme")
    LIGHT = ("light_theme", "Light Theme")

    def __init__(self, code_name, display_name):
        self.code_name = code_name
        self.display_name = display_name

    def __str__(self):
        return self.display_name
