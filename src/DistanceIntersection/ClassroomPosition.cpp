#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <iomanip>
#include <cmath>
#include <filesystem>

using namespace std;

// 读取一行逗号分隔的数据。
// 返回读取的数字个数；0表示文件结束，-1表示格式错误。
int readRow(ifstream& file, double data[], int maxCount)
{
    string line;

    while (getline(file, line))
    {
        if (line.find_first_not_of(" \t\r") == string::npos)
            continue;

        // 将逗号改成空格，方便用 >> 读取
        for (int i = 0; i < (int)line.size(); i++)
        {
            if (line[i] == ',')
                line[i] = ' ';
        }

        stringstream ss(line);
        double value;
        int count = 0;

        while (ss >> value)
        {
            if (count >= maxCount || !isfinite(value))
                return -1;

            data[count] = value;
            count++;
        }

        if (!ss.eof() || count == 0)
            return -1;

        return count;
    }

    return 0;
}

// 二维距离交会，n为本行实际使用的基站数量
bool calculatePosition(
    double station[4][3], double distance[],
    int n, double& x, double& y)
{
    // 初始坐标取参与计算的基站中心
    x = 0.0;
    y = 0.0;

    for (int i = 0; i < n; i++)
    {
        x += station[i][0];
        y += station[i][1];
    }

    x /= n;
    y /= n;

    for (int count = 0; count < 50; count++)
    {
        double aa = 0.0;
        double ab = 0.0;
        double bb = 0.0;
        double al = 0.0;
        double bl = 0.0;

        for (int i = 0; i < n; i++)
        {
            double dx = x - station[i][0];
            double dy = y - station[i][1];
            double r = sqrt(dx * dx + dy * dy);

            if (r < 1e-8)
                return false;

            double a = dx / r;
            double b = dy / r;
            double l = distance[i] - r;

            aa += a * a;
            ab += a * b;
            bb += b * b;
            al += a * l;
            bl += b * l;
        }

        // 解二元一次方程：
        // aa * changeX + ab * changeY = al
        // ab * changeX + bb * changeY = bl
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

int main()
{
    // 程序运行时，工作目录应为项目根目录 IndoorPos
    filesystem::path folder = filesystem::u8path(
        u8"数据-距离交会/数据3-教室-Ultrasonic"
    );

    ifstream baseFile(folder / "base-station-location.txt");
    ifstream rangeFile(folder / "range.txt");
    ifstream refFile(folder / "ref_pos.txt");

    if (!baseFile.is_open() || !rangeFile.is_open() || !refFile.is_open())
    {
        cout << "Cannot open input files." << endl;
        cout << "Working directory: " << filesystem::current_path() << endl;
        return 1;
    }

    // 四行依次对应基站3、4、5、6
    // 每行保存X、Y、Z；二维计算只使用X、Y
    double station[4][3];
    double baseData[4];

    for (int i = 0; i < 4; i++)
    {
        if (readRow(baseFile, baseData, 4) != 4
            || baseData[0] != i + 3)
        {
            cout << "Invalid base station data or order." << endl;
            return 1;
        }

        for (int j = 0; j < 3; j++)
            station[i][j] = baseData[j + 1];
    }

    ofstream outFile(folder / "result_classroom_cpp.csv");

    if (!outFile.is_open())
    {
        cout << "Cannot create output file." << endl;
        return 1;
    }

    outFile << "time_s,elapsed_s,x_m,y_m,range_rms_m,status\n";
    outFile << fixed << setprecision(6);

    double data[5];
    double reference[4];

    // 参考数据按时间递增读取，仅用于计算误差
    int refCount = readRow(refFile, reference, 4);

    int total = 0;
    int successCount = 0;
    int invalidCount = 0;
    int failedCount = 0;
    int matchedCount = 0;

    double startTime = 0.0;
    double sumX = 0.0;
    double sumY = 0.0;

    while (true)
    {
        int count = readRow(rangeFile, data, 5);

        if (count == 0)
            break;

        total++;

        // 当前文件是时间+3个距离，也兼容时间+4个距离
        if (count != 4 && count != 5)
        {
            cout << "Invalid range format at record " << total << endl;
            return 1;
        }

        double time = data[0];

        if (total == 1)
            startTime = time;

        double elapsed = time - startTime;
        int n = count - 1;

        double distance[4];
        bool valid = true;

        // 三个距离对应3、4、5；若有第四个，则对应6
        for (int i = 0; i < n; i++)
        {
            distance[i] = data[i + 1];

            if (distance[i] <= 0.0)
                valid = false;
        }

        if (!valid)
        {
            outFile << time << "," << elapsed
                    << ",nan,nan,nan,invalid\n";
            invalidCount++;
            continue;
        }

        double x;
        double y;

        if (!calculatePosition(station, distance, n, x, y))
        {
            outFile << time << "," << elapsed
                    << ",nan,nan,nan,not_converged\n";
            failedCount++;
            continue;
        }

        // 计算距离拟合残差
        double sum = 0.0;

        for (int i = 0; i < n; i++)
        {
            double dx = x - station[i][0];
            double dy = y - station[i][1];

            double r = sqrt(dx * dx + dy * dy);
            double error = distance[i] - r;

            sum += error * error;
        }

        double rms = sqrt(sum / n);

        outFile << time << "," << elapsed << ","
                << x << "," << y << "," << rms << ",ok\n";

        successCount++;

        // 将参考记录推进到当前时刻或之后
        while (refCount == 4 && reference[0] < time - 0.000001)
            refCount = readRow(refFile, reference, 4);

        if (refCount != 0 && refCount != 4)
        {
            cout << "Invalid reference data." << endl;
            return 1;
        }

        // 时间相同时，才计算定位误差
        if (refCount == 4 && fabs(reference[0] - time) < 0.000001)
        {
            double ex = x - reference[1];
            double ey = y - reference[2];

            sumX += ex * ex;
            sumY += ey * ey;
            matchedCount++;
        }
    }

    cout << "Total rows: " << total << endl;
    cout << "Successful rows: " << successCount << endl;
    cout << "Invalid rows: " << invalidCount << endl;
    cout << "Not converged rows: " << failedCount << endl;
    cout << "Matched reference rows: " << matchedCount << endl;

    if (matchedCount > 0)
    {
        cout << fixed << setprecision(4);
        cout << "X RMSE: " << sqrt(sumX / matchedCount) << " m" << endl;
        cout << "Y RMSE: " << sqrt(sumY / matchedCount) << " m" << endl;
        cout << "Horizontal RMSE: "
             << sqrt((sumX + sumY) / matchedCount) << " m" << endl;
    }

    cout << "Output: result_classroom_cpp.csv" << endl;

    return 0;
}