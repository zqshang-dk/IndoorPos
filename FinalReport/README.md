# 室内定位课程实验报告

## 文件

- `main.tex`：报告正文，使用 XeLaTeX 与 `ctexart`。
- `analysis.py`：独立复算/统计和绘图脚本。读取 `D:\Course\IndoorPos` 下的原始数据及项目已有程序输出；新增文件仅写入本目录。
- `figures/`：脚本生成的报告图片。
- `figures/*.pdf`：LaTeX 引用的矢量图；同名 PNG 用于快速预览。
- `results/`：脚本生成的定位结果、时间戳匹配结果与误差 CSV。
- `main.pdf`：编译生成的报告。

## 复现

需要 Python 3、NumPy 和 Matplotlib：

```powershell
python analysis.py
xelatex main.tex
xelatex main.tex
```

脚本重新计算 RSS 指纹建库、KNN 定位及 K 参数敏感性；对教室超声、PDR、UWB 的既有 C++ 输出进行参考轨迹时间对齐、统计和绘图；并从 Android `SenDa2/20150401055443` 会话绘制惯性与 Wi-Fi 采样情况。教室、PDR、UWB 三项均为存档输出的后处理，不是本轮重新执行 C++ 主程序的结果。UWB 只按估计与真值共有时间戳统计 tag 2，并将平面误差与垂向系统偏差分开报告。Android 样例没有并入定位精度统计。所有新增文件只写在 `FinalReport` 内。

运行后重点查看 `fingerprint_k_sensitivity.csv`、`uwb_tag2_time_aligned.csv`、`pdr_step_errors.csv` 和 `classroom_distance_result.csv`。实例报告中的 DOP 曲线没有对应的可核验 DOP 序列，因此未生成；实例中的软件截图和原理示意不作为本项目实测数据图重绘。图表逐张对应见报告表“实例报告图表与本报告图表对照清单”。

该报告未复用实例 PDF 的个人信息、实验数字或图片。作者和学号留空，提交前请自行填写。
