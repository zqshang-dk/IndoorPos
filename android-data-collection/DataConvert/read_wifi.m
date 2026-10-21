function [da_wifi] = read_wifi(f_wifi,Nav)

if Nav.if_use_wifi == 1
    fid=fopen(f_wifi,'r');
    iii_line = 0;
    t_wifi_0 = -999;

    %da_wifi = struct('time',{zeros()});
    da_wifi.i_eph = 0;

    if fid==-1
        disp('File does not exist'); 
    end
    nextline = fgetl(fid);
    while isstr(nextline)   
        iii_line = iii_line + 1;
        temp =textscan(nextline,'%f %s %d %s');

        if (temp{1} ~= t_wifi_0)
            da_wifi.i_eph = da_wifi.i_eph + 1;
            da_wifi.eph(da_wifi.i_eph).i_ap = 1;
            da_wifi.eph(da_wifi.i_eph).time = temp{1};
            %da_wifi.eph(da_wifi.i_eph).num = 1;
            temp2 = temp{2};
            temp2 = temp2{1};
            da_wifi.eph(da_wifi.i_eph).ap(da_wifi.eph(da_wifi.i_eph).i_ap).mac = temp2;
            da_wifi.eph(da_wifi.i_eph).ap(da_wifi.eph(da_wifi.i_eph).i_ap).ss = temp{3};
            da_wifi.eph(da_wifi.i_eph).ap(da_wifi.eph(da_wifi.i_eph).i_ap).name = temp{4};
            t_wifi_0 = temp{1};
        else
            da_wifi.eph(da_wifi.i_eph).i_ap = da_wifi.eph(da_wifi.i_eph).i_ap + 1;
            %da_wifi.eph(da_wifi.i_eph).num = da_wifi(i_epoch).num + 1;
            temp2 = temp{2};
            temp2 = temp2{1};
            da_wifi.eph(da_wifi.i_eph).ap(da_wifi.eph(da_wifi.i_eph).i_ap).mac = temp2;
            da_wifi.eph(da_wifi.i_eph).ap(da_wifi.eph(da_wifi.i_eph).i_ap).ss = temp{3};
            da_wifi.eph(da_wifi.i_eph).ap(da_wifi.eph(da_wifi.i_eph).i_ap).name = temp{4};
            t_wifi_0 = temp{1};
        end

        nextline = fgetl(fid);
    end
    fprintf('Originally %d Wi-Fi epochs\n', da_wifi.i_eph);

    sta=fclose(fid); 
    if sta == -1  
        disp('File not closed');
    end

    % Settingthethresholdto-85dBm
    Th_db = Nav.wifi_th_db;
    for i=1:da_wifi.i_eph
        for j=da_wifi.eph(i).i_ap:-1:1
            if da_wifi.eph(i).ap(j).ss <= Th_db
                da_wifi.eph(i).ap(j) = [];
                da_wifi.eph(i).i_ap = da_wifi.eph(i).i_ap - 1;
            end        
        end     
    end
    for i=da_wifi.i_eph:-1:1
        if da_wifi.eph(i).i_ap == 0
            da_wifi.eph(i) = [];
            da_wifi.i_eph = da_wifi.i_eph - 1;
        end
    end
    fprintf('Setting the threshold of Wi-Fi signals to %d dBm\n', Th_db);
    
    %% Add Data (for matching Navculation)
    for i=1:da_wifi.i_eph
        int_data = zeros(da_wifi.eph(i).i_ap, 2);
        %da_wifi1.eph(i).data = zeros(da_wifi1.eph(i).i_ap, 2);
        for j=1:da_wifi.eph(i).i_ap
            strmac = da_wifi.eph(i).ap(j).mac;
            int_mac = hex2dec(strmac(1:2))*100000+hex2dec(strmac(4:5))*10000+hex2dec(strmac(7:8))*1000+ ...
                     hex2dec(strmac(10:11))*100+hex2dec(strmac(13:14))*10+hex2dec(strmac(16:17))*1;
            int_ss = da_wifi.eph(i).ap(j).ss;
            int_data(j,:) = [int_mac, int_ss];        
        end
        da_wifi.eph(i).data = int_data;
    end
    
    %% Delete the same epoch
    for i=da_wifi.i_eph:-1:2
        if sum(da_wifi.eph(i).data(:,1))==sum(da_wifi.eph(i-1).data(:,1)) && ...
           sum(da_wifi.eph(i).data(:,2))==sum(da_wifi.eph(i-1).data(:,2))
            da_wifi.eph(i) = [];
            da_wifi.i_eph = da_wifi.i_eph - 1;
        end
    end
    fprintf('Finally %d Wi-Fi epochs\n', da_wifi.i_eph); 
    
else
    da_wifi = 0;
end

