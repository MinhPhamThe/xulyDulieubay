import matplotlib.pyplot as plt
from pymavlink import mavutil
from math import radians, sin, cos, sqrt, atan2
import matplotlib.ticker as ticker
import tkinter as tk
from tkinter import filedialog
import os

# Khai báo biến file_path
file_path = ""
save_directory = ""

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
        # Hiển thị đường dẫn file đã chọn
        label.config(text=f"Đường dẫn file: {file_path}")

def select_save_directory():
    global save_directory
    save_directory = filedialog.askdirectory()
    if save_directory:
        label_directory.config(text=f"Thư mục lưu: {save_directory}")
#Vẽ đồ thị độ cao
def plot_altitude(file_path):
    # Tạo đối tượng mavlink để đọc tệp
    mavlog = mavutil.mavlink_connection(file_path)

    # Danh sách lưu trữ dữ liệu
    times = []
    altitude_relative = []
    altitude_amsl = []

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

    plt.figure(figsize=(12,6))

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
    plt.show()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "docao.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"

#Vẽ đồ thị tầm xa bay
def plot_distance_to_home(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    distance_to_home = []
    home_position = None

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

    plt.figure(figsize=(12,6))

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
    plt.show()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "tamxa.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ

# Vẽ đồ thị tốc độ bay
def plot_groundspeed(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    groundspeeds = []

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
    plt.figure(figsize=(12,6))

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
    plt.show()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "tocdo.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ

#Vẽ đồ thị điện áp
def plot_voltage(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    voltages = []

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
    plt.figure(figsize=(12,6))

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
    plt.show()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "dienap.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ

# Vẽ đồ thị phần trăm ga
def plot_throttle(file_path):
    mavlog = mavutil.mavlink_connection(file_path)
    times = []
    throttle = []

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
    plt.figure(figsize=(12,6))

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
    plt.show()
    # Tạo tên file cho đồ thị, ví dụ: "do_thi.png"
    file_name = "phantramGa.png"
    full_path = os.path.join(save_directory, file_name)
    # Lưu đồ thị vào thư mục đã chọn
    plt.savefig(full_path)
    plt.close()  # Đóng đồ thị sau khi lưu để giải phóng bộ nhớ

def xulyFile():
    plot_altitude(file_path)
    plot_distance_to_home(file_path)
    plot_groundspeed(file_path)
    plot_throttle(file_path)
    plot_voltage(file_path)

def close_window():
    # Đóng cửa sổ
    root.destroy()

# Tạo cửa sổ chính
root = tk.Tk()
root.title("Chọn File")
root.geometry("300x300")  # Đặt kích thước cửa sổ thành 300x300

# Tạo nút để chọn file
button_open = tk.Button(root, text="Chọn File", command=open_file)
button_open.pack(pady=10)

# Tạo label để hiển thị đường dẫn file
label = tk.Label(root, text="Chưa chọn file")
label.pack(pady=10)
# Nút chọn thư mục lưu trữ
button_select_directory = tk.Button(root, text="Chọn Thư mục Lưu", command=select_save_directory)
button_select_directory.pack(pady=10)

# Hiển thị đường dẫn thư mục
label_directory = tk.Label(root, text="Chưa chọn thư mục lưu")
label_directory.pack(pady=10)

# Nút xử lý và lưu đồ thị
button_process = tk.Button(root, text="Lưu Đồ thị", command=xulyFile)
button_process.pack(pady=10)

# Tạo nút để đóng cửa sổ
button_close = tk.Button(root, text="Đóng", command=close_window)
button_close.pack(pady=10)

# Chạy vòng lặp chính
root.mainloop()

print("done")