import tkinter as tk
from PIL import Image, ImageTk
from components.InfoCard import InfoCard
import os

class ChatHome(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#F9F8F8")

        # ===== TIÊU ĐỀ =====
        tk.Label(self, text="Chào mừng bạn đến với", 
                 font=("Inter", 18), bg="#F9F8F8").pack(pady=(60,5))
        tk.Label(self, text="Ứng Dụng Mã Hóa Tin Nhắn", 
                 font=("Inter", 20), bg="#F9F8F8").pack(pady=(0,20))
        tk.Label(self, text="Chọn một cuộc trò chuyện từ danh sách bên trái để bắt đầu nhắn tin", 
                 font=("Inter", 14), bg="#F9F8F8", fg="#848484").pack(pady=(20,30))

        # ===== ẢNH ICON =====
        try:
            key_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "keyyellow.png")
            key_img = Image.open(key_path).resize((40, 40), Image.Resampling.LANCZOS)
            self.key_icon = ImageTk.PhotoImage(key_img)
        except Exception as e:
            print("Không tìm thấy ảnh keyyellow.png:", e)
            self.key_icon = None
        try:
            lock_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "lockyellow.png")
            lock_img = Image.open(lock_path).resize((45, 45), Image.Resampling.LANCZOS)
            self.lock_icon = ImageTk.PhotoImage(lock_img)
        except Exception as e:
            print("Không tìm thấy ảnh lockyellow.png:", e)
            self.lock_icon = None

        try:
            security_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "securityyellow.png")
            security_img = Image.open(security_path).resize((45, 45), Image.Resampling.LANCZOS)
            self.security_icon = ImageTk.PhotoImage(security_img)
        except Exception as e:
            print("Không tìm thấy ảnh securityyellow.png:", e)
            self.security_icon = None

        # ===== CÁC THẺ MÔ TẢ =====
        InfoCard(self, self.key_icon, "Bảo mật tuyệt đối", 
                 "Chỉ bạn và người nhận có thể đọc tin nhắn").pack(fill="x", padx=100, pady=10)
        InfoCard(self, self.lock_icon, "Mã hóa đầu cuối", 
                 "Tất cả tin nhắn được mã hóa bằng thuật toán").pack(fill="x", padx=100, pady=10)
        InfoCard(self, self.security_icon, "Riêng tư", 
                 "Không ai khác có thể xem lịch sử chat của bạn").pack(fill="x", padx=100, pady=10)
