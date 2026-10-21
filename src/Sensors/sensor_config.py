from pathlib import Path

# 这几个脚本放在 IndoorPos/src/Sensors 文件夹中
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent

# 更换采集数据时，修改这里的文件夹名称
SESSION_NAME = "20150401055443"

DATA_DIR = (
    PROJECT_DIR
    / "android-data-collection"
    / "SenDa2"
    / SESSION_NAME
)

# 结果保存在源码文件夹下面
OUTPUT_DIR = SCRIPT_DIR / "sensor_output" / SESSION_NAME

# 绘制出现次数最多的几个 WiFi 热点
WIFI_TOP_N = 5

# None 表示显示全部时间
# 如果只想看前 30 秒，改为 (0, 30)
SENSOR_TIME_RANGE = None