from fingerprint_io import OUTPUT_DIR
import numpy as np
import matplotlib.pyplot as plt

folder = OUTPUT_DIR
result_file = folder / "fingerprint_result.csv"

if not result_file.exists():
    raise SystemExit("请先运行 run_fingerprint.py。")

data = np.atleast_1d(np.genfromtxt(
    result_file,
    delimiter=",",
    names=True,
    encoding="utf-8"
))

figure_folder = folder / "figures"
figure_folder.mkdir(parents=True, exist_ok=True)

# 只对成功定位的时刻统计误差。
valid = (data["success"] == 1) & np.isfinite(data["error_2d_m"])
count = int(np.count_nonzero(valid))

print(f"成功定位：{count}/{len(data)}")

if count == 0:
    raise SystemExit("没有成功定位的数据，无法统计误差。")

time = data["time_s"]

error_e = data["error_e_m"].copy()
error_n = data["error_n_m"].copy()
error_2d = data["error_2d_m"].copy()

# 定位失败的时刻保留空缺。
error_e[~valid] = np.nan
error_n[~valid] = np.nan
error_2d[~valid] = np.nan

errors = error_2d[valid]

mean_error = np.mean(errors)
rmse = np.sqrt(np.mean(errors ** 2))
p95 = np.percentile(errors, 95)

print(f"平均水平误差：{mean_error:.4f} m")
print(f"水平 RMSE：{rmse:.4f} m")
print(f"最大水平误差：{np.max(errors):.4f} m")
print(f"95% 分位误差：{p95:.4f} m")


# 4. 误差随时间变化。
fig, axes = plt.subplots(
    2, 1,
    figsize=(10, 7),
    sharex=True
)

axes[0].plot(time, error_e, "b.-", label="East error")
axes[0].plot(time, error_n, "r.-", label="North error")

axes[0].axhline(
    0,
    color="gray",
    linestyle="--"
)

axes[0].set_title("Coordinate errors")
axes[0].set_ylabel("Error (m)")

axes[1].plot(
    time, error_2d,
    "k.-",
    label="Horizontal error"
)

axes[1].axhline(
    rmse,
    color="red",
    linestyle="--",
    label=f"RMSE = {rmse:.3f} m"
)

axes[1].set_title("Horizontal positioning error")
axes[1].set_xlabel("Time (s)")
axes[1].set_ylabel("Error (m)")

for ax in axes:
    ax.grid(True)
    ax.legend()

fig.tight_layout()
fig.savefig(
    figure_folder / "04_position_errors.png",
    dpi=180,
    bbox_inches="tight"
)


# 5. 误差的经验累计分布。
# 纵轴表示误差不超过横轴数值的样本比例。
sorted_errors = np.sort(errors)
probability = np.arange(1, count + 1) / count

fig, ax = plt.subplots(figsize=(7, 5))

ax.step(
    np.r_[0.0, sorted_errors],
    np.r_[0.0, probability],
    where="post",
    color="blue",
    label="Empirical CDF"
)

ax.set_title(
    f"Horizontal error CDF: {count}/{len(data)} successful epochs"
)

ax.set_xlabel("Horizontal error (m)")
ax.set_ylabel("Cumulative probability")

ax.set_xlim(left=0)
ax.set_ylim(0, 1.02)

ax.grid(True)
ax.legend()

fig.tight_layout()
fig.savefig(
    figure_folder / "05_error_cdf.png",
    dpi=180,
    bbox_inches="tight"
)

print("图片保存到：", figure_folder)

# plt.show()