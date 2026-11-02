"""Reads the original data files without changing or interpreting them."""

import hashlib
from pathlib import Path

from openpyxl import load_workbook

from app.business.models import RawCell, RawData, RawSheetRow

HOTEL_EXCEL = "international_names_with_rooms_1000.xlsx"
HOTEL_CSV = "international_names_with_rooms_1000.csv"
BAR_EXCEL = "drinks_menu_with_sales.xlsx"
REPLACEMENT_CHARACTER = "�"


def _read_sheet(path: Path) -> tuple[list[RawSheetRow], list[RawCell]]:
    """Complete rows become records. Values in incomplete rows are returned as loose cells."""
    workbook = load_workbook(path, data_only=True)
    try:
        sheet = workbook.worksheets[0]
        rows = sheet.iter_rows()
        headers = [cell.value for cell in next(rows)]
        records = []
        stray_cells = []
        for row in rows:
            filled = [cell for cell in row if cell.value is not None]
            if not filled:
                continue
            values = [cell.value for cell in row[: len(headers)]]
            if len(filled) == len(headers) and all(value is not None for value in values):
                records.append(RawSheetRow(row_number=row[0].row, values=dict(zip(headers, values))))
            else:
                stray_cells.extend(RawCell(reference=cell.coordinate, value=cell.value) for cell in filled)
        return records, stray_cells
    finally:
        workbook.close()


def read_raw_data(directory: Path) -> RawData:
    hotel_path = directory / HOTEL_EXCEL
    csv_path = directory / HOTEL_CSV
    bar_path = directory / BAR_EXCEL
    hotel_rows, hotel_stray_cells = _read_sheet(hotel_path)
    bar_rows, bar_stray_cells = _read_sheet(bar_path)
    csv_bytes = csv_path.read_bytes()
    return RawData(
        hotel_source=HOTEL_EXCEL,
        hotel_rows=hotel_rows,
        hotel_stray_cells=hotel_stray_cells,
        bar_source=BAR_EXCEL,
        bar_rows=bar_rows,
        bar_stray_cells=bar_stray_cells,
        hotel_csv_source=HOTEL_CSV,
        hotel_csv_replacement_characters=csv_bytes.decode("utf-8").count(REPLACEMENT_CHARACTER),
        checksums={
            HOTEL_EXCEL: hashlib.sha256(hotel_path.read_bytes()).hexdigest(),
            HOTEL_CSV: hashlib.sha256(csv_bytes).hexdigest(),
            BAR_EXCEL: hashlib.sha256(bar_path.read_bytes()).hexdigest(),
        },
    )
