function [da_gps] = read_gps(f_gps,Nav)

if Nav.if_use_gps == 1
    da_gps = load(f_gps);
    
    fgpskml=fopen([f_gps(1:length(f_gps)-4) '.kml'],'w+');

    fprintf(fgpskml,Nav.str_kml_pin_title_blue);
    for i=1:size(da_gps,1)
        fprintf(fgpskml,Nav.str_kml_pin_point,da_gps(i,3),da_gps(i,2),da_gps(i,3),da_gps(i,2));
    end
    fprintf(fgpskml,Nav.str_kml_pin_end);
    fclose(fgpskml); 
    
    da_gps(:,2:3) = da_gps(:,2:3) * pi/180;
    
%     i_reliable_gps = find(da_gps(:,5)<16);
%     da_gps = da_gps(i_reliable_gps, :);
    
else
    da_gps = 0;
end




