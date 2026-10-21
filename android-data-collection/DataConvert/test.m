clc
close;
clear;

CFG_NAV_v1;
D2R = pi/180;

[da_sensors, da_wifi, da_gps] = dataConvert(Nav.folder_name,Nav);
