#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cmath>
#include <iomanip>
#include <filesystem>

using namespace std;
namespace fs = std::filesystem;

const double PI = 3.141592653589793;
const double DEG = PI / 180.0;

const double WINDOW_SECONDS = 1.0;
const double STEP_THRESHOLD = 9.2;
const double MIN_STEP_INTERVAL = 0.30;
const double STEP_LENGTH = 0.70;

// 加到原始 Z 轴角速度上的补偿量，不是直接加到航向上。
// +0.25 度/秒只是本作业的试验值，并非已经标定的零偏。
const double GZ_CORRECTION = 0.25 * DEG;

struct Sample {
    double time = 0;

    double g[3] = {};       // 原始陀螺，rad/s
    double a[3] = {};       // 加速度，m/s^2
    double m[3] = {};       // 磁场，T

    double gh[3] = {};      // 调平后的陀螺
    double mh[3] = {};      // 调平后的磁场

    double acc = 0;

    double roll = 0;
    double pitch = 0;

    double rollSmooth = 0;
    double pitchSmooth = 0;

    double wzCorrected = 0;

    double headingMag = 0;
    double headingGyro = 0;
    double headingCorrected = 0;

    int step = 0;

    // 下标 0：磁强计
    // 下标 1：原始陀螺
    // 下标 2：补偿后陀螺
    double east[3] = {};
    double north[3] = {};
};

// 把角度限制到 [-pi, pi)
double wrapAngle(double angle) {
    while (angle >= PI) {
        angle -= 2.0 * PI;
    }

    while (angle < -PI) {
        angle += 2.0 * PI;
    }

    return angle;
}

// 根据课件的调平矩阵，计算两个水平分量和一个向下分量
void levelVector(const double input[], double roll, double pitch, double output[]) {
    double sr = sin(roll);
    double cr = cos(roll);
    double sp = sin(pitch);
    double cp = cos(pitch);

    output[0] = cp * input[0] + sr * sp * input[1] + cr * sp * input[2];
    output[1] = cr * input[1] - sr * input[2];
    output[2] = -sp * input[0] + sr * cp * input[1] + cr * cp * input[2];
}

bool readData(const fs::path& file, vector<Sample>& data) {
    ifstream input(file);

    if (!input) {
        cerr << "Cannot open sensors_matrix.txt\n";
        return false;
    }

    string line;
    int lineNumber = 0;

    while (getline(input, line)) {
        ++lineNumber;

        // 跳过空白行
        if (line.find_first_not_of(" \t\r") == string::npos) {
            continue;
        }

        stringstream row(line);
        string cell;

        double value[12] = {};
        int count = 0;
        bool valid = true;

        // 按逗号分隔每一列
        while (getline(row, cell, ',')) {
            if (count >= 12) {
                valid = false;
                break;
            }

            stringstream number(cell);

            if (!(number >> value[count]) || !isfinite(value[count])) {
                valid = false;
                break;
            }

            number >> ws;

            if (!number.eof()) {
                valid = false;
                break;
            }

            ++count;
        }

        // 本次文件的每一行都是 12 列
        if (!valid || count != 12 || line.back() == ',') {
            cerr << "Invalid data at line " << lineNumber << '\n';
            return false;
        }

        Sample s;
        s.time = value[0];

        if (!data.empty() && s.time <= data.back().time) {
            cerr << "Time must increase, line " << lineNumber << '\n';
            return false;
        }

        for (int k = 0; k < 3; ++k) {
            s.g[k] = value[1 + k] * DEG;   // deg/s -> rad/s
            s.a[k] = value[4 + k];
            s.m[k] = value[7 + k] * 1e-7; // mGauss -> T
        }

        // 第 11、12 列不参与本次计算

        // 三轴加速度的模
        s.acc = sqrt(
            s.a[0] * s.a[0]
            + s.a[1] * s.a[1]
            + s.a[2] * s.a[2]
        );

        if (s.acc < 1e-8) {
            cerr << "Invalid acceleration at line " << lineNumber << '\n';
            return false;
        }

        // 使用课件中的加速度计调平公式
        s.roll = atan2(-s.a[1], -s.a[2]);

        s.pitch = atan2(
            s.a[0],
            sqrt(s.a[1] * s.a[1] + s.a[2] * s.a[2])
        );

        data.push_back(s);
    }

    return data.size() >= 3 && !input.bad();
}

// 离线滑动平均，窗口为：
// [当前时刻 - 0.5 秒, 当前时刻 + 0.5 秒)
//
// 文件首尾没有足够数据时，只平均实际存在的数据。
void smoothAngles(vector<Sample>& data) {
    int n = static_cast<int>(data.size());

    int left = 0;
    int right = 0;

    for (int i = 0; i < n; ++i) {
        double begin = data[i].time - WINDOW_SECONDS / 2.0;
        double end = data[i].time + WINDOW_SECONDS / 2.0;

        // 找到窗口左边界
        while (left < n && data[left].time < begin - 1e-8) {
            ++left;
        }

        // right 指向窗口右侧第一个不参与平均的数据
        while (right < n && data[right].time < end - 1e-8) {
            ++right;
        }

        double rollSum = 0;
        double pitchSum = 0;

        for (int j = left; j < right; ++j) {
            rollSum += data[j].roll;
            pitchSum += data[j].pitch;
        }

        data[i].rollSmooth = rollSum / (right - left);
        data[i].pitchSmooth = pitchSum / (right - left);
    }
}

bool calculateHeadings(vector<Sample>& data) {
    for (int i = 0; i < static_cast<int>(data.size()); ++i) {
        Sample& s = data[i];

        // 使用平滑后的姿态角调平
        levelVector(s.g, s.rollSmooth, s.pitchSmooth, s.gh);
        levelVector(s.m, s.rollSmooth, s.pitchSmooth, s.mh);

        if (hypot(s.mh[0], s.mh[1]) < 1e-12) {
            cerr << "Horizontal magnetic field is too small.\n";
            return false;
        }

        // 磁北航向 + 磁偏角 = 真北航向
        s.headingMag = wrapAngle(-atan2(s.mh[1], s.mh[0]) + 14.11 * DEG
        );

        // 等价于先给原始 gz 加常值，再用同一个矩阵调平
        s.wzCorrected = s.gh[2] + cos(s.rollSmooth) * cos(s.pitchSmooth) * GZ_CORRECTION;

        if (i == 0) {
            s.headingGyro = -90.0 * DEG;
            s.headingCorrected = -90.0 * DEG;
        } else {
            const Sample& last = data[i - 1];
            double dt = s.time - last.time;

            // 梯形积分：
            // 前后两个时刻的角速度先取平均，再乘 dt
            s.headingGyro = wrapAngle(
                last.headingGyro
                + 0.5 * (last.gh[2] + s.gh[2]) * dt
            );

            s.headingCorrected = wrapAngle(
                last.headingCorrected
                + 0.5 * (last.wzCorrected + s.wzCorrected) * dt
            );
        }
    }

    return true;
}

// 波谷小于 9.2，且相邻脚步至少相隔 0.30 秒。
// 如果两个候选波谷太接近，保留加速度模更小的那个。
int detectSteps(vector<Sample>& data) {
    vector<int> steps;
    int n = static_cast<int>(data.size());

    for (int i = 1; i < n - 1; ++i) {
        bool valley = data[i].acc < data[i - 1].acc  && data[i].acc <= data[i + 1].acc;

        if (!valley || data[i].acc >= STEP_THRESHOLD) {
            continue;
        }

        if (steps.empty()|| data[i].time - data[steps.back()].time >= MIN_STEP_INTERVAL - 1e-8) {
            steps.push_back(i);
        } else if (data[i].acc < data[steps.back()].acc) {
            steps.back() = i;
        }
    }

    for (int index : steps) {
        data[index].step = 1;
    }

    return static_cast<int>(steps.size());
}

void calculatePositions(vector<Sample>& data) {
    for (int i = 1; i < static_cast<int>(data.size()); ++i) {
        double heading[3] = {
            data[i].headingMag,
            data[i].headingGyro,
            data[i].headingCorrected
        };

        for (int k = 0; k < 3; ++k) {
            data[i].east[k] = data[i - 1].east[k];
            data[i].north[k] = data[i - 1].north[k];

            if (data[i].step == 1) {
                // 航向从北顺时针为正：
                // 北向用 cos，东向用 sin
                data[i].east[k] += STEP_LENGTH * sin(heading[k]);
                data[i].north[k] += STEP_LENGTH * cos(heading[k]);
            }
        }
    }
}

bool saveResults(const fs::path& folder, const vector<Sample>& data) {
    ofstream output(folder / "pdr_result.csv");
    ofstream parameters(folder / "pdr_parameters.csv");

    if (!output || !parameters) {
        return false;
    }

    output << "time_s,gx_rad_s,gy_rad_s,gz_rad_s,"
           << "ax_mps2,ay_mps2,az_mps2,mx_T,my_T,mz_T,"
           << "acc_norm_mps2,roll_rad,pitch_rad,"
           << "roll_smooth_rad,pitch_smooth_rad,"
           << "gyro_down_rad_s,gyro_down_corrected_rad_s,"
           << "heading_mag_rad,heading_gyro_rad,heading_corrected_rad,"
           << "is_step,east_mag_m,north_mag_m,"
           << "east_gyro_m,north_gyro_m,east_corrected_m,north_corrected_m\n";

    // 科学计数法可保留 Tesla 单位的小数值精度
    output << scientific << setprecision(12);

    for (const Sample& s : data) {
        output << s.time;

        for (int k = 0; k < 3; ++k) {
            output << ',' << s.g[k];
        }

        for (int k = 0; k < 3; ++k) {
            output << ',' << s.a[k];
        }

        for (int k = 0; k < 3; ++k) {
            output << ',' << s.m[k];
        }

        output << ',' << s.acc
               << ',' << s.roll
               << ',' << s.pitch
               << ',' << s.rollSmooth
               << ',' << s.pitchSmooth
               << ',' << s.gh[2]
               << ',' << s.wzCorrected
               << ',' << s.headingMag
               << ',' << s.headingGyro
               << ',' << s.headingCorrected
               << ',' << s.step;

        for (int k = 0; k < 3; ++k) {
            output << ',' << s.east[k]
                   << ',' << s.north[k];
        }

        output << '\n';
    }

    parameters << "step_length_m,valley_threshold_mps2,"
               << "min_step_interval_s,window_s,gz_correction_rad_s\n";

    parameters << setprecision(15)
               << STEP_LENGTH << ','
               << STEP_THRESHOLD << ','
               << MIN_STEP_INTERVAL << ','
               << WINDOW_SECONDS << ','
               << GZ_CORRECTION << '\n';

    output.flush();
    parameters.flush();

    return output.good() && parameters.good();
}

int main() {
    try {
        // 从当前工作目录向上查找数据目录。
        // 兼容项目根目录、src/PDR、src/output 等启动位置。
        fs::path root = fs::current_path();
        fs::path folder;
        bool found = false;

        while (true) {
            folder = root / fs::u8path(u8"数据-行人航迹推算");

            if (fs::exists(folder / "sensors_matrix.txt")) {
                found = true;
                break;
            }

            if (root == root.parent_path()) {
                break;
            }

            root = root.parent_path();
        }

        if (!found) {
            cerr << "Cannot find data. Run inside the IndoorPos project.\n";
            cerr << "Working directory: " << fs::current_path() << '\n';
            return 1;
        }

        vector<Sample> data;

        if (!readData(folder / "sensors_matrix.txt", data)) {
            return 1;
        }

        smoothAngles(data);

        if (!calculateHeadings(data)) {
            return 1;
        }

        int stepCount = detectSteps(data);
        calculatePositions(data);

        fs::path outputFolder = root / "src" / "PDR" / "pdr_output";
        fs::create_directories(outputFolder);

        if (!saveResults(outputFolder, data)) {
            cerr << "Cannot write result files.\n";
            return 1;
        }

        cout << fixed << setprecision(3);

        cout << "Samples: " << data.size() << '\n';

        cout << "Duration (s): " << data.back().time - data.front().time << '\n';

        cout << "Detected steps: " << stepCount << '\n';

        cout << "Estimated walking distance (m): " << stepCount * STEP_LENGTH << '\n';

        cout << "Added gz correction (deg/s): " << GZ_CORRECTION / DEG << '\n';

        cout << "Saved pdr_result.csv and pdr_parameters.csv " << "in pdr_output.\n";
    } catch (const exception& error) {
        cerr << "Error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}