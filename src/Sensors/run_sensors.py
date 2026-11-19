import sys

# 不生成这些自编模块的 __pycache__ 缓存
sys.dont_write_bytecode = True

import matplotlib.pyplot as plt

from sensor_config import (
    DATA_DIR,
    OUTPUT_DIR,
    WIFI_TOP_N,
    SENSOR_TIME_RANGE
)

from sensor_io import (
    read_sensors,
    read_wifi,
    save_csv
)

from plot_sensors import plot_sensors
from plot_wifi import plot_wifi


def main():
    # 检查配置
    if WIFI_TOP_N < 1:
        raise ValueError("WIFI_TOP_N 至少为 1")

    if SENSOR_TIME_RANGE is not None:
        if SENSOR_TIME_RANGE[0] >= SENSOR_TIME_RANGE[1]:
            raise ValueError(
                "时间范围的开始值必须小于结束值"
            )

    # Windows 常用中文字体
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "DejaVu Sans"
    ]

    plt.rcParams["axes.unicode_minus"] = False

    # 第一步：读取数据
    print("数据目录：", DATA_DIR)

    data = read_sensors(DATA_DIR / "sensors.txt")
    wifi = read_wifi(DATA_DIR / "wifi.txt")

    # 第二步：创建输出文件夹
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 第三步：保存三种传感器的数据
    settings = [
        (1, "gyroscope.csv", "rad_s"),
        (2, "accelerometer.csv", "m_s2"),
        (3, "magnetometer.csv", "uT")
    ]

    for kind, filename, unit in settings:
        print(f"{filename}：{len(data[kind])} 条")

        save_csv(
            OUTPUT_DIR / filename,
            [
                "time_s",
                "x_" + unit,
                "y_" + unit,
                "z_" + unit
            ],
            data[kind]
        )

    # 保存全部 WiFi 记录
    save_csv(
        OUTPUT_DIR / "wifi_records.csv",
        ["time_s", "mac", "rss_dbm", "ssid"],
        wifi
    )

    # 第四步：绘制传感器曲线
    print("正在绘制传感器曲线……")
    plot_sensors(data, OUTPUT_DIR)

    # 第五步：绘制 WiFi 图
    print("正在绘制 WiFi 图……")
    plot_wifi(wifi, OUTPUT_DIR)

    print("全部处理完成，输出目录：", OUTPUT_DIR)

    # 所有图片保存之后，再统一显示
    plt.show()


if __name__ == "__main__":
    main()