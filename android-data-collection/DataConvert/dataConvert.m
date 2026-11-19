
function [da, da_wifi, da_gps] = dataConvert(folder_name, Cal)

% folder_name = 'C:\Users\LiYou\Desktop\SenDa2\20140812091826\';
f_sensors = [folder_name 'sensors.txt'];
f_wifi = [folder_name 'wifi.txt'];
f_gps = [folder_name 'GPS.txt'];

% Sensor data
[da] = read_sensors(f_sensors,Cal);

% WiFi
[da_wifi] = read_wifi(f_wifi,Cal);

% GPS
[da_gps] = read_gps(f_gps,Cal);



































