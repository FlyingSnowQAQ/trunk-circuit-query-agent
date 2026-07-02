"""
.xls 旧格式文件解析器
使用 xlrd 库读取 .xls 文件
"""
import xlrd


def parse_xls(file_path: str, encoding: str = None) -> dict:
    """
    解析 .xls 文件
    返回: { sheet_name: [ [row_values], ... ] }
    """
    try:
        if encoding:
            wb = xlrd.open_workbook(file_path, encoding_override=encoding)
        else:
            wb = xlrd.open_workbook(file_path)

        result = {}
        for sheet_name in wb.sheet_names():
            ws = wb.sheet_by_name(sheet_name)
            rows = []
            for row_idx in range(ws.nrows):
                row = []
                for col_idx in range(ws.ncols):
                    cell = ws.cell(row_idx, col_idx)
                    # 统一转为字符串
                    if cell.ctype == xlrd.XL_CELL_EMPTY:
                        row.append(None)
                    elif cell.ctype == xlrd.XL_CELL_NUMBER:
                        val = cell.value
                        if val == int(val):
                            row.append(str(int(val)))
                        else:
                            row.append(str(val))
                    else:
                        row.append(str(cell.value).strip())
                rows.append(row)
            result[sheet_name] = rows

        wb.release_resources()
        return result

    except Exception as e:
        raise RuntimeError(f"解析 .xls 文件失败 [{file_path}]: {e}")


def parse_xls_summary(file_path: str, encoding: str = None) -> list:
    """
    解析 .xls 文件并返回所有sheet的平坦行列表
    每行: { "sheet": sheet_name, "row_data": [values], "row_idx": idx }
    """
    sheets = parse_xls(file_path, encoding)
    records = []
    for sheet_name, rows in sheets.items():
        for idx, row in enumerate(rows):
            records.append({
                "sheet": sheet_name,
                "row_idx": idx,
                "row_data": row,
            })
    return records
