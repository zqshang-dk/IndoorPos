from pathlib import Path
import csv
import math

# 五个脚本都放在 IndoorPos/src/Fingerprint 中。
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent

DATA_DIR = PROJECT_DIR / "数据-信号强度指纹识别"
OUTPUT_DIR = SCRIPT_DIR / "fingerprint_output"


def read_table(path, columns):
    """读取空格分隔的数字，并检查每行列数。"""
    rows = []

    with open(path, "r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                row = [float(value) for value in line.split()]
            except ValueError:
                raise ValueError(
                    f"{path.name} 第 {line_number} 行含非数字"
                )

            if len(row) != columns:
                raise ValueError(
                    f"{path.name} 第 {line_number} 行列数错误"
                )

            if not all(math.isfinite(value) for value in row):
                raise ValueError(
                    f"{path.name} 第 {line_number} 行含无效数值"
                )

            rows.append(row)

    if not rows:
        raise ValueError(f"{path.name} 没有数据")

    return rows


def save_csv(name, header, rows):
    """把计算结果保存到输出目录。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(
        OUTPUT_DIR / name,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)