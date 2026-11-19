#include <iostream>
#include <fstream>
#include <iomanip>
#include <cmath>
#include <filesystem>

using namespace std;
const double PI = 3.14159265358979323846;
const double earthA = 6378137.0;
const double e2 = 0.00669437999014;

// 根据四个距离和已知高程，计算水平坐标
bool calculatePosition(double sx[], double sy[], double sh[], double d[], double h, double& x, double& y)
{
    // 初始位置取四个基站的中心
    x = 0.0;
    y = 0.0;

    for (int i = 0; i < 4; i++)
    {
        x += sx[i];
        y += sy[i];
    }

    x /= 4.0;
    y /= 4.0;

    // 最多迭代50次
    for (int k = 0; k < 50; k++)
    {
        double aa = 0.0;
        double ab = 0.0;
        double bb = 0.0;
        double al = 0.0;
        double bl = 0.0;

        for (int i = 0; i < 4; i++)
        {
            double dx = x - sx[i];
            double dy = y - sy[i];
            double dz = h - sh[i];

            // 当前估计位置到基站的距离
            double r = sqrt(dx * dx + dy * dy + dz * dz);

            if (r < 1e-8)
            {
                return false;
            }

            // 距离公式对x、y的偏导数
            double a = dx / r;
            double b = dy / r;

            // 测量距离减去计算距离
            double l = d[i] - r;

            // 累加最小二乘方程的系数
            aa += a * a;
            ab += a * b;
            bb += b * b;
            al += a * l;
            bl += b * l;
        }

        // 求解下面的二元一次方程：
        // aa * changeX + ab * changeY = al
        // ab * changeX + bb * changeY = bl

        double det = aa * bb - ab * ab;

        if (fabs(det) < 1e-12)
        {
            return false;
        }

        double changeX = (bb * al - ab * bl) / det;
        double changeY = (aa * bl - ab * al) / det;

        x += changeX;
        y += changeY;

        if (!isfinite(x) || !isfinite(y))
        {
            return false;
        }

        // 坐标改正量小于0.0001米，结束迭代
        if (sqrt(changeX * changeX + changeY * changeY) < 0.0001)
        {
            return true;
        }
    }

    return false;
}

int main()
{
    // 数据目录
    filesystem::path folder = filesystem::u8path(u8"数据-距离交会/数据1-无人机-Ultrasonic");

    ifstream baseFile(folder / "base-station-location.txt");
    ifstream rangeFile(folder / "range-with-height.txt");

    if (!baseFile.is_open() || !rangeFile.is_open())
    {
        cout << "Cannot open input files." << endl;
        return 1;
    }

    double lat[4];
    double lon[4];
    double sh[4];

    double sx[4];
    double sy[4];

    // 读取基站坐标，检查编号顺序
    for (int i = 0; i < 4; i++)
    {
        int id;

        if (!(baseFile >> id >> lat[i] >> lon[i] >> sh[i]) || id != i + 1)
        {
            cout << "Invalid base station data." << endl;
            return 1;
        }
    }

    // 将经纬度转换为局部平面坐标
    // 对于本题几十米的场地，可以采用这种局部近似

    double rad = PI / 180.0;
    double lat0 = lat[0] * rad;

    double q = 1.0 - e2 * sin(lat0) * sin(lat0);

    // WGS84椭球曲率半径
    double N = earthA / sqrt(q);
    double M = earthA * (1.0 - e2) / pow(q, 1.5);

    for (int i = 0; i < 4; i++)
    {
        sx[i] = (lon[i] - lon[0]) * rad * N * cos(lat0);
        sy[i] = (lat[i] - lat[0]) * rad * M;
    }

    ofstream outFile(folder / "result_cpp.csv");

    if (!outFile.is_open())
    {
        cout << "Cannot create output file." << endl;
        return 1;
    }

    outFile << "time_s,east_m,north_m,height_m,range_rms_m,status\n";
    outFile << fixed << setprecision(6);

    double time;
    double d[4];
    double h;

    int successCount = 0;
    int invalidCount = 0;
    int failedCount = 0;

    // 每次读取一行观测值
    while (rangeFile >> time >> d[0] >> d[1] >> d[2] >> d[3] >> h)
    {
        bool valid = isfinite(h);

        for (int i = 0; i < 4; i++)
        {
            double heightDifference = fabs(h - sh[i]);

            // 斜距不能为零，也不能小于竖直高差
            if (!isfinite(d[i]) || d[i] <= 0.0 || d[i] < heightDifference)
            {
                valid = false;
            }
        }

        if (!valid)
        {
            outFile << time << ",nan,nan," << h << ",nan,invalid\n";

            invalidCount++;
            continue;
        }

        double x;
        double y;

        bool success = calculatePosition(sx, sy, sh, d, h, x, y);

        if (!success)
        {
            outFile << time << ",nan,nan," << h << ",nan,not_converged\n";

            failedCount++;
            continue;
        }

        // 计算四个距离残差的均方根
        double sum = 0.0;

        for (int i = 0; i < 4; i++)
        {
            double dx = x - sx[i];
            double dy = y - sy[i];
            double dz = h - sh[i];

            double r = sqrt(dx * dx + dy * dy + dz * dz);
            double error = d[i] - r;

            sum += error * error;
        }

        double rms = sqrt(sum / 4.0);

        outFile << time << ","
                << x << ","
                << y << ","
                << h << ","
                << rms << ",ok\n";

        successCount++;
    }

    cout << "Successful rows: " << successCount << endl;
    cout << "Invalid rows: " << invalidCount << endl;
    cout << "Not converged rows: " << failedCount << endl;
    cout << "Output: result_cpp.csv" << endl;

    return 0;
}