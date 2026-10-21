import matplotlib.pyplot as plt

from sensor_config import SENSOR_TIME_RANGE


def plot_sensors(data, output_dir):
    settings = [
        (
            1,
            "陀螺三轴角速度",
            "角速度 (rad/s)",
            "01_gyroscope.png"
        ),
        (
            2,
            "加速度计三轴输出",
            "加速度计输出 (m/s²)",
            "02_accelerometer.png"
        ),
        (
            3,
            "磁强计三轴输出",
            "磁场 (μT)",
            "03_magnetometer.png"
        )
    ]

    colors = ["red", "green", "blue"]
    labels = ["X轴", "Y轴", "Z轴"]

    for kind, title, unit, filename in settings:
        rows = data[kind]

        if not rows:
            print(f"没有{title}数据，跳过此图")
            continue

        # 如果设置了时间范围，只绘制这个范围内的数据
        if SENSOR_TIME_RANGE is not None:
            begin, end = SENSOR_TIME_RANGE

            rows = [
                row for row in rows
                if begin <= row[0] <= end
            ]

        if not rows:
            print(f"{title}在所选时间段内没有数据")
            continue

        time = [row[0] for row in rows]

        fig, ax = plt.subplots(figsize=(11, 4.5))

        # 分别绘制 X、Y、Z 三个轴
        for j in range(3):
            values = [row[j + 1] for row in rows]

            ax.plot(
                time,
                values,
                color=colors[j],
                linewidth=0.9,
                label=labels[j]
            )

        ax.set_title(title)
        ax.set_xlabel("相对传感器记录起点的时间 (s)")
        ax.set_ylabel(unit)

        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper right")

        fig.tight_layout()
        fig.savefig(output_dir / filename, dpi=180)

    # 此处不调用 plt.show()
    # 由主程序最后统一显示全部图片