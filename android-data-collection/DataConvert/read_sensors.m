% New - unit deg/s, do not need to change axis

function [da] = read_sensors(f_sensor,Cal)

da_sensor = load(f_sensor);

% First delete the repeated data
% for i=1:size(da_sensor,1)
%    %for j=size(da_sensor,1):-1:i+1
%    nnn = size(da_sensor,1);
%    for j=i+1:nnn
%        if (da_sensor(j,1) == da_sensor(i,1) && abs(da_sensor(j,2)-da_sensor(i,2))<10^-6)
%            
%            da_sensor(j,:) = [];
%            nnn = nnn -1;
%        end  
%    end   
% end

nnn1 = size(da_sensor,1);
for i=nnn1:-1:2
    if da_sensor(i-1,1) == da_sensor(i,1) && abs(da_sensor(i-1,2)-da_sensor(i,2))<10^-6
        da_sensor(i,:) = [];
        nnn1 = nnn1 -1;
    end
end

nda = size(da_sensor, 1);
dataRate = Cal.dataRate;

t0 = min(da_sensor(:,2));
da_sensor(:,2) = da_sensor(:,2) - t0;

da_gyro0 = zeros(nda,4);
da_accel0 = zeros(nda,4);
da_mag0 = zeros(nda,4);
da_baro0 = zeros(nda,2);
da_temper0 = zeros(nda,2);

iii_gyro = 0;
iii_accel = 0;
iii_mag = 0;
iii_baro = 0;
iii_temper = 0;


    
for i = 1:nda
    if da_sensor(i,1) == 1
        iii_gyro = iii_gyro + 1;   
        if iii_gyro == 1 %% sometimes mag time will not start at the same time with gyro and accel
            t00_gyro = da_sensor(i,2);
            if abs(t00_gyro-t0) > 10
                dtdt_gyro = t00_gyro;
            else
                dtdt_gyro = 0; 
            end
        end
        da_gyro0(iii_gyro,:) = [da_sensor(i,2)-dtdt_gyro da_sensor(i,3:5)];
    elseif da_sensor(i,1) == 2
        iii_accel = iii_accel + 1;
        if iii_accel == 1 %% sometimes mag time will not start at the same time with gyro and accel
            t00_accel = da_sensor(i,2);
            if abs(t00_accel-t0) > 10
                dtdt_accel = t00_accel;
            else
                dtdt_accel = 0;
            end
        end
        da_accel0(iii_accel,:) = [da_sensor(i,2)-dtdt_accel da_sensor(i,3:5)];
    elseif da_sensor(i,1) == 3
        iii_mag = iii_mag + 1;
        if iii_mag == 1 %% sometimes mag time will not start at the same time with gyro and accel
            t00_mag = da_sensor(i,2);
            if abs(t00_mag-t0) > 10
                dtdt_mag = t00_mag;
            else
                dtdt_mag = 0;
            end
        end
        da_mag0(iii_mag,:) = [da_sensor(i,2)-dtdt_mag da_sensor(i,3:5)]; 
    elseif da_sensor(i,1) == 4
        iii_baro = iii_baro + 1; 
        if iii_baro == 1 %% sometimes mag time will not start at the same time with gyro and accel
            t00_baro = da_sensor(i,2);
            if abs(t00_baro-t0) > 10
                dtdt_baro = t00_baro;
            else
                dtdt_baro = 0;
            end
        end
        da_baro0(iii_baro,:) = [da_sensor(i,2)-dtdt_baro da_sensor(i,3)];   
    elseif da_sensor(i,1) == 0
        iii_temper = iii_temper + 1;
       
        if iii_temper == 1 %% sometimes mag time will not start at the same time with gyro and accel
            t00_temper = da_sensor(i,2);
            if abs(t00_temper-t0) > 10
                dtdt_temper = t00_temper;
            else
                dtdt_temper = 0;
            end
        end
        da_temper0(iii_temper,:) = [da_sensor(i,2)-dtdt_temper da_sensor(i,3)];
    end 
end

if iii_gyro ~= 0 
    da_gyro0  = da_gyro0(1:iii_gyro, :);
end
if iii_accel ~= 0
    da_accel0 = da_accel0(1:iii_accel, :);
end
if iii_mag ~=0
    da_mag0  = da_mag0(1:iii_mag, :);
end
if iii_baro ~= 0
    da_baro0  = da_baro0(1:iii_baro, :);
end
if iii_temper ~= 0
    da_temper0  = da_temper0(1:iii_temper, :);
end

% interpolation
da_gyro0(1,1) = 0;   
da_accel0(1,1) = 0; 
da_mag0(1,1) = 0;   
da_baro0(1,1) = 0;   
da_temper0(1,1) = 0; 


if iii_mag ~= 0 && iii_gyro ~= 0 && iii_accel ~= 0 && iii_baro ~= 0 && iii_temper ~= 0
    t_end = min([da_gyro0(iii_gyro,1), da_accel0(iii_accel,1), da_mag0(iii_mag,1), da_baro0(iii_baro,1), da_temper0(iii_temper,1)]);
elseif iii_mag ~= 0 && iii_gyro ~= 0 && iii_accel ~= 0
    t_end = min([da_gyro0(iii_gyro,1), da_accel0(iii_accel,1), da_mag0(iii_mag,1)]);
elseif iii_mag == 0 && iii_gyro ~= 0 && iii_accel ~= 0
    t_end = min([da_gyro0(iii_gyro,1), da_accel0(iii_accel,1)]);
elseif iii_mag == 0 && iii_gyro == 0 && iii_accel ~= 0
    t_end = da_gyro0(iii_gyro,1);   
end
t_end = 1/dataRate * (floor(t_end*dataRate));

x1 = [0:1/dataRate:t_end]';

da_gyro = zeros(length(x1),4);
da_gyro(:,1) = x1;

da_accel = zeros(length(x1),4);
da_accel(:,1) = x1;

da_mag = zeros(length(x1),4);
da_mag(:,1) = x1;

da_baro = zeros(length(x1),2);
da_baro(:,1) = x1;

da_temper = zeros(length(x1),2);
da_temper(:,1) = x1;



for i = 2:4
    if iii_gyro ~= 0 
        da_gyro(:,i) = interp1(da_gyro0(:,1),da_gyro0(:,i),da_gyro(:,1));
    end
    if iii_accel ~= 0
        da_accel(:,i) = interp1(da_accel0(:,1),da_accel0(:,i),da_accel(:,1));
    end
    if iii_mag ~=0
        da_mag(:,i) = interp1(da_mag0(:,1),da_mag0(:,i),da_mag(:,1));    
    end
end
if iii_baro ~= 0
    da_baro(:,2) = interp1(da_baro0(:,1),da_baro0(:,2),da_baro(:,1));
end
if iii_temper ~= 0
    da_temper(:,2) = interp1(da_temper0(:,1),da_temper0(:,2),da_temper(:,1));
end

unit_mag = 10;  % Converted from uT to mG

%%%%%%
da = [da_gyro(:,1) da_gyro(:,2:4) da_accel(:,2:4) da_mag(:,2:4)*unit_mag da_baro(:,2) da_temper(:,2)];

col_t = 1;      % s
col_gyro = [2,3,4];    % deg/s   
col_accel = [5,6,7];   % m/s^2
col_mag = [8,9,10];    % mGauss
col_baro = 11;         % hPa
col_temper = 12;       % ^oC

fname_out = [f_sensor(1:length(f_sensor)-4) '_matrix.txt'];
fout_sensors = fopen(fname_out, 'w');
for i=1:size(da,1)
    fprintf(fout_sensors,'%.6f,%.6f,%.6f,%.6f,%.3f,%.3f,%.3f,%.6f,%.6f,%.6f,%.6f,%.6f\n',...
        da(i,1), da(i,2:4), da(i,5:7), da(i,8:10), da(i,11:12));    
end
fclose(fout_sensors);

clear da_gyro0 da_accel0  da_mag0 da_baro0 da_temper0 x1;
clear da_gyro da_accel  da_mag da_baro da_temper;
clear da_sensor;

if Cal.if_plot_sensors == 1
    figure;
    subplot(2,1,1);
    plot(da(:,col_t),da(:,col_gyro(1)),da(:,col_t),da(:,col_gyro(2)),da(:,col_t),da(:,col_gyro(3)),'linewidth',Cal.Font_linewidth);
    yi=ylabel('deg/s'); set(yi,'fontsize',Cal.Font_label);
    li=legend('Gx','Gy','Gz'); set(li,'fontsize',Cal.Font_legent);
    ti=title('Gyro and accelerometer outputs'); set(ti,'fontsize',Cal.Font_title);
    grid on; set(gca,'FontSize',Cal.Font_axis);
    subplot(2,1,2);
    plot(da(:,col_t),da(:,col_accel(1)),da(:,col_t),da(:,col_accel(2)),da(:,col_t),da(:,col_accel(3)),'linewidth',Cal.Font_linewidth);
    yi=ylabel('m/s^2'); set(yi,'fontsize',Cal.Font_label);
    li=legend('Ax','Ay','Az'); set(li,'fontsize',Cal.Font_legent);
    grid on; set(gca,'FontSize',Cal.Font_axis);
    xi=xlabel('Time (sec)'); set(xi,'fontsize',Cal.Font_label);

    figure,
    subplot(3,1,1);
    plot(da(:,col_t),da(:,col_mag(1)),da(:,col_t),da(:,col_mag(2)),da(:,col_t),da(:,col_mag(3)),'linewidth',Cal.Font_linewidth);
    yi=ylabel('mGauss'); set(yi,'fontsize',Cal.Font_label);
    li=legend('Mx','My','Mz'); set(li,'fontsize',Cal.Font_legent);
    ti=title('Magnetometer, barometer, and temperature outputs'); set(ti,'fontsize',Cal.Font_title);
    grid on; set(gca,'FontSize',Cal.Font_axis);
    subplot(3,1,2);
    plot(da(:,col_t),da(:,col_baro),'linewidth',Cal.Font_linewidth);
    yi=ylabel('hPa'); set(yi,'fontsize',Cal.Font_label);
    li=legend('Bx'); set(li,'fontsize',Cal.Font_legent);
    grid on; set(gca,'FontSize',Cal.Font_axis);
    subplot(3,1,3);
    plot(da(:,col_t),da(:,col_temper),'linewidth',Cal.Font_linewidth);
    yi=ylabel('^oC'); set(yi,'fontsize',Cal.Font_label);
    li=legend('Tx'); set(li,'fontsize',Cal.Font_legent);
    ti=title('Temperature'); set(ti,'fontsize',Cal.Font_title);
    xi=xlabel('Time (sec)'); set(xi,'fontsize',Cal.Font_label);
    grid on; set(gca,'FontSize',Cal.Font_axis);
end

