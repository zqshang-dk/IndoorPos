import matplotlib.pyplot as plt

from sensor_config import WIFI_TOP_N
from sensor_io import save_csv


def plot_wifi(records, output_dir):
    # 按扫描时间整理数据
    # scans[时间][MAC] = [RSS总和, 观测次数]
    scans = {}

    for time, mac, rss, name in records:
        if time not in scans:
            scans[time] = {}

        if mac not in scans[time]:
            scans[time][mac] = [0.0, 0]

        scans[time][mac][0] += rss
        scans[time][mac][1] += 1

    times = sorted(scans)

    # 同一时间、同一 MAC 若有重复记录，取平均值
    for time in times:
        for mac in scans[time]:
            total, count = scans[time][mac]
            scans[time][mac] = total / count

    # 统计每个 MAC 出现于多少次扫描
    appearances = {}

    for time in times:
        for mac in scans[time]:
            appearances[mac] = appearances.get(mac, 0) + 1

    # 按出现次数从多到少排序
    mac_list = sorted(
        appearances,
        key=appearances.get,
        reverse=True
    )

    selected = mac_list[:WIFI_TOP_N]

    print(f"WiFi 扫描次数：{len(times)}")
    print(f"不同 MAC 地址数量：{len(mac_list)}")
    print("用于 RSS 曲线的 MAC：")

    for mac in selected:
        print(
            f"  {mac}：出现在 {appearances[mac]} 次扫描中"
        )

    # 第一张图：热点数量 + 选定热点的 RSS
    fig, axes = plt.subplots(
        2, 1,
        figsize=(12, 8),
        sharex=True
    )

    counts = [len(scans[time]) for time in times]

    axes[0].plot(
        times,
        counts,
        color="black",
        linewidth=1
    )

    axes[0].set_title("每次扫描发现的 WiFi 热点数量")
    axes[0].set_ylabel("不同 MAC 数量")
    axes[0].grid(True, alpha=0.3)

    # 整理选定热点的 RSS 数据
    selected_rows = []

    for time in times:
        row = [time]

        for mac in selected:
            # 没有扫描到时使用 nan
            value = scans[time].get(mac, float("nan"))
            row.append(value)

        selected_rows.append(row)

    # 每个热点绘制一条曲线
    for j, mac in enumerate(selected):
        rss_values = [
            row[j + 1] for row in selected_rows
        ]

        axes[1].plot(
            times,
            rss_values,
            marker=".",
            markersize=3,
            linewidth=0.9,
            label=mac
        )

    axes[1].set_title(
        "出现次数最多的热点：RSS 随时间变化"
    )
    axes[1].set_xlabel("wifi.txt 记录时间 (s)")
    axes[1].set_ylabel("RSS (dBm)")
    axes[1].grid(True, alpha=0.3)

    # 将图例放在图外，避免挡住曲线
    axes[1].legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        fontsize=9
    )

    fig.tight_layout()
    fig.savefig(
        output_dir / "04_wifi_time_series.png",
        dpi=180
    )

    # 保存选定热点的 RSS
    save_csv(
        output_dir / "wifi_selected.csv",
        ["time_s"] + selected,
        selected_rows
    )

    # 保存每次扫描的热点数量
    scan_rows = []

    for i in range(len(times)):
        scan_rows.append([times[i], counts[i]])

    save_csv(
        output_dir / "wifi_scan_counts.csv",
        ["time_s", "ap_count"],
        scan_rows
    )

    # 第二张图：第一次扫描中信号最强的 10 个热点
    first_scan = scans[times[0]]

    strongest = sorted(
        first_scan,
        key=first_scan.get,
        reverse=True
    )[:10]

    values = [first_scan[mac] for mac in strongest]

    fig, ax = plt.subplots(figsize=(11, 5))

    y = list(range(len(strongest)))

    ax.barh(y, values, color="steelblue")
    ax.set_yticks(y)
    ax.set_yticklabels(strongest)
    ax.invert_yaxis()

    ax.set_title(
        f"首次扫描的最强热点，时间 {times[0]:.3f} s"
    )
    ax.set_xlabel(
        "RSS (dBm)，越接近 0 表示信号越强"
    )
    ax.set_ylabel("MAC 地址")

    ax.grid(True, axis="x", alpha=0.3)

    # 在柱状图上标注 RSS 数值
    for i, value in enumerate(values):
        ax.text(
            value + 1,
            i,
            f"{value:.1f}",
            va="center"
        )

    fig.tight_layout()
    fig.savefig(
        output_dir / "05_wifi_first_scan.png",
        dpi=180
    )