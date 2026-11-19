# IndoorPos 室内定位课程实验

本项目整理了室内定位课程中的实验数据、定位程序和绘图脚本，包含距离交会定位、行人航迹推算（PDR）、信号强度指纹定位，以及安卓手机传感器数据分析。

程序主要使用 C++ 和 Python 编写。C++ 用于距离交会和 PDR 计算，Python 用于指纹定位、数据处理和结果绘图。

## 1. 实验内容

| 实验模块 | 主要内容 | 使用语言 |
| --- | --- | --- |
| 距离交会定位 | 根据基站坐标和测距数据，计算无人机、小车及人员的位置 | C++ |
| 行人航迹推算 | 姿态计算、航向估计、步伐检测及行走轨迹推算 | C++、Python |
| 信号强度指纹定位 | 建立 RSS 指纹库，通过相似度匹配计算位置并评价误差 | Python |
| 手机传感器分析 | 读取陀螺仪、加速度计、磁强计和 WiFi 数据，导出 CSV 并绘图 | Python |

## 2. 项目结构

下面列出了主要目录和文件，部分数据文件、图片及运行结果未逐一展开。

```text
IndoorPos/
├── README.md
├── .gitignore
├── .vscode/                         # 本地 VS Code 配置
│
├── src/
│   ├── DistanceIntersection/        # 距离交会定位
│   │   ├── UAVPosition.cpp
│   │   ├── UWBPosition.cpp
│   │   ├── ClassroomPosition.cpp
│   │   └── StudentPosition.cpp
│   │
│   ├── PDR/                         # 行人航迹推算
│   │   ├── PDRPosition.cpp
│   │   ├── plot_pdr_signals.py
│   │   ├── plot_pdr_tracks.py
│   │   └── pdr_output/              # 计算结果和图片
│   │
│   ├── Fingerprint/                 # 信号强度指纹定位
│   │   ├── run_fingerprint.py       # 统一运行入口
│   │   ├── fingerprint_io.py
│   │   ├── fingerprint_algorithm.py
│   │   ├── plot_fingerprint_tracks.py
│   │   ├── plot_fingerprint_errors.py
│   │   └── fingerprint_output/      # 指纹库、定位结果和图片
│   │
│   ├── Sensors/                     # 手机传感器数据分析
│   │   ├── run_sensors.py           # 统一运行入口
│   │   ├── sensor_config.py
│   │   ├── sensor_io.py
│   │   ├── plot_sensors.py
│   │   ├── plot_wifi.py
│   │   └── sensor_output/           # CSV 和图片
│   │
│   └── output/                      # C++ 编译生成的 exe 文件
│
├── 数据-距离交会/
│   ├── 数据1-无人机-Ultrasonic/
│   ├── 数据2-小车-UWB/
│   ├── 数据3-教室-Ultrasonic/
│   └── 数据4-课上同学采集-Ultrasonic/
│       ├── 无遮挡数据/
│       └── 有遮挡数据/
│
├── 数据-行人航迹推算/
│   ├── sensors_matrix.txt
│   └── pos_reference.txt
│
├── 数据-信号强度指纹识别/
│   ├── database.data
│   ├── rp_loc.txt
│   └── test1_with_ref.data
│
├── android-data-collection/
│   ├── 数据采集软件.md
│   ├── sensor-data-collection.apk
│   ├── DataConvert/                 # 配套 MATLAB 数据转换程序
│   └── SenDa2/
│       └── 20150401055443/
│           ├── sensors.txt
│           ├── wifi.txt
│           ├── GPS.txt
│           └── GPS.kml
│
└── PPT/                             # 课程课件
```

运行后，程序会在对应位置生成或更新结果文件。

## 3. 运行环境

| 项目 | 说明 |
| --- | --- |
| 操作系统 | 以下命令以 Windows PowerShell 为例 |
| C++ 编译器 | 支持 C++17 的 g++，例如较新版 MinGW-w64 |
| Python | 建议使用 Python 3.10 或更新版本 |
| Python 第三方库 | NumPy、Matplotlib |
| 编辑器 | 可使用 VS Code |

C++ 程序使用了 `<filesystem>`，编译时需要启用 C++17。

先在终端检查环境：

```powershell
g++ --version
python --version
```

安装 Python 依赖：

```powershell
python -m pip install numpy matplotlib
```


## 4. 运行前的准备

在 VS Code 中打开整个 `IndoorPos` 文件夹，并让终端停留在项目根目录。

例如：

```powershell
cd D:\Course\IndoorPos
```

如果项目保存在其他位置，将上面的路径替换为自己的路径。

首次编译前，创建 exe 输出目录：

```powershell
New-Item -ItemType Directory -Force .\src\output
```

所有 C++ 源文件都是独立程序，各自包含 `main()`，需要分别编译。

下面的运行命令都从项目根目录执行。距离交会程序使用相对路径读取数据，运行时尤其需要注意当前工作目录。

## 5. 距离交会定位

### 5.1 程序说明

| 源文件 | 数据目录 | 主要计算方法 |
| --- | --- | --- |
| `UAVPosition.cpp` | `数据1-无人机-Ultrasonic` | 利用已知高程进行二维迭代最小二乘定位 |
| `UWBPosition.cpp` | `数据2-小车-UWB` | 利用多个基站的测距进行三维迭代最小二乘定位 |
| `ClassroomPosition.cpp` | `数据3-教室-Ultrasonic` | 根据有效测距进行二维定位，并与参考位置比较 |
| `StudentPosition.cpp` | `数据4-课上同学采集-Ultrasonic` | 分别处理无遮挡和有遮挡数据，进行二维定位及误差评价 |

各数据集的详细格式见对应目录中的 `数据格式.md` 或 `readme.md`。

### 5.2 编译

在项目根目录执行：

```powershell
g++ -std=c++17 -Wall -Wextra -O2 .\src\DistanceIntersection\UAVPosition.cpp -o .\src\output\UAVPosition.exe

g++ -std=c++17 -Wall -Wextra -O2 .\src\DistanceIntersection\UWBPosition.cpp -o .\src\output\UWBPosition.exe

g++ -std=c++17 -Wall -Wextra -O2 .\src\DistanceIntersection\ClassroomPosition.cpp -o .\src\output\ClassroomPosition.exe

g++ -std=c++17 -Wall -Wextra -O2 .\src\DistanceIntersection\StudentPosition.cpp -o .\src\output\StudentPosition.exe
```

### 5.3 运行

根据需要运行对应程序：

```powershell
.\src\output\UAVPosition.exe
.\src\output\UWBPosition.exe
.\src\output\ClassroomPosition.exe
.\src\output\StudentPosition.exe
```

`StudentPosition.exe` 会依次处理无遮挡和有遮挡两个场景。

### 5.4 输出文件

当前距离交会程序将计算结果保存在对应的数据目录中。

| 程序 | 输出文件 |
| --- | --- |
| 无人机定位 | `数据-距离交会/数据1-无人机-Ultrasonic/result_cpp.csv` |
| UWB 标签 2 定位 | `数据-距离交会/数据2-小车-UWB/result_tag_2_cpp.csv` |
| UWB 标签 3 定位 | `数据-距离交会/数据2-小车-UWB/result_tag_3_cpp.csv` |
| 教室定位 | `数据-距离交会/数据3-教室-Ultrasonic/result_classroom_cpp.csv` |
| 同学采集数据定位 | 无遮挡、有遮挡目录中各自的 `result_student_cpp.csv` |

结果中的 `range_rms_m` 表示测距拟合残差的均方根，不能直接当作位置误差。

当前 UWB 程序没有读取 `true_position_tag_2.txt` 和 `true_position_tag_3.txt` 进行误差统计。

## 6. 行人航迹推算（PDR）

### 6.1 功能

PDR 程序读取 `数据-行人航迹推算/sensors_matrix.txt`，完成以下处理：

1. 读取并转换传感器数据单位。
2. 根据加速度计算横滚角和俯仰角。
3. 使用滑动平均平滑姿态角。
4. 对陀螺仪和磁强计数据进行调平。
5. 计算磁强计航向、陀螺积分航向和补偿后的陀螺航向。
6. 根据加速度模的波谷检测步伐。
7. 使用固定步长推算三条行走轨迹。

### 6.2 编译与计算

```powershell
g++ -std=c++17 -Wall -Wextra -O2 .\src\PDR\PDRPosition.cpp -o .\src\output\PDRPosition.exe

.\src\output\PDRPosition.exe
```

计算结果保存在：

```text
src/PDR/pdr_output/
├── pdr_result.csv
└── pdr_parameters.csv
```

### 6.3 绘图

先完成 C++ 计算，再运行：

```powershell
python .\src\PDR\plot_pdr_signals.py
python .\src\PDR\plot_pdr_tracks.py
```

第一个脚本显示图窗后，需要关闭图窗，程序才会结束，然后再运行第二个脚本。

图片保存在：

```text
src/PDR/pdr_output/figures/
```

| 绘图脚本 | 图片内容 |
| --- | --- |
| `plot_pdr_signals.py` | 传感器数据、原始和平滑姿态角、航向、步伐检测等 |
| `plot_pdr_tracks.py` | 补偿前后的行走轨迹对比 |

### 6.4 主要参数

参数位于 `src/PDR/PDRPosition.cpp` 顶部。

| 参数 | 当前值 | 含义 |
| --- | --- | --- |
| `WINDOW_SECONDS` | 1.0 s | 姿态角滑动平均窗口 |
| `STEP_THRESHOLD` | 9.2 m/s² | 步伐检测的加速度模波谷阈值 |
| `MIN_STEP_INTERVAL` | 0.30 s | 相邻步伐的最小时间间隔 |
| `STEP_LENGTH` | 0.70 m | 固定步长 |
| `GZ_CORRECTION` | 0.25°/s，代码中转换为 rad/s | 原始 Z 轴角速度的附加补偿量 |

这些参数针对当前实验数据设置，更换数据后可能需要调整。

其中角速度补偿量是试验值，并非通过传感器标定得到的零偏。

当前程序未使用 `pos_reference.txt` 进行参考轨迹误差评价。

## 7. 信号强度指纹定位

### 7.1 输入数据

数据目录：

```text
数据-信号强度指纹识别/
```

| 文件 | 内容 |
| --- | --- |
| `rp_loc.txt` | 参考点编号及三个坐标 |
| `database.data` | 参考点编号及 30 个热点的 RSS 观测 |
| `test1_with_ref.data` | 时间、30 个 RSS 观测及三个参考坐标 |

### 7.2 处理方法

程序先对每个参考点的有效 RSS 求平均，建立指纹库。

定位时，将测试 RSS 与各参考点比较，根据共同有效热点的 RSS 差异和覆盖率计算相似度，选择得分最高的若干个参考点，再对坐标进行加权平均。

| 项目 | 当前设置 |
| --- | --- |
| 热点数量 | 30 |
| 缺失 RSS 标志 | `-110` |
| 邻居数量 `K` | 3 |
| 最少共同有效热点数量 `MIN_COMMON` | 3 |

`-110` 不参与 RSS 平均或共同热点比较。

相似度得分是用于匹配和加权的指标，不是严格的概率。

测试数据中的参考坐标只用于定位完成后的误差评价，不参与位置计算。

### 7.3 一次运行完成计算和绘图

```powershell
python .\src\Fingerprint\run_fingerprint.py
```

也可以在 VS Code 中打开 `run_fingerprint.py`，使用“运行 Python 文件”。

统一入口会完成建库、定位、误差统计和绘图，不需要逐个运行其他模块。

### 7.4 脚本分工

| 文件 | 作用 |
| --- | --- |
| `run_fingerprint.py` | 组织整个处理流程 |
| `fingerprint_io.py` | 数据读取、结果保存和目录配置 |
| `fingerprint_algorithm.py` | 建立指纹库和匹配定位 |
| `plot_fingerprint_tracks.py` | 参考点分布及轨迹对比绘图 |
| `plot_fingerprint_errors.py` | 定位误差及误差累计分布绘图 |

### 7.5 输出结果

```text
src/Fingerprint/fingerprint_output/
├── fingerprint_database.csv
├── fingerprint_result.csv
└── figures/
    ├── 01_reference_points.png
    ├── 02_reference_track.png
    ├── 03_position_compare.png
    ├── 04_position_errors.png
    └── 05_error_cdf.png
```

终端会输出成功定位数量、平均水平误差、水平 RMSE 和最大水平误差。

## 8. 手机传感器数据分析

### 8.1 输入数据

默认读取：

```text
android-data-collection/SenDa2/20150401055443/
```

当前 Python 程序主要处理：

| 文件 | 处理内容 |
| --- | --- |
| `sensors.txt` | 陀螺仪、加速度计和磁强计三轴数据 |
| `wifi.txt` | WiFi 热点、信号强度及扫描记录 |

数据采集软件的使用方法见：

```text
android-data-collection/数据采集软件.md
```

`DataConvert/` 是配套 MATLAB 转换程序，运行这里的 Python 分析脚本不需要先运行 MATLAB。

### 8.2 一次运行完成导出和绘图

```powershell
python .\src\Sensors\run_sensors.py
```

也可以直接在 VS Code 中运行 `run_sensors.py`。

### 8.3 脚本分工

| 文件 | 作用 |
| --- | --- |
| `run_sensors.py` | 统一运行入口 |
| `sensor_config.py` | 数据目录、采集批次和绘图参数 |
| `sensor_io.py` | 读取传感器及 WiFi 数据，保存 CSV |
| `plot_sensors.py` | 绘制三种传感器的三轴曲线 |
| `plot_wifi.py` | 绘制 WiFi 信号强度曲线及首次扫描结果 |

更换采集数据时，修改 `sensor_config.py`：

```python
SESSION_NAME = "20150401055443"
```

该名称需要与 `SenDa2` 中实际存在的采集文件夹一致。

其他常用参数：

```python
# 绘制出现次数最多的 5 个 WiFi 热点
WIFI_TOP_N = 5

# 显示全部传感器数据
SENSOR_TIME_RANGE = None

# 如果只显示前 30 秒，可改为：
# SENSOR_TIME_RANGE = (0, 30)
```

### 8.4 输出结果

默认输出到：

```text
src/Sensors/sensor_output/20150401055443/
```

| 类型 | 输出内容 |
| --- | --- |
| 传感器 CSV | `gyroscope.csv`、`accelerometer.csv`、`magnetometer.csv` |
| WiFi CSV | `wifi_records.csv`、`wifi_selected.csv`、`wifi_scan_counts.csv` |
| 传感器图片 | 陀螺仪、加速度计、磁强计三轴曲线 |
| WiFi 图片 | 选定热点的信号强度时间序列、首次扫描的信号强度柱状图 |

导出的陀螺仪单位为 rad/s，加速度计单位为 m/s²，磁强计单位为 μT。

当前模块用于原始数据整理和绘图，没有执行传感器插值、姿态解算或定位计算。

## 9. 输出目录汇总

| 内容 | 保存位置 |
| --- | --- |
| C++ 可执行文件 | `src/output/` |
| 距离交会定位结果 | 对应的距离交会数据目录 |
| PDR 计算结果 | `src/PDR/pdr_output/` |
| PDR 图片 | `src/PDR/pdr_output/figures/` |
| 指纹定位结果 | `src/Fingerprint/fingerprint_output/` |
| 指纹定位图片 | `src/Fingerprint/fingerprint_output/figures/` |
| 手机传感器分析结果 | `src/Sensors/sensor_output/采集文件夹名称/` |

## 10. 说明

本项目用于室内定位课程学习和实验，各模块的参数、坐标约定及数据格式以当前代码和对应数据说明为准。

不同实验使用的坐标原点和数据单位可能不同，比较结果前需要先确认其定义。

本项目尚未提供运行全部实验的统一入口，请根据需要选择对应模块。