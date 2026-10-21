from fingerprint_io import OUTPUT_DIR
import numpy as np
import matplotlib.pyplot as plt

folder = OUTPUT_DIR

database_file = folder / "fingerprint_database.csv"
result_file = folder / "fingerprint_result.csv"

if not database_file.exists() or not result_file.exists():
    raise SystemExit("请先运行 run_fingerprint.py。")

database = np.atleast_1d(np.genfromtxt(
    database_file,
    delimiter=",",
    names=True,
    encoding="utf-8"
))

result = np.atleast_1d(np.genfromtxt(
    result_file,
    delimiter=",",
    names=True,
    encoding="utf-8"
))

figure_folder = folder / "figures"
figure_folder.mkdir(parents=True, exist_ok=True)

ref_e = result["ref_east_m"]
ref_n = result["ref_north_m"]

east = result["east_m"].copy()
north = result["north_m"].copy()

# 定位失败时，轨迹在对应位置断开。
failed = result["success"] != 1
east[failed] = np.nan
north[failed] = np.nan


def mark_reference_ends(ax):
    ax.plot(ref_e[0], ref_n[0], "ko", markersize=5)

    distance = np.hypot(
        ref_e[-1] - ref_e[0],
        ref_n[-1] - ref_n[0]
    )

    if distance < 1e-8:
        ax.annotate(
            "Start / End",
            (ref_e[0], ref_n[0]),
            xytext=(10, -18),
            textcoords="offset points"
        )
    else:
        ax.annotate(
            "Start",
            (ref_e[0], ref_n[0]),
            xytext=(8, 8),
            textcoords="offset points"
        )

        ax.plot(ref_e[-1], ref_n[-1], "ks", markersize=5)

        ax.annotate(
            "End",
            (ref_e[-1], ref_n[-1]),
            xytext=(8, 8),
            textcoords="offset points"
        )


def save_figure(fig, ax, title, name):
    ax.set_title(title)
    ax.set_xlabel("East (m)")
    ax.set_ylabel("North (m)")

    # 横纵坐标中 1 米的显示长度相同。
    ax.set_aspect("equal", adjustable="box")
    ax.margins(0.15)

    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(
        figure_folder / name,
        dpi=180,
        bbox_inches="tight"
    )


# 1. 参考点分布。
fig, ax = plt.subplots(figsize=(7, 6))

ax.plot(
    database["east_m"],
    database["north_m"],
    "b*",
    markersize=5,
    label="Reference points"
)

save_figure(
    fig, ax,
    "Reference point locations",
    "01_reference_points.png"
)


# 2. 参考轨迹。
fig, ax = plt.subplots(figsize=(7, 6))

ax.plot(
    ref_e, ref_n,
    "g+-",
    linewidth=1,
    markersize=5,
    label="Reference"
)

mark_reference_ends(ax)

save_figure(
    fig, ax,
    "Reference trajectory",
    "02_reference_track.png"
)


# 3. 定位轨迹与参考轨迹对比。
fig, ax = plt.subplots(figsize=(7, 6))

ax.plot(
    ref_e, ref_n,
    "g+-",
    linewidth=1,
    markersize=5,
    label="Reference"
)

ax.plot(
    east, north,
    "r.-",
    linewidth=1,
    markersize=5,
    label="WKNN"
)

mark_reference_ends(ax)

save_figure(
    fig, ax,
    "Position solution and reference",
    "03_position_compare.png"
)

print("图片保存到：", figure_folder)

# plt.show()