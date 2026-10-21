from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# 本脚本保存于 IndoorPos/src/PDR/ 中。
# 根据脚本位置找项目根目录，不依赖终端的当前目录。
root = Path(__file__).resolve().parents[2]
folder = root / "src" / "PDR" / "pdr_output"

result_file = folder / "pdr_result.csv"
parameter_file = folder / "pdr_parameters.csv"

if not result_file.exists() or not parameter_file.exists():
    raise SystemExit("请先编译并运行 PDRPosition.cpp，再运行绘图脚本。")

# names=True 表示用 CSV 第一行作为列名。
data = np.genfromtxt(
    result_file, delimiter=",", names=True, encoding="utf-8"
)

parameters = np.genfromtxt(
    parameter_file, delimiter=",", names=True, encoding="utf-8"
)

time = data["time_s"] - data["time_s"][0]

threshold = float(parameters["valley_threshold_mps2"])
correction = np.degrees(float(parameters["gz_correction_rad_s"]))
window = float(parameters["window_s"])

figure_folder = folder / "figures"
figure_folder.mkdir(parents=True, exist_ok=True)


def save_figure(fig, name):
    fig.tight_layout()
    fig.savefig(figure_folder / name, dpi=180, bbox_inches="tight")


def draw_heading(ax, column, label, color, style="-"):
    angle = np.degrees(data[column]).copy()

    # 不连接跨越 -180/180 度边界的两个点，
    # 避免画出假的竖直线。
    jumps = np.abs(np.diff(angle)) > 180
    angle[np.where(jumps)[0] + 1] = np.nan

    ax.plot(
        time, angle,
        color=color,
        linestyle=style,
        linewidth=0.8,
        label=label
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Heading (deg)")
    ax.set_ylim(-180, 180)
    ax.grid(True)
    ax.legend()


# 1. 三轴陀螺、加速度计、磁强计
fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)

gyro_columns = ["gx_rad_s", "gy_rad_s", "gz_rad_s"]
acc_columns = ["ax_mps2", "ay_mps2", "az_mps2"]
mag_columns = ["mx_T", "my_T", "mz_T"]

colors = ["blue", "green", "red"]
labels = ["X", "Y", "Z"]

for k in range(3):
    axes[0].plot(
        time, np.degrees(data[gyro_columns[k]]),
        color=colors[k],
        linewidth=0.5,
        label=labels[k]
    )

    axes[1].plot(
        time, data[acc_columns[k]],
        color=colors[k],
        linewidth=0.5,
        label=labels[k]
    )

    # C++ 输出单位为 T。
    # 绘图转换为 Gauss：1 T = 10000 Gauss。
    axes[2].plot(
        time, data[mag_columns[k]] * 10000,
        color=colors[k],
        linewidth=0.5,
        label=labels[k]
    )

axes[0].set_title("Gyroscope")
axes[0].set_ylabel("deg/s")

axes[1].set_title("Accelerometer")
axes[1].set_ylabel("m/s^2")

axes[2].set_title("Magnetometer")
axes[2].set_ylabel("Gauss")
axes[2].set_xlabel("Time (s)")

for ax in axes:
    ax.grid(True)
    ax.legend(loc="upper right")

save_figure(fig, "01_sensor_data.png")


# 2、3. 平滑前后的水平姿态角，分别保存
for smooth in [False, True]:
    if smooth:
        roll_column = "roll_smooth_rad"
        pitch_column = "pitch_smooth_rad"
        title = f"Horizontal angles: {window:g} s moving average"
        name = "03_attitude_smooth.png"
    else:
        roll_column = "roll_rad"
        pitch_column = "pitch_rad"
        title = "Horizontal angles: without smoothing"
        name = "02_attitude_raw.png"

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(
        time, np.degrees(data[roll_column]),
        "b-", linewidth=0.7, label="Roll"
    )

    ax.plot(
        time, np.degrees(data[pitch_column]),
        "r--", linewidth=0.7, label="Pitch"
    )

    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Angle (deg)")
    ax.grid(True)
    ax.legend()

    save_figure(fig, name)


# 4. 单独画磁强计航向
fig, ax = plt.subplots(figsize=(10, 4))

draw_heading(ax, "heading_mag_rad", "Magnetometer", "blue")

ax.set_title("Heading from magnetometer")
save_figure(fig, "04_heading_mag.png")


# 5. 磁强计航向与未补偿的陀螺航向
fig, ax = plt.subplots(figsize=(10, 4))

draw_heading(ax, "heading_mag_rad", "Magnetometer", "blue")
draw_heading(ax, "heading_gyro_rad", "Gyroscope", "red", "--")

ax.set_title("Heading comparison: before correction")
save_figure(fig, "05_heading_before.png")


# 6. 脚步探测：全时段和前 10 秒局部放大
step = data["is_step"] == 1
fig, axes = plt.subplots(2, 1, figsize=(11, 7))

for ax in axes:
    ax.plot(
        time, data["acc_norm_mps2"],
        "b-", linewidth=0.6, label="Acceleration norm"
    )

    ax.plot(
        time[step], data["acc_norm_mps2"][step],
        "r+", markersize=5, label="Step"
    )

    ax.axhline(
        threshold,
        color="gray",
        linestyle="--",
        label=f"Threshold = {threshold:g}"
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Acceleration (m/s^2)")
    ax.grid(True)
    ax.legend()

axes[0].set_title(f"Detected steps: {np.count_nonzero(step)}")
axes[1].set_title("First 10 seconds")
axes[1].set_xlim(0, min(10, time[-1]))

save_figure(fig, "06_step_detection.png")


# 7. 补偿后的陀螺航向与磁强计航向
fig, ax = plt.subplots(figsize=(10, 4))

draw_heading(ax, "heading_mag_rad", "Magnetometer", "blue")

draw_heading(
    ax, "heading_corrected_rad",
    "Corrected gyroscope", "red", "--"
)

ax.set_title(
    f"Heading comparison: gz correction = {correction:+.3f} deg/s"
)

save_figure(fig, "07_heading_after.png")

print("图片保存到：", figure_folder)

plt.show()