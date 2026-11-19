#数据读取文件
import csv
import math


def read_sensors(file):
    # 每条记录保存为：[时间, X, Y, Z]
    data = {
        1: [],       # 陀螺
        2: [],       # 加速度计
        3: []        # 磁强计
    }

    start_time = None
    other_count = 0

    with open(file, "r", encoding="utf-8-sig") as f:
        for line_number, line in enumerate(f, start=1):
            # 跳过空行
            if not line.strip():
                continue

            parts = line.split()

            if len(parts) != 5:
                raise ValueError(
                    f"sensors.txt 第 {line_number} 行不是 5 列"
                )

            kind = int(parts[0])
            values = [float(value) for value in parts[1:]]

            if not all(math.isfinite(value) for value in values):
                raise ValueError(
                    f"sensors.txt 第 {line_number} 行有无效数字"
                )

            time = values[0]

            if start_time is None or time < start_time:
                start_time = time

            # 本次图片中的三种传感器
            if kind in data:
                if data[kind] and time < data[kind][-1][0]:
                    raise ValueError(
                        f"sensors.txt 第 {line_number} 行时间倒退"
                    )

                data[kind].append(values)
            else:
                other_count += 1

    if start_time is None:
        raise ValueError("sensors.txt 没有数据")

    for kind in data:
        for row in data[kind]:
            # 三种传感器使用同一个时间起点
            # 保留各传感器之间原本存在的时间差
            row[0] -= start_time

            # 原始陀螺单位是 deg/s
            # 转换成课件图中的 rad/s
            if kind == 1:
                for j in range(1, 4):
                    row[j] = row[j] * math.pi / 180.0

    print(f"未绘制的其他传感器记录：{other_count} 条")

    return data


def read_wifi(file):
    records = []

    with open(file, "r", encoding="utf-8-sig") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue

            # 最多分成 4 部分
            # 第 4 部分保留整个热点名称，包括名称中的空格
            parts = line.strip().split(maxsplit=3)

            if len(parts) < 3:
                raise ValueError(
                    f"wifi.txt 第 {line_number} 行少于 3 列"
                )

            time = float(parts[0])
            mac = parts[1].lower()
            rss = float(parts[2])

            if len(parts) == 4:
                name = parts[3]
            else:
                name = ""

            if not math.isfinite(time) or not math.isfinite(rss):
                raise ValueError(
                    f"wifi.txt 第 {line_number} 行有无效数字"
                )

            if records and time < records[-1][0]:
                raise ValueError(
                    f"wifi.txt 第 {line_number} 行时间倒退"
                )

            records.append([time, mac, rss, name])

    if not records:
        raise ValueError("wifi.txt 没有数据")

    return records


def save_csv(file, header, rows):
    # utf-8-sig 方便 Windows Excel 正确显示中文热点名称
    with open(file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(header)
        writer.writerows(rows)