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
def plot_4thongso(file_path):
    # Đọc dữ liệu từ file CSV
    data = pd.read_csv(file_path)
    times = pd.to_timedelta(data['flightTime']).dt.total_seconds().values  # Chuyển đổi sang giây
    throttlePct = data['throttlePct'].astype(float).values
    distance_to_home = data['distanceToHome'].astype(float).values
    altitudeAMSL = data['altitudeAMSL'].astype(float).values
    groundSpeed = data['groundSpeed'].astype(float).values
    missionItemIndex = data['missionItemIndex'].astype(float).values
    itemMission = [0]
    for i in range(len(missionItemIndex)):
        if missionItemIndex[i]>missionItemIndex[i-1]:
            itemMission.append(i)
    print(itemMission)

    fig, ax1 = plt.subplots(figsize=(12, 8))
    line1, = ax1.plot(times, throttlePct, label="Phần trăm ga", color="blue", linewidth=0.5)
    line2, = ax1.plot(times, altitudeAMSL, label="Độ cao so với mực nước biển", color="red", linewidth=2)
    line3, = ax1.plot(times, groundSpeed, label="Tốc độ bay", color="purple", linewidth=2)
    ax1.set_ylabel("Phần trăm ga - Độ cao - Tốc độ bay \n (% - m - km/h)")
    ax2 = ax1.twinx()   
    line4, = ax2.plot(times, distance_to_home, label="Tầm xa", color="green", linewidth=2)
    ax2.set_ylabel("Tầm bay xa\n(m)", rotation = -90, labelpad=20)
    plt.axvline(times[0], label="Bắt đầu", color='black', linestyle='--', linewidth=1)
    plt.text(times[0],-60, "Bắt đầu", fontsize=5,rotation = 90, color="black", ha='right')
    plt.axvline(times[len(missionItemIndex)-1], label="Kết thúc", color='black', linestyle='--', linewidth=1)
    plt.text(times[len(missionItemIndex)-1],-60, "Kết thúc", fontsize=5,rotation = 90, color="black", ha='right')
    for i in range(1, len(itemMission), 1):
        plt.axvline(times[itemMission[i]], label=f"Điểm {i}", color='black', linestyle='--', linewidth=0.5)
        plt.text(times[itemMission[i]], -60 , f"Điểm {i}", fontsize=5, rotation=90, color="black", ha='right')

    plt.grid()
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(50))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_time(x)))
    lines = [line1, line2, line3, line4] 
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc="lower left", bbox_to_anchor=(1, 1))

    # Đặt tên cho đồ thị và trục
    plt.title("Tầm xa - Độ cao - Phần trăm Ga - Tốc độ\nX4 bay lần 2 (không có camera)", fontsize=12)
    ax1.set_xlabel("Thời gian bay\n(phút giây)")

    plt.tight_layout()
    plt.grid()
    file_name = "tonghop.png"
    full_path = os.path.join(save_directory, file_name)
    plt.savefig(full_path)
    plt.close()

def xulyFile_csv():
    # Reset thanh tiến trình
    progress_bar['value'] = 0
    progress_bar['maximum'] = 5  # Tổng số hàm nhỏ
    label.config(text=f"")

    # Chạy các hàm nhỏ và cập nhật thanh tiến trình
    for task in [plot_altitude_csv, plot_distance_to_home_csv, plot_groundspeed_csv, plot_throttle_csv, plot_voltage_csv, plot_accel_csv, plot_4thongso]:
        task(file_path)  # Gọi hàm nhỏ
        progress_bar['value'] += 1  # Cập nhật thanh tiến trình
        root.update_idletasks()  # Cập nhật giao diện
    label.config(text=f"Hoàn thành!")
def process_csvfile():
    # Tạo một luồng mới để chạy các tác vụ
    thread = threading.Thread(target=xulyFile_csv)
    thread.start()  # Bắt đầu luồng
def process_file():
    if file_path.endswith(".csv"):
        label.config(text=f"")
        process_csvfile()
    else:
        label.config(text=f"CHỌN FILE .CSV")       
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
button_open = tk.Button(frame, text="Chọn File .csv", command=open_file, width= 20)
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