from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# 本脚本也保存于 IndoorPos/src/PDR/ 中。
root = Path(__file__).resolve().parents[2]
folder = root / "src" / "PDR" / "pdr_output"

result_file = folder / "pdr_result.csv"
parameter_file = folder / "pdr_parameters.csv"

if not result_file.exists() or not parameter_file.exists():
    raise SystemExit("请先编译并运行 PDRPosition.cpp，再运行绘图脚本。")

data = np.genfromtxt(
    result_file, delimiter=",", names=True, encoding="utf-8"
)

parameters = np.genfromtxt(
    parameter_file, delimiter=",", names=True, encoding="utf-8"
)

correction = np.degrees(float(parameters["gz_correction_rad_s"]))

figure_folder = folder / "figures"
figure_folder.mkdir(parents=True, exist_ok=True)

# 两张图采用相同的坐标范围，方便比较。
all_east = np.concatenate([
    data["east_mag_m"],
    data["east_gyro_m"],
    data["east_corrected_m"]
])

all_north = np.concatenate([
    data["north_mag_m"],
    data["north_gyro_m"],
    data["north_corrected_m"]
])

east_limits = (all_east.min() - 10, all_east.max() + 10)
north_limits = (all_north.min() - 10, all_north.max() + 10)

for corrected in [False, True]:
    if corrected:
        east_column = "east_corrected_m"
        north_column = "north_corrected_m"

        label = "Corrected gyroscope PDR"
        title = f"PDR: gz correction = {correction:+.3f} deg/s"
        name = "09_track_after.png"
    else:
        east_column = "east_gyro_m"
        north_column = "north_gyro_m"

        label = "Gyroscope PDR"
        title = "PDR: before correction"
        name = "08_track_before.png"

    fig, ax = plt.subplots(figsize=(8, 7))

    ax.plot(
        data["east_mag_m"], data["north_mag_m"],
        "b-", linewidth=1, label="Magnetometer PDR"
    )

    ax.plot(
        data[east_column], data[north_column],
        "r--", linewidth=1, label=label
    )

    # 标出起点
    ax.plot(
        0, 0,
        "ko", markersize=6, label="Start"
    )

    # 标出磁强计轨迹的终点
    ax.plot(
        data["east_mag_m"][-1],
        data["north_mag_m"][-1],
        "bs", markersize=6, label="Magnetometer end"
    )

    # 标出陀螺轨迹的终点
    ax.plot(
        data[east_column][-1],
        data[north_column][-1],
        "rs", markersize=6, label="Gyroscope end"
    )

    ax.set_title(title)
    ax.set_xlabel("East (m)")
    ax.set_ylabel("North (m)")

    ax.set_xlim(east_limits)
    ax.set_ylim(north_limits)

    # 保证横纵方向上 1 米的显示长度相同
    ax.set_aspect("equal", adjustable="box")

    ax.grid(True)
    ax.legend(fontsize=9)

    fig.tight_layout()
    fig.savefig(
        figure_folder / name,
        dpi=180,
        bbox_inches="tight"
    )

# 末点距起点的距离不等于定位误差，
# 除非已知真实终点就是起点。
print("各条轨迹的末点坐标，单位：m")

for name, east_column, north_column in [
    ("Magnetometer", "east_mag_m", "north_mag_m"),
    ("Gyroscope", "east_gyro_m", "north_gyro_m"),
    ("Corrected gyroscope", "east_corrected_m", "north_corrected_m")
]:
    east = data[east_column][-1]
    north = data[north_column][-1]

    print(f"{name}: East = {east:.3f}, North = {north:.3f}")

print("图片保存到：", figure_folder)

plt.show()