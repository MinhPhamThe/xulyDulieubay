import pandas as pd
import matplotlib.pyplot as plt
from pymavlink import mavutil
from math import radians, sin, cos, sqrt, atan2
import matplotlib.ticker as ticker
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import threading
import math

# Khai báo biến file_path
file_path = ""
save_directory = ""
start_time = None
end_time = None

# Hàm tính khoảng cách giữa hai tọa độ GPS bằng công thức Haversine
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Bán kính trái đất tính theo km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c * 1000  # Đổi sang mét
    return distance

# Hàm chuyển đổi thời gian thành chuỗi "xx phút yy s"
def format_time(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}p {remaining_seconds}s"


def open_file():
    global file_path  # Sử dụng biến toàn cục
    # Mở hộp thoại chọn file
    file_path = filedialog.askopenfilename()
    if file_path:
        # Hiển thị đường dẫn file trong Entry box
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(0, file_path)

def select_save_directory():
    global save_directory
    save_directory = filedialog.askdirectory()
    if save_directory:
        # Hiển thị đường dẫn thư mục lưu trong Entry box
        entry_save_path.delete(0, tk.END)
        entry_save_path.insert(0, save_directory)

# Tính toán các mốc thời gian
def calculate_time_tlog(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    throttle = []
    first_throttle_100pct = None

    while True:
        msg = mavlog.recv_match(blocking=False)
        if msg is None:
            break

        # Kiểm tra nếu thông báo chứa thông tin throttle
        if msg.get_type() == 'VFR_HUD':
            throttle = msg.throttle
            time = msg._timestamp
            times.append(time)

            # Kiểm tra nếu throttle đạt 100 và lưu thời gian lần đầu tiên
            if throttle == 100 and first_throttle_100pct is None:
                first_throttle_100pct = time

    # Chuẩn hóa thời gian bắt đầu
    first_throttle_100pct = first_throttle_100pct - times[0]
    return(first_throttle_100pct)

#Vẽ đồ thị độ cao
def plot_altitude_tlog(file_path):
    # Tạo đối tượng mavlink để đọc tệp
    mavlog = mavutil.mavlink_connection(file_path)

    # Danh sách lưu trữ dữ liệu
    times = []
    altitude_relative = []
    altitude_amsl = []
    start_time_inair = calculate_time_tlog(file_path)
    # Đọc từng message trong file
    while True:
        # Nhận thông báo từ file
        msg = mavlog.recv_match(blocking=False)
        if msg is None:
            break

        # Kiểm tra loại thông báo là GLOBAL_POSITION_INT
        if msg.get_type() == 'GLOBAL_POSITION_INT':
            # Lấy thời gian (milliseconds) và chuyển thành giây
            time = msg.time_boot_ms / 1000.0
            times.append(time)

            # Lấy giá trị cao độ (đơn vị cm -> chuyển đổi sang mét)
            altitude_relative.append(msg.relative_alt / 1000.0)
            altitude_amsl.append(msg.alt / 1000.0)

    # Trừ đi thời gian bắt đầu để thời gian bay bắt đầu từ 0
    start_time = times[0]
    times = [t - start_time for t in times]

    plt.figure(figsize=(19.2, 10.8))

    plt.axvline(start_time_inair, color='red', linestyle='--')
    plt.text(start_time_inair + 1.0 , 0, f"Bắt đầu = {format_time(start_time_inair)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')

    # Vẽ cao độ tương đối
    plt.plot(times, altitude_relative, label="Độ cao tương đối (m)", color="blue")
    
    # Vẽ cao độ so với mực nước biển
    plt.plot(times, altitude_amsl, label="Độ cao so với mực nước biển (m)", color="green")

    # Tìm giá trị đỉnh của từng độ cao
    max_alt_rel = max(altitude_relative)
    max_alt_amsl = max(altitude_amsl)
    
    # Thời điểm của các giá trị đỉnh
    max_time_rel = times[altitude_relative.index(max_alt_rel)]
    max_time_amsl = times[altitude_amsl.index(max_alt_amsl)]

    # Đặt tên cho đồ thị và trục
    plt.title("Độ cao bay")
    plt.xlabel("Thời gian bay")
    plt.ylabel("m")

    # Hiển thị chú thích
    plt.legend()

    # Đánh dấu các giá trị đỉnh
    plt.scatter(max_time_rel, max_alt_rel, color="blue", marker="o")
    plt.text(max_time_rel, max_alt_rel, f"{max_alt_rel:.2f} m", color="blue")
    
    plt.scatter(max_time_amsl, max_alt_amsl, color="green", marker="o")
    plt.text(max_time_amsl, max_alt_amsl, f"{max_alt_amsl:.2f} m", color="green")

    # Đặt khoảng cách mốc trên trục x là 100 giây
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    
    plt.xticks(rotation=90)

    # Hiển thị đồ thị
    plt.grid()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "docao.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
def plot_altitude_csv(file_path):
    # Đọc dữ liệu từ file CSV
    data = pd.read_csv(file_path)
    
    # Giả định rằng các cột 'flightTime', 'altitudeRelative' và 'altitudeAMSL' tồn tại
    # Chuyển đổi định dạng thời gian từ 'HH:MM:SS' sang giây
    times = pd.to_timedelta(data['flightTime']).dt.total_seconds().values  # Chuyển đổi sang giây
    altitude_relative = data['altitudeRelative'].astype(float).values  # Lấy giá trị độ cao tương đối
    altitude_amsl = data['altitudeAMSL'].astype(float).values  # Lấy giá trị độ cao AMSL
    
    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = times - start_time

    plt.figure(figsize=(19.2, 10.8))
    plt.axvline(start_time, color='red', linestyle='--')
    plt.text(start_time + 1.0 , 0, f"Bắt đầu = {format_time(start_time)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')
    # Vẽ độ cao tương đối
    plt.plot(times, altitude_relative, label="Độ cao tương đối (m)", color="green")
    # Vẽ độ cao AMSL
    plt.plot(times, altitude_amsl, label="Độ cao so với mực nước biển (m)", color="blue")

    # Tìm giá trị đỉnh của altitudeRelative
    max_altitude_relative = max(altitude_relative)
    max_time_relative = times[altitude_relative.argmax()]  # Tìm chỉ số giá trị lớn nhất

    # Tìm giá trị đỉnh của altitudeAMSL
    max_altitude_amsl = max(altitude_amsl)
    max_time_amsl = times[altitude_amsl.argmax()]  # Tìm chỉ số giá trị lớn nhất

    # Đặt tên cho đồ thị và trục
    plt.title("Độ cao bay")
    plt.xlabel("Thời gian bay")
    plt.ylabel("Độ cao (m)")

    # Hiển thị chú thích
    plt.legend()

    # Đánh dấu giá trị đỉnh cho altitudeRelative
    plt.scatter(max_time_relative, max_altitude_relative, color="green", marker="o")
    plt.text(max_time_relative, max_altitude_relative, f"{max_altitude_relative:.2f} m", color="green")

    # Đánh dấu giá trị đỉnh cho altitudeAMSL
    plt.scatter(max_time_amsl, max_altitude_amsl, color="blue", marker="o")
    plt.text(max_time_amsl, max_altitude_amsl, f"{max_altitude_amsl:.2f} m", color="blue")

    # Đặt khoảng cách mốc trên trục x là 100 giây và xoay dọc
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)


    # Hiển thị đồ thị
    plt.grid()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "docao.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ

#Vẽ đồ thị tầm xa bay
def plot_distance_to_home_tlog(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    distance_to_home = []
    home_position = None
    start_time_inair = calculate_time_tlog(file_path)
    while True:
        msg = mavlog.recv_match(blocking=False)
        if msg is None:
            break

        if msg.get_type() == 'GLOBAL_POSITION_INT':
            time = msg.time_boot_ms / 1000.0  # Thời gian tính bằng giây
            times.append(time)

            # Lấy tọa độ hiện tại
            current_lat = msg.lat / 1e7
            current_lon = msg.lon / 1e7

            # Xác định điểm Home nếu chưa có
            if home_position is None:
                home_position = (current_lat, current_lon)

            # Tính khoảng cách đến Home
            dist_to_home = haversine(home_position[0], home_position[1], current_lat, current_lon)
            distance_to_home.append(dist_to_home)

    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = [t - start_time for t in times]

    plt.figure(figsize=(19.2, 10.8))
    plt.axvline(start_time_inair, color='red', linestyle='--')
    plt.text(start_time_inair + 1.0 , 0, f"Bắt đầu = {format_time(start_time_inair)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')
    # Vẽ khoảng cách đến Home
    plt.plot(times, distance_to_home, label=" Tầm xa ", color="blue")

    # Tìm giá trị đỉnh của khoảng cách đến Home
    max_dist = max(distance_to_home)
    max_time = times[distance_to_home.index(max_dist)]

    # Đặt tên cho đồ thị và trục
    plt.title("Tầm xa")
    plt.xlabel("Thời gian bay")
    plt.ylabel("m")

    # Hiển thị chú thích
    plt.legend()

    # Đánh dấu giá trị đỉnh
    plt.scatter(max_time, max_dist, color="purple", marker="o")
    plt.text(max_time, max_dist, f"{max_dist:.2f} m", color="blue")

    # Đặt khoảng cách mốc trên trục x là 100 giây và xoay dọc
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    # Hiển thị đồ thị
    plt.grid()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "tamxa.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ
def plot_distance_to_home_csv(file_path):
    # Đọc dữ liệu từ file CSV
    data = pd.read_csv(file_path)
    
    # Giả định rằng các cột 'flightTime', 'distanceToHome' tồn tại
    # Chuyển đổi định dạng thời gian từ 'HH:MM:SS' sang giây
    times = pd.to_timedelta(data['flightTime']).dt.total_seconds().values  # Chuyển đổi sang giây
    distance_to_home = data['distanceToHome'].astype(float).values  # Lấy giá trị khoảng cách đến nhà
    
    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = times - start_time
    plt.figure(figsize=(19.2, 10.8))
    plt.axvline(start_time, color='red', linestyle='--')
    plt.text(start_time + 1.0 , 0, f"Bắt đầu = {format_time(start_time)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')
    # Vẽ khoảng cách đến nhà
    plt.plot(times, distance_to_home, label="Tầm xa (m)", color="blue")

    # Tìm giá trị đỉnh của distanceToHome
    max_distance = max(distance_to_home)
    max_time = times[distance_to_home.argmax()]  # Tìm chỉ số giá trị lớn nhất

    # Đặt tên cho đồ thị và trục
    plt.title("Tầm xa")
    plt.xlabel("Thời gian bay")
    plt.ylabel("Tầm xa(m)")

    # Hiển thị chú thích
    plt.legend()

    # Đánh dấu giá trị đỉnh cho distanceToHome
    plt.scatter(max_time, max_distance, color="orange", marker="o")
    plt.text(max_time, max_distance, f"{max_distance:.2f} m", color="blue")

    # Đặt khoảng cách mốc trên trục x là 100 giây và xoay dọc
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    # Hiển thị đồ thị
    plt.grid()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "tamxa.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ

# Vẽ đồ thị tốc độ bay
def plot_groundspeed_tlog(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    groundspeeds = []
    start_time_inair = calculate_time_tlog(file_path)
    while True:
        msg = mavlog.recv_match(blocking=False)
        if msg is None:
            break

        # Kiểm tra nếu thông báo chứa thông tin groundspeed
        if msg.get_type() == 'VFR_HUD':  # `VFR_HUD` chứa thông tin `groundspeed`
            time = msg._timestamp  # Lấy timestamp
            times.append(time)
            groundspeeds.append(msg.groundspeed * 3.6)  # Tốc độ mặt đất trong m/s

    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = [t - start_time for t in times]
    plt.figure(figsize=(19.2, 10.8))
    plt.axvline(start_time_inair, color='red', linestyle='--')
    plt.text(start_time_inair + 1.0 , 0, f"Bắt đầu = {format_time(start_time_inair)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')
    # Vẽ groundspeed
    plt.plot(times, groundspeeds, label="Tốc độ bay", color="blue")

    # Tìm giá trị đỉnh của groundspeed
    max_groundspeed = max(groundspeeds)
    max_time = times[groundspeeds.index(max_groundspeed)]

    # Đặt tên cho đồ thị và trục
    plt.title("Tốc độ bay")
    plt.xlabel("Thời gian bay")
    plt.ylabel("km/h")

    # Hiển thị chú thích
    plt.legend()

    # Đánh dấu giá trị đỉnh
    plt.scatter(max_time, max_groundspeed, color="orange", marker="o")
    plt.text(max_time, max_groundspeed, f"{max_groundspeed:.2f} km/h", color="blue")

    # Đặt khoảng cách mốc trên trục x là 100 giây và xoay dọc
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    # Hiển thị đồ thị
    plt.grid()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "tocdo.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ
def plot_groundspeed_csv(file_path):
    # Đọc dữ liệu từ file CSV
    data = pd.read_csv(file_path)
    
    # Giả định rằng các cột 'flightTime', 'groundSpeed' tồn tại
    # Chuyển đổi định dạng thời gian từ 'HH:MM:SS' sang giây
    times = pd.to_timedelta(data['flightTime']).dt.total_seconds().values  # Chuyển đổi sang giây
    groundSpeed = data['groundSpeed'].astype(float).values  # Lấy giá trị khoảng cách đến nhà
    
    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = times - start_time

    plt.figure(figsize=(19.2, 10.8))
    plt.axvline(start_time, color='red', linestyle='--')
    plt.text(start_time + 1.0 , 0, f"Bắt đầu = {format_time(start_time)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')
    # Vẽ khoảng cách đến nhà
    plt.plot(times, groundSpeed, label="Tốc độ bay (km/h)", color="blue")

    # Tìm giá trị đỉnh của groundSpeed
    max_distance = max(groundSpeed)
    max_time = times[groundSpeed.argmax()]  # Tìm chỉ số giá trị lớn nhất

    # Đặt tên cho đồ thị và trục
    plt.title("Tốc độ bay")
    plt.xlabel("Thời gian bay")
    plt.ylabel("Tốc độ bay(km/h)")

    # Hiển thị chú thích
    plt.legend()

    # Đánh dấu giá trị đỉnh cho groundSpeed
    plt.scatter(max_time, max_distance, color="orange", marker="o")
    plt.text(max_time, max_distance, f"{max_distance:.2f} km/h", color="blue")

    # Đặt khoảng cách mốc trên trục x là 100 giây và xoay dọc
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    
    # Hiển thị đồ thị
    plt.grid()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "tocdo.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ

#Vẽ đồ thị điện áp
def plot_voltage_tlog(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    voltages = []
    start_time_inair = calculate_time_tlog(file_path)
    while True:
        msg = mavlog.recv_match(blocking=False)
        if msg is None:
            break

        # Kiểm tra nếu thông báo chứa thông tin điện áp pin
        if msg.get_type() == 'SYS_STATUS':  # Thay thế nếu điện áp pin nằm trong thông báo khác
            time = msg._timestamp  # Lấy timestamp
            times.append(time)
            voltages.append(msg.voltage_battery/1000);  # Lưu giá trị điện áp pin

    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = [t - start_time for t in times]
    plt.figure(figsize=(19.2, 10.8))
    plt.axvline(start_time_inair, color='red', linestyle='--')
    plt.text(start_time_inair + 1.0 , 0, f"Bắt đầu = {format_time(start_time_inair)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')
    # Vẽ điện áp pin
    plt.plot(times, voltages, label="Điện áp pin (V)", color="blue")

    # Tìm giá trị đỉnh của điện áp
    max_voltage = max(voltages)
    min_voltage = min(voltages)
    max_time = times[voltages.index(max_voltage)]
    min_time = times[voltages.index(min_voltage)]

    # Đặt tên cho đồ thị và trục
    plt.title("Điện áp pin")
    plt.xlabel("Thời gian bay")
    plt.ylabel("V")

    # Hiển thị chú thích
    plt.legend()

    # Đánh dấu giá trị đỉnh
    plt.scatter(max_time, max_voltage, color="blue", marker="o")
    plt.text(max_time, max_voltage, f"{max_voltage:.2f} V", color="blue")
    # Đánh dấu giá trị đỉnh
    plt.scatter(min_time, min_voltage, color="blue", marker="o")
    plt.text(min_time, min_voltage, f"{min_voltage:.2f} V", color="blue")
    # Đặt khoảng cách mốc trên trục x là 100 giây và xoay dọc
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    # Hiển thị đồ thị
    plt.grid()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "dienap.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ
def plot_voltage_csv(file_path):
    # Đọc dữ liệu từ file CSV
    data = pd.read_csv(file_path)
    
    # Giả định rằng các cột 'flightTime', 'voltage' tồn tại
    # Chuyển đổi định dạng thời gian từ 'HH:MM:SS' sang giây
    times = pd.to_timedelta(data['flightTime']).dt.total_seconds().values  # Chuyển đổi sang giây
    voltage = data['battery0.voltage'].astype(float).values
    
    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = times - start_time

    plt.figure(figsize=(19.2, 10.8))
    plt.axvline(start_time, color='red', linestyle='--')
    plt.text(start_time + 1.0 , 0, f"Bắt đầu = {format_time(start_time)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')
    # Vẽ khoảng cách đến nhà
    plt.plot(times, voltage, label="Điện áp pin (V)", color="blue")

    # Tìm giá trị đỉnh của voltage
    max_distance = max(voltage)
    max_time = times[voltage.argmax()]  # Tìm chỉ số giá trị lớn nhất

    # Đặt tên cho đồ thị và trục
    plt.title("Điện áp pin")
    plt.xlabel("Thời gian bay")
    plt.ylabel("Điện áp pin(V)")

    # Hiển thị chú thích
    plt.legend()

    # Đánh dấu giá trị đỉnh cho voltage
    plt.scatter(max_time, max_distance, color="orange", marker="o")
    plt.text(max_time, max_distance, f"{max_distance:.2f} V", color="blue")

    # Đặt khoảng cách mốc trên trục x là 100 giây và xoay dọc
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    # Hiển thị đồ thị
    plt.grid()
        # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "dienap.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ

# Vẽ đồ thị phần trăm ga
def plot_throttle_tlog(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    throttle = []
    start_time_inair = calculate_time_tlog(file_path)
    while True:
        msg = mavlog.recv_match(blocking=False)
        if msg is None:
            break

        # Kiểm tra nếu thông báo chứa thông tin điện áp pin
        if msg.get_type() == 'VFR_HUD':  # Thay thế nếu điện áp pin nằm trong thông báo khác
            time = msg._timestamp  # Lấy timestamp
            times.append(time)
            throttle.append(msg.throttle);  # Lưu giá trị điện áp pin

    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = [t - start_time for t in times]
    plt.figure(figsize=(19.2, 10.8))
    plt.axvline(start_time_inair, color='red', linestyle='--')
    plt.text(start_time_inair + 1.0 , 0, f"Bắt đầu = {format_time(start_time_inair)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')
    # Vẽ điện áp pin
    plt.plot(times, throttle, label="Phần trăm ga (%)", color="blue")

    # Đặt tên cho đồ thị và trục
    plt.title("Phần trăm ga")
    plt.xlabel("Thời gian bay")
    plt.ylabel("%")

    # Hiển thị chú thích
    plt.legend()

    # Đặt khoảng cách mốc trên trục x là 100 giây và xoay dọc
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    # Hiển thị đồ thị
    plt.grid()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "phantramGa.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ
def plot_throttle_csv(file_path):
    # Đọc dữ liệu từ file CSV
    data = pd.read_csv(file_path)
    
    # Giả định rằng các cột 'flightTime', 'throttlePct' tồn tại
    # Chuyển đổi định dạng thời gian từ 'HH:MM:SS' sang giây
    times = pd.to_timedelta(data['flightTime']).dt.total_seconds().values  # Chuyển đổi sang giây
    throttlePct = data['throttlePct'].astype(float).values  # Lấy giá trị khoảng cách đến nhà
    
    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = times - start_time

    plt.figure(figsize=(19.2, 10.8))
    plt.axvline(start_time, color='red', linestyle='--')
    plt.text(start_time + 1.0 , 0, f"Bắt đầu = {format_time(start_time)}", color='red', fontsize=10, fontweight='bold')

    plt.axvline(times[-1], color='red', linestyle='--')
    plt.text(times[-1] + 1.0 , 0, f"Kết thúc = {format_time(times[-1])}", color='red', fontsize=10, fontweight='bold')
    # Vẽ khoảng cách đến nhà
    plt.plot(times, throttlePct, label="Phần trăm ga (%)", color="blue")

    # Tìm giá trị đỉnh của throttlePct
    max_distance = max(throttlePct)
    max_time = times[throttlePct.argmax()]  # Tìm chỉ số giá trị lớn nhất

    # Đặt tên cho đồ thị và trục
    plt.title("Phần trăm ga")
    plt.xlabel("Thời gian bay")
    plt.ylabel("Phần trăm ga(%)")

    # Hiển thị chú thích
    plt.legend()

    # Đặt khoảng cách mốc trên trục x là 100 giây và xoay dọc
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    # Hiển thị đồ thị
    plt.grid()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "phantramGa.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ

# Vẽ đồ thị phần roll pitch heading
def plot_accel_tlog(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    roll = []
    pitch = []
    yaw = []
    while True:
        msg = mavlog.recv_match(blocking=False)
        if msg is None:
            break

        # Kiểm tra nếu thông báo chứa thông tin điện áp pin
        if msg.get_type() == 'ATTITUDE':  # Thay thế nếu điện áp pin nằm trong thông báo khác
            time = msg._timestamp  # Lấy timestamp
            times.append(time)
            roll.append(math.degrees(msg.roll))    # chuyển từ radian sang độ
            pitch.append(math.degrees(msg.pitch))
            yaw.append(math.degrees(msg.yaw))

    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = [t - start_time for t in times]
    plt.figure(figsize=(12,6))
    # Vẽ điện áp pin
    plt.plot(times, roll, label="Roll", color="blue")
    plt.plot(times, pitch, label="Pitch",color="green")
    plt.plot(times, yaw, label="Yaw",color="red")

    plt.figure(figsize=(12, 6))
    
    plt.subplot(2, 1, 1)
    plt.plot(times, roll, label="Roll", color="blue")
    plt.plot(times, pitch, label="Pitch", color="green")
    plt.legend()
    plt.grid()
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    plt.subplot(2, 1, 2)
    plt.plot(times, yaw, label="Heading", color="red")
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)
    plt.legend()
    plt.grid()

    # Đặt tên cho đồ thị và trục
    plt.title("Gia tốc")
    plt.xlabel("Thời gian bay")
    plt.ylabel("°")

    # Hiển thị chú thích

 
    plt.tight_layout()    
    file_name = "giatoc.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
def plot_accel_csv(file_path):
    # Đọc dữ liệu từ file CSV
    data = pd.read_csv(file_path)
    times = pd.to_timedelta(data['flightTime']).dt.total_seconds().values  # Chuyển đổi sang giây
    roll = data['roll'].astype(float).values
    pitch = data['pitch'].astype(float).values
    heading = data['heading'].astype(float).values
    
    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = times - start_time

    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(times, roll, label="Roll", color="blue")
    plt.plot(times, pitch, label="Pitch", color="green")
    plt.legend()
    plt.grid()
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    plt.subplot(2, 1, 2)
    plt.plot(times, heading, label="Heading", color="red")
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)
    plt.legend()
    plt.grid()

    # Đặt tên cho đồ thị và trục
    plt.title("Gia tốc")
    plt.xlabel("Thời gian bay")
    plt.ylabel("°")

    # Hiển thị chú thích

 
    plt.tight_layout()    
    file_name = "giatoc.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)

# Vẽ đồ thị kết hợp throttle speed altitude
def plot_throttle_speed_altitude_tlog(file_path):
    # Đọc dữ liệu từ file CSV
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    groundspeeds = []
    throttle = []
    altitude = []
    while True:
        msg = mavlog.recv_match(blocking=False)
        if msg is None:
            break

        # Kiểm tra nếu thông báo chứa thông tin groundspeed
        if msg.get_type() == 'VFR_HUD':  # `VFR_HUD` chứa thông tin `groundspeed`
            time = msg._timestamp  # Lấy timestamp
            times.append(time)
            groundspeeds.append(msg.groundspeed * 3.6)  # Tốc độ mặt đất trong m/s
            throttle.append(msg.throttle)
            altitude.append(msg.alt)

    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = [t - start_time for t in times]


    fig, ax1 = plt.subplots(figsize=(12, 8))
    ax1.plot(times, throttle, label="Phần trăm ga", color="blue")
    ax1.plot(times, groundspeeds, label="Tốc độ", color="green")
    ax1.set_ylabel("% - km/h")
    ax2 = ax1.twinx()
    ax2.plot(times, altitude, label="Độ cao so với mực nước biển", color="red")
    ax2.set_ylabel("m")

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.grid()
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    # Đặt tên cho đồ thị và trục
    plt.title("Tốc độ - Độ cao - Ga")
    ax1.set_xlabel("Thời gian bay")

    # Hiển thị chú thích

    plt.tight_layout()   
    file_name = "ga_tocdo_docao.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
def plot_throttle_speed_altitude_csv(file_path):
    # Đọc dữ liệu từ file CSV
    data = pd.read_csv(file_path)
    times = pd.to_timedelta(data['flightTime']).dt.total_seconds().values  # Chuyển đổi sang giây
    throttlePct = data['throttlePct'].astype(float).values
    groundSpeed = data['groundSpeed'].astype(float).values
    altitudeAMSL = data['altitudeAMSL'].astype(float).values
    
    # Chuẩn hóa thời gian bắt đầu từ 0
    start_time = times[0]
    times = times - start_time


    fig, ax1 = plt.subplots(figsize=(12, 8))

    ax1.plot(times, throttlePct, label="Phần trăm ga", color="blue")
    ax1.plot(times, groundSpeed, label="Tốc độ", color="green")
    ax1.set_ylabel("% - km/h")
    ax2 = ax1.twinx()
    ax2.plot(times, altitudeAMSL, label="Độ cao so với mực nước biển", color="red")
    ax2.set_ylabel("m")

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.grid()
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    plt.xticks(rotation=90)

    # Đặt tên cho đồ thị và trục
    plt.title("Tốc độ - Độ cao - Ga")
    ax1.set_xlabel("Thời gian bay")

    # Hiển thị chú thích

    plt.tight_layout()
    file_name = "ga_tocdo_docao.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)

def xulyFile_tlog():
    # Reset thanh tiến trình
    progress_bar['value'] = 0
    progress_bar['maximum'] = 7  # Tổng số hàm nhỏ

    # Chạy các hàm nhỏ và cập nhật thanh tiến trình
    for task in [plot_altitude_tlog, plot_distance_to_home_tlog, plot_groundspeed_tlog, plot_throttle_tlog, plot_voltage_tlog, plot_accel_tlog, plot_throttle_speed_altitude_tlog]:
        task(file_path)  # Gọi hàm nhỏ
        progress_bar['value'] += 1  # Cập nhật thanh tiến trình
        root.update_idletasks()  # Cập nhật giao diện
    label.config(text=f"Hoàn thành!")
def process_tlogfile():
    # Tạo một luồng mới để chạy các tác vụ
    thread = threading.Thread(target=xulyFile_tlog)
    thread.start()  # Bắt đầu luồng

def xulyFile_csv():
    # Reset thanh tiến trình
    progress_bar['value'] = 0
    progress_bar['maximum'] = 5  # Tổng số hàm nhỏ
    label.config(text=f"")

    # Chạy các hàm nhỏ và cập nhật thanh tiến trình
    for task in [plot_altitude_csv, plot_distance_to_home_csv, plot_groundspeed_csv, plot_throttle_csv, plot_voltage_csv, plot_accel_csv, plot_throttle_speed_altitude_csv]:
        task(file_path)  # Gọi hàm nhỏ
        progress_bar['value'] += 1  # Cập nhật thanh tiến trình
        root.update_idletasks()  # Cập nhật giao diện
    label.config(text=f"Hoàn thành!")
def process_csvfile():
    # Tạo một luồng mới để chạy các tác vụ
    thread = threading.Thread(target=xulyFile_csv)
    thread.start()  # Bắt đầu luồng

def process_file():
    if file_path.endswith(".tlog"):
        label.config(text=f"")
        process_tlogfile()
    elif file_path.endswith(".csv"):
        label.config(text=f"")
        process_csvfile()
    else:
        label.config(text=f"CHỌN FILE .CSV/.TLOG")
        
def close_window():
    # Đóng cửa sổ
    root.destroy()

# Tạo cửa sổ chính
root = tk.Tk()
root.title("Xử lý dữ liệu bay")
root.geometry("500x320")  # Đặt kích thước cửa sổ thành 300x300

# Frame chứa các nút và khung hiển thị đường dẫn
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(pady=20)

# Nút chọn file
button_open = tk.Button(frame, text="Chọn File .csv/.tlog", command=open_file, width= 20)
button_open.grid(row=0, column=0, padx=5, pady=5)

# Hộp nhập hiển thị đường dẫn file
entry_file_path = tk.Entry(frame, width=40)
entry_file_path.grid(row=0, column=1, padx=5, pady=5)

# Nút chọn thư mục lưu trữ
button_select_directory = tk.Button(frame, text="Chọn Thư mục Lưu", command=select_save_directory, width= 20)
button_select_directory.grid(row=1, column=0, padx=5, pady=5)

# Hộp nhập hiển thị đường dẫn thư mục lưu trữ
entry_save_path = tk.Entry(frame, width=40)
entry_save_path.grid(row=1, column=1, padx=5, pady=5)

# Nút xử lý và lưu đồ thị
button_process = tk.Button(root, text="Xử lý dữ liệu", command=process_file)
button_process.pack(pady=10)

# Thanh tiến trình
progress_bar = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate')
progress_bar.pack(pady=10)

# Tạo label để hiển thị đường dẫn file
label = tk.Label(root, text="")
label.pack(pady=10)

# Tạo nút để đóng cửa sổ
button_close = tk.Button(root, text="Đóng", command=close_window, width = 10)
button_close.pack(pady=10)

# Chạy vòng lặp chính
root.mainloop()

print("done")