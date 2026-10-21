#include <iostream>
#include <fstream>
#include <iomanip>
#include <cmath>
#include <string>
#include <filesystem>

using namespace std;

// 求解三元一次方程
// a的前3列是系数，第4列是等号右边的数
// result保存三个未知数的解
bool solve3(double a[3][4], double result[3])
{
    // 高斯消元
    for (int k = 0; k < 3; k++)
    {
        // 找到当前列绝对值最大的系数
        int row = k;

        for (int i = k + 1; i < 3; i++)
        {
            if (fabs(a[i][k]) > fabs(a[row][k]))
            {
                row = i;
            }
        }

        // 系数过小，无法可靠求解
        if (fabs(a[row][k]) < 1e-12)
        {
            return false;
        }

        // 交换两行
        for (int j = 0; j < 4; j++)
        {
            double temp = a[k][j];
            a[k][j] = a[row][j];
            a[row][j] = temp;
        }

        // 消去当前未知数
        for (int i = k + 1; i < 3; i++)
        {
            double factor = a[i][k] / a[k][k];

            for (int j = k; j < 4; j++)
            {
                a[i][j] -= factor * a[k][j];
            }
        }
    }

    // 从最后一个方程开始回代
    for (int i = 2; i >= 0; i--)
    {
        double value = a[i][3];

        for (int j = i + 1; j < 3; j++)
        {
            value -= a[i][j] * result[j];
        }

        result[i] = value / a[i][i];
    }

    return true;
}

// 根据八个距离计算标签位置
// station[i][0、1、2]分别表示第i个基站的X、Y、Z
// p[0、1、2]分别保存标签的X、Y、Z
bool calculatePosition(double station[8][3],double d[8], double p[3])
{
    // 水平初始位置取基站中心
    p[0] = 0.0;
    p[1] = 0.0;

    for (int i = 0; i < 8; i++)
    {
        p[0] += station[i][0];
        p[1] += station[i][1];
    }

    p[0] /= 8.0;
    p[1] /= 8.0;

    // Z=0只是初始猜测，后面也参与计算和更新
    p[2] = 0.0;

    for (int count = 0; count < 50; count++)
    {
        // 最小二乘法得到的三元一次方程
        double a[3][4] = {0};

        for (int i = 0; i < 8; i++)
        {
            double dx = p[0] - station[i][0];
            double dy = p[1] - station[i][1];
            double dz = p[2] - station[i][2];

            double r = sqrt(dx * dx + dy * dy + dz * dz);

            if (r < 1e-8)
            {
                return false;
            }

            // 距离对三个坐标的偏导数
            double b[3];
            b[0] = dx / r;
            b[1] = dy / r;
            b[2] = dz / r;

            // 测量距离减去计算距离
            double l = d[i] - r;

            // 累加方程系数
            for (int j = 0; j < 3; j++)
            {
                for (int k = 0; k < 3; k++)
                {
                    a[j][k] += b[j] * b[k];
                }

                a[j][3] += b[j] * l;
            }
        }

        double change[3];

        if (!solve3(a, change))
        {
            return false;
        }

        // 更新三个坐标
        for (int j = 0; j < 3; j++)
        {
            p[j] += change[j];

            if (!isfinite(p[j]))
            {
                return false;
            }
        }

        double changeLength = sqrt(
            change[0] * change[0]
            + change[1] * change[1]
            + change[2] * change[2]
        );

        // 改正量小于0.0001米，认为已经收敛
        if (changeLength < 0.0001)
        {
            return true;
        }
    }

    return false;
}

int main()
{
    filesystem::path folder = filesystem::u8path(u8"数据-距离交会/数据2-小车-UWB");

    ifstream baseFile(folder / "base-station-location.txt");

    if (!baseFile.is_open())
    {
        cout << "Cannot open base station file." << endl;
        return 1;
    }

    double station[8][3];

    // 读取八个基站，检查编号顺序
    for (int i = 0; i < 8; i++)
    {
        int id;

        if (!(baseFile >> id >> station[i][0] >> station[i][1] >> station[i][2]) || id != i + 1)
        {
            cout << "Invalid base station data." << endl;
            return 1;
        }
    }

    // 分别计算标签2和标签3
    for (int tag = 2; tag <= 3; tag++)
    {
        string number = to_string(tag);

        string inputName = "range_tag_" + number + ".txt";
        string outputName = "result_tag_" + number + "_cpp.csv";

        ifstream inFile(folder / inputName);

        if (!inFile.is_open())
        {
            cout << "Cannot open " << inputName << endl;
            return 1;
        }

        ofstream outFile(folder / outputName);

        if (!outFile.is_open())
        {
            cout << "Cannot create " << outputName << endl;
            return 1;
        }

        outFile << "time_ms,x_m,y_m,z_m,range_rms_m,status\n";
        outFile << fixed << setprecision(6);

        long long time;
        double d[8];

        int successCount = 0;
        int failedCount = 0;

        while (inFile >> time
               >> d[0] >> d[1] >> d[2] >> d[3]
               >> d[4] >> d[5] >> d[6] >> d[7])
        {
            bool valid = true;

            for (int i = 0; i < 8; i++)
            {
                if (!isfinite(d[i]) || d[i] <= 0.0)
                {
                    valid = false;
                }
            }

            if (!valid)
            {
                outFile << time << ",nan,nan,nan,nan,invalid\n";
                failedCount++;
                continue;
            }

            double p[3];

            if (!calculatePosition(station, d, p))
            {
                outFile << time
                        << ",nan,nan,nan,nan,not_converged\n";

                failedCount++;
                continue;
            }

            // 计算八个距离残差的均方根
            double sum = 0.0;

            for (int i = 0; i < 8; i++)
            {
                double dx = p[0] - station[i][0];
                double dy = p[1] - station[i][1];
                double dz = p[2] - station[i][2];

                double r = sqrt(dx * dx + dy * dy + dz * dz);
                double error = d[i] - r;

                sum += error * error;
            }

            double rms = sqrt(sum / 8.0);

            outFile << time << ","
                    << p[0] << ","
                    << p[1] << ","
                    << p[2] << ","
                    << rms << ",ok\n";

            successCount++;
        }

        cout << "Tag " << tag << endl;
        cout << "Successful rows: " << successCount << endl;
        cout << "Failed rows: " << failedCount << endl;
        cout << "Output: " << outputName << endl;
    }

    return 0;
}