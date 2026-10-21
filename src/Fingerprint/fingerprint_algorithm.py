import math

AP_COUNT = 30
MISSING_RSS = -110.0


def build_database(locations, training):
    """按参考点编号，对每个热点的有效 RSS 求平均。"""
    points = []
    id_to_index = {}

    # 先读取参考点编号和坐标。
    for row in locations:
        if row[0] < 1 or not row[0].is_integer():
            raise ValueError("参考点编号必须为正整数")

        point_id = int(row[0])

        if point_id in id_to_index:
            raise ValueError(f"参考点编号重复：{point_id}")

        point = {
            "id": point_id,
            "pos": row[1:4],
            "samples": 0,
            "sum": [0.0] * AP_COUNT,
            "count": [0] * AP_COUNT,
            "mean": [MISSING_RSS] * AP_COUNT,
        }

        # 记录“参考点编号”对应的列表下标。
        id_to_index[point_id] = len(points)
        points.append(point)

    # 累加每个参考点、每个热点的有效 RSS。
    for row in training:
        if row[0] not in id_to_index:
            raise ValueError(
                f"建库数据中的参考点编号不存在：{row[0]}"
            )

        point = points[id_to_index[row[0]]]
        point["samples"] += 1

        for j in range(AP_COUNT):
            rss = row[j + 1]

            if rss != MISSING_RSS:
                point["sum"][j] += rss
                point["count"][j] += 1

    # 求平均，-110 不参与计算。
    for point in points:
        if point["samples"] == 0:
            raise ValueError(
                f'参考点 {point["id"]} 没有建库数据'
            )

        for j in range(AP_COUNT):
            count = point["count"][j]

            if count > 0:
                point["mean"][j] = point["sum"][j] / count

            # count 为 0 时，均值保持为 -110。

    return points


def locate(rss, points, k=3, min_common=3):
    """只使用 RSS 定位，不接收参考坐标。"""
    if k < 1 or min_common < 1:
        raise ValueError("k 和 min_common 必须大于零")

    # 统计测试观测中的有效热点数量。
    valid_aps = sum(value != MISSING_RSS for value in rss)

    if valid_aps < min_common:
        return None, valid_aps, 0

    candidates = []

    for index, point in enumerate(points):
        square_sum = 0.0
        common = 0

        for j in range(AP_COUNT):
            # 只比较双方都有有效观测的热点。
            if rss[j] == MISSING_RSS or point["count"][j] == 0:
                continue

            difference = rss[j] - point["mean"][j]
            square_sum += difference ** 2
            common += 1

        if common < min_common:
            continue

        # RSS 均方根差，避免维数不同导致直接比较不公平。
        rms = math.sqrt(square_sum / common)

        # 共同有效热点占测试有效热点的比例。
        coverage = common / valid_aps

        # 差异越小、覆盖率越高，分数越大。
        # 这是相似度分数，不是严格的概率。
        score = coverage / (1.0 + rms)

        candidates.append((score, index))

    if not candidates:
        return None, valid_aps, 0

    # 元组第一项是分数，按分数从大到小排序。
    # 分数完全相同时，按参考点数组下标排序。
    candidates.sort(key=lambda item: (-item[0], item[1]))

    # 不足 k 个时，切片会返回所有实际可用的候选点。
    selected = candidates[:k]

    position = [0.0, 0.0, 0.0]
    weight_sum = 0.0

    for score, index in selected:
        weight_sum += score

        for j in range(3):
            position[j] += score * points[index]["pos"][j]

    for j in range(3):
        position[j] /= weight_sum

    return position, valid_aps, len(selected)