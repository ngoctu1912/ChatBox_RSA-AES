# frontend/main.py

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tkinter as tk
import threading
import socketio
from screens.Home import HomePage
from screens.Login import LoginPage
from screens.Register import RegisterPage
from frontend.components.Chat import Chat

# Cấu hình URL WebSocket Server
WEBSOCKET_URL = 'http://localhost:5000'

class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title("Ứng Dụng Chat Mã Hóa RSA-AES")
        
        # Tự động điều chỉnh kích thước theo màn hình
        self.setup_responsive_window()
        
        # Lưu thông tin người dùng hiện tại
        self.current_user = {}
        
        # Lưu pending notifications
        self.pending_notifications = []

        # ===== SOCKET.IO CLIENT SETUP =====
        self.sio_client = socketio.Client()
        self.connect_socketio()
        self.register_socketio_events()

        # ===== KHUNG CHỨA GIAO DIỆN =====
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # ===== LƯU CÁC TRANG TRONG DICTIONARY =====
        self.frames = {}
        
        # Chỉ khởi tạo các trang cơ bản (không cần user_data)
        for F in (HomePage, LoginPage, RegisterPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self) 
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew") 

        # Hiển thị trang Home đầu tiên
        self.show_frame("HomePage")
        
        # Thiết lập ngắt kết nối an toàn khi đóng cửa sổ
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_responsive_window(self):
        """Tự động điều chỉnh kích thước cửa sổ theo màn hình"""
        # Lấy kích thước màn hình
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Tính toán kích thước cửa sổ (80% màn hình)
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # Giới hạn kích thước
        # Min: 1000x600 (cho laptop 14")
        # Max: 1600x900 (cho màn hình lớn)
        window_width = max(1000, min(window_width, 1600))
        window_height = max(600, min(window_height, 900))
        
        # Tính vị trí để căn giữa màn hình
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set geometry và giới hạn
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(1000, 600)
        self.maxsize(1600, 900)
        self.resizable(True, True)
        
        # Phím tắt fullscreen
        self.is_fullscreen = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

    def connect_socketio(self):
        """Khởi tạo kết nối SocketIO trong luồng riêng"""
        try:
            self.sio_client.connect(WEBSOCKET_URL)
            print(f" SocketIO Client connected to {WEBSOCKET_URL}")

            # Chạy luồng lắng nghe trong nền
            threading.Thread(target=self.sio_client.wait, daemon=True).start()
            
        except Exception as e:
            print(f" SocketIO connection failed: {e}")

    def register_socketio_events(self):
        """Đăng ký các event listeners cho SocketIO"""
        
        @self.sio_client.on('pending_messages_notification')
        def on_pending_notification(data):
            """Nhận thông báo về pending messages khi đăng nhập"""
            count = data.get('count', 0)
            message = data.get('message', '')
            print(f"📬 {message}")
            
            # Lưu notification để hiển thị trong UI
            self.pending_notifications.append({
                'count': count,
                'message': message
            })
            
            # TODO: Hiển thị popup hoặc badge trong UI
        
        @self.sio_client.on('message_queued')
        def on_message_queued(data):
            """Nhận thông báo khi tin nhắn được queue (người nhận chưa online)"""
            print(f" Message queued: {data.get('message')}")
            
            # TODO: Hiển thị icon "pending" trong chat UI
            # Có thể cập nhật ChatScreen để hiển thị tin nhắn với trạng thái pending
        
        @self.sio_client.on('message_delivered')
        def on_message_delivered(data):
            """Nhận thông báo khi pending message được deliver"""
            message_id = data.get('message_id')
            print(f" Pending message {message_id} has been delivered")
            
            # TODO: Cập nhật icon từ "pending" → "delivered" trong UI

    def show_frame(self, page_name):
        """Hiển thị trang được chỉ định, tạo ChatPage nếu cần"""
        
        if page_name == "ChatPage":
            if not self.current_user:
                print("  Lỗi: Không thể mở ChatPage vì người dùng chưa đăng nhập.")
                return
            
            # Xóa frame ChatPage cũ nếu có
            if "ChatPage" in self.frames:
                self.frames["ChatPage"].destroy()
                del self.frames["ChatPage"]
            
            # Lấy container frame
            container = self.frames[list(self.frames.keys())[0]].master
            
            # TẠO MỚI CHATPAGE với user_data và sio_client
            chat_frame = Chat(
                parent=container, 
                controller=self, 
                user_data=self.current_user,
                sio_client=self.sio_client
            )
            self.frames["ChatPage"] = chat_frame
            chat_frame.grid(row=0, column=0, sticky="nsew")
            
            # Hiển thị pending notifications nếu có
            if self.pending_notifications:
                for notif in self.pending_notifications:
                    # TODO: Hiển thị trong ChatScreen
                    print(f" UI Notification: {notif['message']}")
                self.pending_notifications.clear()
        
        # Hiển thị frame
        frame = self.frames.get(page_name)
        if frame:
            frame.tkraise()

    def on_closing(self):
        """Ngắt kết nối SocketIO an toàn trước khi đóng ứng dụng"""
        if self.sio_client.connected:
            self.sio_client.disconnect()
            print(" SocketIO Client disconnected")
        self.destroy()
    
    def toggle_fullscreen(self, event=None):
        """Chuyển đổi chế độ toàn màn hình (F11)"""
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        return "break"
    
    def exit_fullscreen(self, event=None):
        """Thoát chế độ toàn màn hình (ESC)"""
        self.is_fullscreen = False
        self.attributes("-fullscreen", False)
        return "break"


if __name__ == '__main__':
    app = App()
    app.mainloop()