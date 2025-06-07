import win32com.client
import pythoncom

class ExcelReader:
    def __init__(self):
        pythoncom.CoInitialize()
        self.excel = win32com.client.Dispatch("Excel.Application")
        self.wb = self.excel.ActiveWorkbook
        self.sheet = self.wb.ActiveSheet

    def read_column(self, start_cell, num_points):
        col = ''.join(filter(str.isalpha, start_cell))
        end_cell = f"{col}{num_points}"
        data_range = self.sheet.Range(f"{start_cell}:{end_cell}")
        return [cell.Value for cell in data_range]

    def read_cell(self, cell):
        return self.sheet.Range(cell).Value
