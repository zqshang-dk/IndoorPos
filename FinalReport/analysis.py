from pathlib import Path
import csv
import math
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(r"D:\Course\IndoorPos")
OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"
RES = OUT / "results"
FIG.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.unicode_minus": False,
                     "figure.dpi": 150, "savefig.dpi": 180})

def save_figure(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png")
    fig.savefig(FIG / f"{name}.pdf")
    plt.close(fig)

def table(path):
    return np.loadtxt(path)

def save_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

def fingerprint():
    d = ROOT / "数据-信号强度指纹识别"
    loc = table(d / "rp_loc.txt")
    train, test = table(d / "database.data"), table(d / "test1_with_ref.data")
    aps, missing, k, min_common = 30, -110.0, 3, 3
    means, counts = {}, {}
    for row in train:
        pid = int(row[0]); means.setdefault(pid, np.zeros(aps)); counts.setdefault(pid, np.zeros(aps, dtype=int))
        valid = row[1:] != missing
        means[pid][valid] += row[1:][valid]; counts[pid][valid] += 1
    locmap = {int(r[0]): r[1:4] for r in loc}
    for pid in means:
        mask = counts[pid] > 0
        means[pid][mask] /= counts[pid][mask]
        means[pid][~mask] = missing
    out, errs = [], []
    for row in test:
        obs = row[1:31]; valid_aps = int(np.sum(obs != missing)); candidates = []
        for pid in locmap:
            common = (obs != missing) & (counts[pid] > 0)
            n = int(common.sum())
            if n < min_common: continue
            rms = float(np.sqrt(np.mean((obs[common] - means[pid][common]) ** 2)))
            score = (n / valid_aps) / (1 + rms)
            candidates.append((score, pid))
        candidates.sort(key=lambda x: (-x[0], x[1]))
        selected = candidates[:k]
        if not selected:
            out.append([row[0], *([math.nan] * 10), valid_aps, 0, 0]); continue
        sw = sum(s for s, _ in selected)
        pos = sum((s * locmap[p] for s, p in selected), np.zeros(3)) / sw
        ref = row[31:34]; delta = pos[:2] - ref[:2]; err = float(np.linalg.norm(delta)); errs.append(err)
        out.append([row[0], *pos, *ref, *delta, err, valid_aps, len(selected), 1])
    save_csv(RES / "fingerprint_result.csv", ["time_s","east_m","north_m","z_m","ref_east_m","ref_north_m","ref_z_m","error_e_m","error_n_m","error_2d_m","valid_aps","neighbors_used","success"], out)
    e = np.array(errs)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(loc[:,1], loc[:,2], s=12, c="#6c757d", label="Reference points")
    ax.plot(test[:,31], test[:,32], "k--", lw=1.2, label="Reference path")
    a = np.array(out, dtype=float)
    ax.plot(a[:,1], a[:,2], color="#d1495b", lw=1.3, label="Weighted KNN")
    ax.set(xlabel="East (m)", ylabel="North (m)", title="RSS fingerprint positioning")
    ax.axis("equal"); ax.grid(alpha=.25); ax.legend(); save_figure(fig, "fingerprint_track")
    fig, ax = plt.subplots(figsize=(7, 4.5)); ax.plot(np.sort(e), np.arange(1,len(e)+1)/len(e), color="#00798c")
    ax.set(xlabel="Horizontal error (m)", ylabel="Empirical CDF", title="Fingerprint error distribution", ylim=(0,1)); ax.grid(alpha=.25); save_figure(fig, "fingerprint_cdf")
    return {"n":len(e), "mean":float(e.mean()), "rmse":float(np.sqrt(np.mean(e**2))), "median":float(np.median(e)), "p95":float(np.percentile(e,95)), "max":float(e.max()), "train":len(train), "points":len(loc)}

def fingerprint_k_sensitivity():
    d = ROOT / "数据-信号强度指纹识别"
    loc = table(d / "rp_loc.txt")
    train, test = table(d / "database.data"), table(d / "test1_with_ref.data")
    locmap = {int(r[0]): r[1:3] for r in loc}
    sums, counts = {}, {}
    for row in train:
        pid = int(row[0]); sums.setdefault(pid, np.zeros(30)); counts.setdefault(pid, np.zeros(30, int))
        valid = row[1:] != -110.0
        sums[pid][valid] += row[1:][valid]; counts[pid][valid] += 1
    means = {pid: np.divide(sums[pid], counts[pid], out=np.full(30, -110.0), where=counts[pid] > 0) for pid in sums}
    rows, stats = [], []
    for k in (1, 2, 3, 5, 7, 10):
        errors = []
        for row in test:
            obs, candidates = row[1:31], []
            for pid, mean in means.items():
                common = (obs != -110.0) & (counts[pid] > 0)
                n = int(common.sum())
                if n < 3: continue
                rms = float(np.sqrt(np.mean((obs[common] - mean[common]) ** 2)))
                score = (n / max(1, int(np.sum(obs != -110.0)))) / (1 + rms)
                candidates.append((score, pid))
            candidates.sort(key=lambda x: (-x[0], x[1]))
            chosen = candidates[:k]
            if not chosen: continue
            weights = np.array([s for s, _ in chosen])
            pos = np.average(np.array([locmap[p] for _, p in chosen]), axis=0, weights=weights)
            err = float(np.linalg.norm(pos - row[31:33]))
            errors.append(err); rows.append([k, row[0], pos[0], pos[1], row[31], row[32], err])
        e = np.asarray(errors)
        stats.append([k, len(e), float(np.mean(e)), float(np.sqrt(np.mean(e**2))), float(np.median(e)), float(np.percentile(e, 95))])
    save_csv(RES / "fingerprint_k_sensitivity.csv", ["K","n","mean_m","rmse_m","median_m","p95_m"], stats)
    save_csv(RES / "fingerprint_k_errors.csv", ["K","time_s","east_m","north_m","ref_east_m","ref_north_m","error_m"], rows)
    a = np.asarray(stats)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(a[:,0], a[:,3], "o-", label="RMSE"); ax.plot(a[:,0], a[:,2], "s--", label="Mean error")
    ax.set(xlabel="Number of neighbors K", ylabel="Horizontal error (m)", title="Fingerprint sensitivity to K")
    ax.set_xticks(a[:,0]); ax.grid(alpha=.25); ax.legend(); save_figure(fig, "fingerprint_k_sensitivity")
    return stats

def pdr():
    # The C++ PDR executable writes its output in src/PDR. Read its saved trajectory
    # without modifying the original project; compare it to time-matched reference fixes.
    src = ROOT / "src" / "PDR" / "pdr_output"
    data = np.genfromtxt(src / "pdr_result.csv", delimiter=",", names=True)
    ref = table(ROOT / "数据-行人航迹推算" / "pos_reference.txt")
    lat0, lon0 = ref[0,1:3]; R = 6378137.0
    east = np.deg2rad(ref[:,2]-lon0)*R*np.cos(np.deg2rad(lat0))
    north = np.deg2rad(ref[:,1]-lat0)*R
    re = np.interp(data["time_s"], ref[:,0], east); rn = np.interp(data["time_s"], ref[:,0], north)
    keep = data["is_step"] > 0
    error = np.hypot(data["east_corrected_m"][keep]-re[keep], data["north_corrected_m"][keep]-rn[keep])
    save_csv(RES / "pdr_step_errors.csv", ["time_s","east_m","north_m","ref_east_m","ref_north_m","error_m"],
             zip(data["time_s"][keep], data["east_corrected_m"][keep], data["north_corrected_m"][keep], re[keep], rn[keep], error))
    fig, ax = plt.subplots(figsize=(7,6)); ax.plot(east,north,"k-",lw=1.4,label="Reference")
    ax.plot(data["east_mag_m"],data["north_mag_m"],color="#00798c",lw=1,label="Magnetometer")
    ax.plot(data["east_corrected_m"],data["north_corrected_m"],color="#d1495b",lw=1,label="Gyroscope, bias-adjusted")
    ax.set(xlabel="East (m)",ylabel="North (m)",title="PDR trajectory and reference"); ax.axis("equal"); ax.grid(alpha=.25); ax.legend(); save_figure(fig, "pdr_track")
    fig, axes = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
    axes[0].plot(data["time_s"], data["acc_norm_mps2"], color="#00798c", lw=.7)
    axes[0].scatter(data["time_s"][keep], data["acc_norm_mps2"][keep], s=8, color="#d1495b", label="Detected steps")
    axes[0].set_ylabel("Acceleration norm (m/s$^2$)"); axes[0].legend(loc="upper right")
    axes[1].plot(data["time_s"], np.rad2deg(data["roll_smooth_rad"]), label="Roll")
    axes[1].plot(data["time_s"], np.rad2deg(data["pitch_smooth_rad"]), label="Pitch")
    axes[1].set_ylabel("Angle (deg)"); axes[1].legend(ncol=2)
    axes[2].plot(data["time_s"], np.rad2deg(np.unwrap(data["heading_mag_rad"])), label="Magnetic heading")
    axes[2].plot(data["time_s"], np.rad2deg(np.unwrap(data["heading_corrected_rad"])), label="Bias-adjusted gyro")
    axes[2].set_ylabel("Heading (deg)"); axes[2].set_xlabel("Time (s)"); axes[2].legend(ncol=2)
    for ax in axes: ax.grid(alpha=.25)
    axes[0].set_title("PDR signals, attitude, heading and detected steps")
    save_figure(fig, "pdr_signals")
    fig, axes = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
    for ax, cols, scale, ylabel, title in (
        (axes[0], ("ax_mps2", "ay_mps2", "az_mps2"), 1.0, "Acceleration (m/s$^2$)", "Accelerometer"),
        (axes[1], ("gx_rad_s", "gy_rad_s", "gz_rad_s"), 1.0, "Angular rate (rad/s)", "Gyroscope"),
        (axes[2], ("mx_T", "my_T", "mz_T"), 1e6, "Magnetic field ($\\mu$T)", "Magnetometer")):
        for col, axis in zip(cols, ("x", "y", "z")):
            ax.plot(data["time_s"], data[col] * scale, lw=.55, label=axis)
        ax.set_ylabel(ylabel); ax.set_title(title, loc="left", fontsize=10)
        ax.grid(alpha=.25); ax.legend(ncol=3, fontsize=8, loc="upper right")
    axes[-1].set_xlabel("Time (s)")
    save_figure(fig, "pdr_raw_sensors")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(data["time_s"][keep], error, color="#d1495b", lw=1, label="Bias-adjusted gyro PDR")
    ax.axhline(np.sqrt(np.mean(error**2)), color="#00798c", ls="--", label=f"RMSE = {np.sqrt(np.mean(error**2)):.2f} m")
    ax.set(xlabel="Time (s)", ylabel="Horizontal error (m)", title="PDR error at detected step times")
    ax.grid(alpha=.25); ax.legend(); save_figure(fig, "pdr_error_time")
    return {"samples":len(data),"steps":int(keep.sum()),"start":float(data['time_s'][0]),"end":float(data['time_s'][-1]),"mean":float(error.mean()),"rmse":float(np.sqrt(np.mean(error**2))),"p95":float(np.percentile(error,95)),"terminal":float(error[-1])}

def existing_distance():
    # Preserve provenance: these are stored outputs from the supplied C++ programs.
    d = ROOT / "数据-距离交会" / "数据3-教室-Ultrasonic"
    r = np.genfromtxt(d / "result_classroom_cpp.csv", delimiter=",", names=True, encoding="utf-8")
    ref = np.genfromtxt(d / "ref_pos.txt", delimiter=",")
    # genfromtxt infers the textual status column as float/NaN; successful rows
    # are unambiguously those with finite solution coordinates.
    ok = np.isfinite(r["x_m"]) & np.isfinite(r["y_m"])
    east = np.interp(r["time_s"][ok], ref[:,0], ref[:,1])
    north = np.interp(r["time_s"][ok], ref[:,0], ref[:,2])
    error = np.hypot(r["x_m"][ok] - east, r["y_m"][ok] - north)
    save_csv(RES / "classroom_distance_result.csv", ["time_s","east_m","north_m","ref_east_m","ref_north_m","error_m","range_rms_m"],
             zip(r["time_s"][ok], r["x_m"][ok], r["y_m"][ok], east, north, error, r["range_rms_m"][ok]))
    fig, ax = plt.subplots(figsize=(7, 5)); ax.plot(ref[:,1],ref[:,2],"k-",lw=1.2,label="Reference")
    ax.plot(r["x_m"][ok],r["y_m"][ok],color="#d1495b",lw=.8,label="Stored C++ solution")
    ax.set(xlabel="East / local x (m)",ylabel="North / local y (m)",title="Classroom ultrasonic range intersection"); ax.axis("equal"); ax.grid(alpha=.25); ax.legend(); save_figure(fig, "classroom_range_track")
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    t = r["time_s"][ok]
    axes[0].plot(t, error, color="#d1495b", lw=.8)
    axes[0].axhline(np.sqrt(np.mean(error**2)), color="#00798c", ls="--", label=f"RMSE = {np.sqrt(np.mean(error**2)):.3f} m")
    axes[0].set_ylabel("Horizontal error (m)"); axes[0].legend()
    axes[1].plot(t, r["range_rms_m"][ok], color="#edae49", lw=.8)
    axes[1].set(xlabel="Time (s)", ylabel="Range-fit RMS (m)")
    for ax in axes: ax.grid(alpha=.25)
    axes[0].set_title("Classroom position error and range-fit residual")
    save_figure(fig, "classroom_error_residual")
    return {"rows":len(r),"ok":int(ok.sum()),"range_rms_median":float(np.median(r["range_rms_m"][ok])),"mean_error":float(error.mean()),"rmse":float(np.sqrt(np.mean(error**2))),"p95":float(np.percentile(error,95)),"max":float(error.max())}

def uwb_tag2():
    d = ROOT / "数据-距离交会" / "数据2-小车-UWB"
    est = np.genfromtxt(d / "result_tag_2_cpp.csv", delimiter=",", names=True, encoding="utf-8")
    truth = table(d / "true_position_tag_2.txt")
    et, ei, ti = np.intersect1d(est["time_ms"], truth[:,0], return_indices=True)
    p, q = est[ei], truth[ti,1:4]
    delta = np.column_stack((p["x_m"], p["y_m"], p["z_m"])) - q
    eh = np.linalg.norm(delta[:,:2], axis=1)
    save_csv(RES / "uwb_tag2_time_aligned.csv", ["time_ms","x_m","y_m","z_m","true_x_m","true_y_m","true_z_m","error_x_m","error_y_m","error_z_m","error_2d_m","error_3d_m"],
             zip(et, p["x_m"], p["y_m"], p["z_m"], q[:,0], q[:,1], q[:,2], delta[:,0], delta[:,1], delta[:,2], eh, np.linalg.norm(delta,axis=1)))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].plot(q[:,0], q[:,1], "k-", lw=1.1, label="Reference")
    axes[0].plot(p["x_m"], p["y_m"], color="#d1495b", lw=.8, label="UWB solution")
    axes[0].set(xlabel="X (m)", ylabel="Y (m)", title="Tag 2 horizontal trajectory"); axes[0].axis("equal"); axes[0].legend()
    axes[1].plot((et - et[0]) / 1000.0, eh, color="#00798c", lw=.7)
    axes[1].set(xlabel="Elapsed time from first matched epoch (s)", ylabel="Horizontal error (m)", title="Timestamp-matched error")
    for ax in axes: ax.grid(alpha=.25)
    save_figure(fig, "uwb_tag2_track_error")
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    elapsed = (et - et[0]) / 1000.0
    axes[0].plot(elapsed, q[:,2], color="#00798c", lw=.8, label="Reference z")
    axes[0].plot(elapsed, p["z_m"], color="#d1495b", lw=.8, label="Estimated z")
    axes[0].set_ylabel("Height (m)"); axes[0].legend(ncol=2)
    axes[1].plot(elapsed, delta[:,2], color="#edae49", lw=.8)
    axes[1].axhline(float(np.mean(delta[:,2])), color="#00798c", ls="--", label=f"Mean bias = {np.mean(delta[:,2]):.3f} m")
    axes[1].set(xlabel="Elapsed time from first matched epoch (s)", ylabel="Vertical error (m)")
    axes[1].legend()
    for ax in axes: ax.grid(alpha=.25)
    axes[0].set_title("UWB tag 2 vertical estimate and error")
    save_figure(fig,"uwb_tag2_vertical_error")
    return {"estimate_rows":len(est),"truth_rows":len(truth),"matched":len(et),"horizontal_rmse":float(np.sqrt(np.mean(eh**2))),"horizontal_mean":float(eh.mean()),"horizontal_p95":float(np.percentile(eh,95)),"vertical_bias":float(np.mean(delta[:,2])),"vertical_rmse":float(np.sqrt(np.mean(delta[:,2]**2)))}

def android_sample():
    d = ROOT / "android-data-collection" / "SenDa2" / "20150401055443"
    sensors = np.loadtxt(d / "sensors.txt")
    base = sensors[:,1].min()
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    for typ, label, scale in ((1,"Gyroscope (deg/s)",1.0),(2,"Accelerometer (m/s$^2$)",1.0),(3,"Magnetometer (raw units)",1.0)):
        rows = sensors[:,0] == typ
        if typ == 1: ax=axes[0]
        else: ax=axes[1]
        vals=sensors[rows]
        for j, axis in enumerate(("x","y","z")):
            ax.plot(vals[:,1]-base, vals[:,j+2]*scale, lw=.55, label=f"{label.split()[0]} {axis}")
        if typ != 1: break
    axes[0].set_ylabel("Angular rate (deg/s)"); axes[1].set_ylabel("Acceleration (m/s$^2$)")
    axes[1].set_xlabel("Time from session start (s)")
    for ax in axes: ax.grid(alpha=.25); ax.legend(ncol=3, fontsize=8)
    axes[0].set_title("Android inertial samples (types 1 and 2)")
    save_figure(fig, "android_inertial_timeseries")
    # Wi-Fi records are time, BSSID, RSS(dBm), SSID; summarize scans by timestamp.
    scans = {}
    with (d / "wifi.txt").open(encoding="utf-8") as f:
        for line in f:
            fields=line.strip().split(" ", 3)
            if len(fields) < 3: continue
            try: ts=float(fields[0]); rss=float(fields[2])
            except ValueError: continue
            scans.setdefault(ts, []).append((fields[1],rss))
    counts=[len(v) for v in scans.values()]
    macs={mac for values in scans.values() for mac,_ in values}
    fig, ax=plt.subplots(figsize=(8,4.2))
    ax.plot(list(scans), counts, color="#d1495b", lw=.8)
    ax.set(xlabel="Time from session start (s)", ylabel="Visible AP records per scan", title="Wi-Fi scan density in Android session")
    ax.grid(alpha=.25); save_figure(fig,"android_wifi_scan_density")
    ap_counts = {mac: sum(any(m == mac for m, _ in values) for values in scans.values()) for mac in macs}
    top_aps = sorted(ap_counts, key=lambda mac: (-ap_counts[mac], mac))[:4]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for mac in top_aps:
        points = [(ts, rss) for ts, values in scans.items() for bssid, rss in values if bssid == mac]
        points.sort()
        ax.plot([p[0] for p in points], [p[1] for p in points], marker=".", ms=2.5, lw=.7,
                label=f"{mac} ({len(points)} samples)")
    ax.set(xlabel="Time from session start (s)", ylabel="Received signal strength (dBm)",
           title="RSS time series of four most frequently observed BSSIDs")
    ax.grid(alpha=.25); ax.legend(fontsize=7, ncol=2); save_figure(fig,"android_wifi_rss_timeseries")
    save_csv(RES / "android_wifi_scan_summary.csv", ["scan_count","unique_bssid","mean_records_per_scan","min_rss_dbm","max_rss_dbm"],
             [[len(scans),len(macs),float(np.mean(counts)),min(r for v in scans.values() for _,r in v),max(r for v in scans.values() for _,r in v)]])
    return {"sensor_rows":len(sensors),"gyro_rows":int(np.sum(sensors[:,0]==1)),"accel_rows":int(np.sum(sensors[:,0]==2)),"mag_rows":int(np.sum(sensors[:,0]==3)),"wifi_scans":len(scans),"unique_bssid":len(macs),"mean_aps_per_scan":float(np.mean(counts)),"top_bssids":top_aps}

if __name__ == "__main__":
    print("FINGERPRINT", fingerprint())
    print("PDR_STORED_EXECUTABLE_OUTPUT", pdr())
    print("CLASSROOM_STORED_CPP_OUTPUT", existing_distance())
    print("FINGERPRINT_K_SENSITIVITY", fingerprint_k_sensitivity())
    print("UWB_TAG2_TIMESTAMP_MATCH", uwb_tag2())
    print("ANDROID_SAMPLE", android_sample())
