#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <iomanip>
#include <cmath>
#include <filesystem>

using namespace std;
using namespace filesystem;

#define cover 0
// 读取一行CSV数据：0表示文件结束，-1表示格式错误
int readRow(ifstream& file, double data[], int maxCount)
{
    string line;

    while (getline(file, line))
    {
        if (line.find_first_not_of(" \t\r") == string::npos)
            continue;

        stringstream ss(line);
        string item;
        int count = 0;

        // 每次读取两个逗号之间的内容
        while (getline(ss, item, ','))
        {
            if (count >= maxCount)
                return -1;

            stringstream number(item);
            double value;

            if (!(number >> value) || !isfinite(value))
                return -1;

            number >> ws;
            if (!number.eof())
                return -1;

            data[count++] = value;
        }

        // 最后一列为空，也视为格式错误
        if (line.back() == ',' || count == 0)
            return -1;

        return count;
    }

    return 0;
}

// 根据n个有效距离，计算二维位置
bool calculatePosition(
    double sx[], double sy[], double d[],
    int n, double& x, double& y)
{
    x = 0.0;
    y = 0.0;

    // 初始位置取有效基站的中心
    for (int i = 0; i < n; i++)
    {
        x += sx[i];
        y += sy[i];
    }

    x /= n;
    y /= n;

    for (int count = 0; count < 50; count++)
    {
        double aa = 0.0, ab = 0.0, bb = 0.0;
        double al = 0.0, bl = 0.0;

        for (int i = 0; i < n; i++)
        {
            double dx = x - sx[i];
            double dy = y - sy[i];
            double r = sqrt(dx * dx + dy * dy);

            if (r < 1e-8)
                return false;

            double a = dx / r;
            double b = dy / r;
            double l = d[i] - r;

            aa += a * a;
            ab += a * b;
            bb += b * b;
            al += a * l;
            bl += b * l;
        }

        // 求解二元一次方程，得到坐标改正数
        double det = aa * bb - ab * ab;

        if (fabs(det) < 1e-12)
            return false;

        double changeX = (bb * al - ab * bl) / det;
        double changeY = (aa * bl - ab * al) / det;

        x += changeX;
        y += changeY;

        if (!isfinite(x) || !isfinite(y))
            return false;

        if (sqrt(changeX * changeX + changeY * changeY) < 0.0001)
            return true;
    }

    return false;
}

// 处理一个文件夹：无遮挡或有遮挡
bool processData(filesystem::path folder)
{
    ifstream baseFile(folder / "base-station-location.txt");
    ifstream rangeFile(folder / "range.txt");
    ifstream refFile(folder / "ref_pos.txt");

    if (!baseFile.is_open() || !rangeFile.is_open() || !refFile.is_open())
    {
        cout << "Cannot open input files." << endl;
        cout << "Working directory: " << filesystem::current_path() << endl;
        return false;
    }

    double station[4][3];
    double row[5];

    // 基站顺序必须是3、4、5、6
    for (int i = 0; i < 4; i++)
    {
        if (readRow(baseFile, row, 4) != 4 || row[0] != i + 3)
        {
            cout << "Invalid base station data or order." << endl;
            return false;
        }

        for (int j = 0; j < 3; j++)
            station[i][j] = row[j + 1];
    }

    ofstream outFile(folder / "result_student_cpp.csv");

    if (!outFile.is_open())
    {
        cout << "Cannot create output file." << endl;
        return false;
    }

    outFile << "time_s,elapsed_s,x_m,y_m,used_count,range_rms_m,status\n";
    outFile << fixed << setprecision(6);

    double reference[4];
    int refCount = readRow(refFile, reference, 4);

    int total = 0, success = 0, insufficient = 0, failed = 0;
    int matched = 0;
    double startTime = 0.0;
    double sumX = 0.0, sumY = 0.0;

    while (true)
    {
        int count = readRow(rangeFile, row, 5);

        if (count == 0)
            break;

        total++;

        if (count != 5)
        {
            cout << "Invalid range data at record " << total << endl;
            return false;
        }

        double time = row[0];

        if (total == 1)
            startTime = time;

        double elapsed = time - startTime;

        // 筛选有效距离，同时保存它对应的基站坐标
        double sx[4], sy[4], d[4];
        int n = 0;

        for (int i = 0; i < 4; i++)
        {
            if (row[i + 1] > 0.0)
            {
                sx[n] = station[i][0];
                sy[n] = station[i][1];
                d[n] = row[i + 1];
                n++;
            }
        }

        if (n < 3)
        {
            outFile << time << "," << elapsed
                    << ",nan,nan," << n << ",nan,insufficient\n";
            insufficient++;
            continue;
        }

        double x, y;

        if (!calculatePosition(sx, sy, d, n, x, y))
        {
            outFile << time << "," << elapsed
                    << ",nan,nan," << n << ",nan,not_converged\n";
            failed++;
            continue;
        }

        // 计算距离拟合残差的均方根
        double sum = 0.0;

        for (int i = 0; i < n; i++)
        {
            double dx = x - sx[i];
            double dy = y - sy[i];
            double r = sqrt(dx * dx + dy * dy);
            double error = d[i] - r;

            sum += error * error;
        }

        double rms = sqrt(sum / n);

        outFile << time << "," << elapsed << ","
                << x << "," << y << "," << n << ","
                << rms << ",ok\n";
        success++;

        // 两个文件均按时间递增，推进参考记录进行匹配
        while (refCount == 4 && reference[0] < time - 0.000001)
            refCount = readRow(refFile, reference, 4);

        if (refCount != 0 && refCount != 4)
        {
            cout << "Invalid reference data." << endl;
            return false;
        }

        // 参考坐标只用于评价，不参与位置计算
        if (refCount == 4 && fabs(reference[0] - time) < 0.000001)
        {
            double ex = x - reference[1];
            double ey = y - reference[2];

            sumX += ex * ex;
            sumY += ey * ey;
            matched++;
        }
    }

    cout << "Total: " << total << endl;
    cout << "Successful: " << success << endl;
    cout << "Insufficient ranges: " << insufficient << endl;
    cout << "Not converged: " << failed << endl;
    cout << "Matched reference rows: " << matched << endl;

    if (matched > 0)
    {
        cout << fixed << setprecision(4);
        cout << "X RMSE: " << sqrt(sumX / matched) << " m" << endl;
        cout << "Y RMSE: " << sqrt(sumY / matched) << " m" << endl;
        cout << "Horizontal RMSE: "
             << sqrt((sumX + sumY) / matched) << " m" << endl;
    }

    cout << "Output: result_student_cpp.csv" << endl;
    return true;
}

int main()
{
    // 运行时的工作目录应为项目根目录 IndoorPos
    path root = u8path(u8"数据-距离交会/数据4-课上同学采集-Ultrasonic");

    cout << "Dataset: no obstruction" << endl;
    bool ok1 = processData(root / filesystem::u8path(u8"无遮挡数据"));

    cout << "\nDataset: obstruction" << endl;
    bool ok2 = processData(root / filesystem::u8path(u8"有遮挡数据"));

    return (ok1 && ok2) ? 0 : 1;
}