import math

from fingerprint_io import (
    DATA_DIR,
    OUTPUT_DIR,
    read_table,
    save_csv,
)

from fingerprint_algorithm import (
    AP_COUNT,
    build_database,
    locate,
)

K = 3
MIN_COMMON = 3


def main():
    # 参考点编号 + 3 个坐标。
    locations = read_table(DATA_DIR / "rp_loc.txt", 4)

    # 参考点编号 + 30 个 RSS。
    training = read_table(
        DATA_DIR / "database.data",
        AP_COUNT + 1
    )

    # 时间 + 30 个 RSS + 3 个参考坐标。
    tests = read_table(
        DATA_DIR / "test1_with_ref.data",
        AP_COUNT + 4
    )

    for i in range(1, len(tests)):
        if tests[i][0] <= tests[i - 1][0]:
            raise ValueError("测试数据的时间必须递增")

    points = build_database(locations, training)

    # 保存指纹库，列名与原来的 C++ 输出一致。
    database_header = [
        "rp_id", "east_m", "north_m", "z_m", "samples"
    ]

    database_header += [
        f"mean_ap{j}" for j in range(1, AP_COUNT + 1)
    ]

    database_header += [
        f"count_ap{j}" for j in range(1, AP_COUNT + 1)
    ]

    database_rows = []

    for point in points:
        row = [point["id"]] + point["pos"] + [point["samples"]]
        row += point["mean"] + point["count"]
        database_rows.append(row)

    result_header = [
        "time_s", "east_m", "north_m", "z_m",
        "ref_east_m", "ref_north_m", "ref_z_m",
        "error_e_m", "error_n_m", "error_2d_m",
        "valid_aps", "neighbors_used", "success",
    ]

    results = []
    errors = []

    for row in tests:
        time = row[0]

        # Python 下标从 0 开始。
        # 第 2～31 列，即 30 个 RSS。
        rss = row[1:31]

        # 定位函数只接收 RSS，不接收坐标真值。
        position, valid_aps, used = locate(
            rss, points, K, MIN_COMMON
        )

        # 最后 3 列参考坐标，只用于误差评价。
        reference = row[31:34]

        if position is None:
            position = [math.nan, math.nan, math.nan]
            error_e = error_n = error_2d = math.nan
            success = 0
        else:
            error_e = position[0] - reference[0]
            error_n = position[1] - reference[1]
            error_2d = math.hypot(error_e, error_n)

            errors.append(error_2d)
            success = 1

        result = [time] + position + reference

        result += [
            error_e,
            error_n,
            error_2d,
            valid_aps,
            used,
            success,
        ]

        results.append(result)

    save_csv(
        "fingerprint_database.csv",
        database_header,
        database_rows
    )

    save_csv(
        "fingerprint_result.csv",
        result_header,
        results
    )

    print(f"建库数据：{len(training)} 行")
    print(f"参考点：{len(points)} 个，K = {K}")
    print(f"成功定位：{len(errors)}/{len(tests)}")

    if errors:
        mean_error = sum(errors) / len(errors)

        rmse = math.sqrt(
            sum(value ** 2 for value in errors) / len(errors)
        )

        print(f"平均水平误差：{mean_error:.4f} m")
        print(f"水平 RMSE：{rmse:.4f} m")
        print(f"最大水平误差：{max(errors):.4f} m")

    print("结果保存到：", OUTPUT_DIR)


if __name__ == "__main__":
    import runpy
    from pathlib import Path
    import matplotlib.pyplot as plt

    # 当前主程序所在的文件夹
    script_folder = Path(__file__).resolve().parent

    # 第一步：完成指纹定位，并保存计算结果
    print("第一步：计算指纹定位结果")
    main()

    # 第二步：运行轨迹绘图脚本
    print("\n第二步：绘制参考点分布和定位轨迹")
    runpy.run_path(
        str(script_folder / "plot_fingerprint_tracks.py"),
        run_name="__main__"
    )

    # 第三步：运行误差绘图脚本
    print("\n第三步：绘制定位误差和误差累计分布")
    runpy.run_path(
        str(script_folder / "plot_fingerprint_errors.py"),
        run_name="__main__"
    )

    print("\n全部计算完成，结果和图片已经保存。")

    # 所有图片生成后，统一显示
    plt.show()