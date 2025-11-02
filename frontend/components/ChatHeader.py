import tkinter as tk
from tkinter import ttk 
from PIL import Image, ImageTk
import os

class ChatHeader(tk.Frame):
    """Component Header chung cho ChatScreen và EmptyChatScreen"""
    
    def __init__(self, parent, contact_name, avatar_icon, current_user_id=None, partner_id=None, rsa_keys=None):
        super().__init__(parent, bg="#FFFFFF")
        self.parent_screen = parent
        self.contact_name = contact_name
        self.avatar_icon = avatar_icon
        self.current_user_id = current_user_id
        self.partner_id = partner_id
        self.rsa_keys = rsa_keys or {}  
        
        # Thêm setup style ngay từ đầu
        self._setup_custom_scrollbar_style()
        
        self._create_header()
        self._create_rsa_panel()
    
    # === HÀM THIẾT LẬP STYLE MỚI CHO SCROLLBAR ===
    def _setup_custom_scrollbar_style(self):
        """Tạo style custom cho scrollbar ngang (dựa trên Sidebar)"""
        style = ttk.Style()
        style.theme_use('default')
        
        # Style cho thanh cuộn ngang
        style.configure(
            "Custom.Horizontal.TScrollbar",
            background="#E0E0E0",      # Màu nền thanh cuộn
            troughcolor="#ffffff",      # Màu nền rãnh
            borderwidth=0,              # Bỏ viền
            arrowsize=0,                # Ẩn mũi tên
            height=8                    # Độ cao thanh cuộn (thon gọn)
        )
        
        # Màu khi hover
        style.map(
            "Custom.Horizontal.TScrollbar",
            background=[("active", "#B0B0B0"), ("!active", "#E0E0E0")]
        )
    
    def _create_header(self):
        """Tạo phần header chính"""
        header_frame = tk.Frame(self, bg="#FFFFFF", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Avatar
        tk.Label(header_frame, image=self.avatar_icon, bg="#FFFFFF").pack(side="left", padx=15)
        
        # Thông tin người nhận
        info_frame = tk.Frame(header_frame, bg="#FFFFFF")
        info_frame.pack(side="left", fill="y")
        
        tk.Label(
            info_frame,
            text=self.contact_name,
            font=("Inter", 13),
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(12, 0))
        
        # Trạng thái online
        status_frame = tk.Frame(info_frame, bg="#FFFFFF")
        status_frame.pack(anchor="w", pady=(2, 0))
        
        try:
            status_path = os.path.join(
                os.path.dirname(__file__), "..", "assets", "icons", "button.png"
            )
            status_img = Image.open(status_path).resize((10, 10), Image.Resampling.LANCZOS)
            self.status_icon = ImageTk.PhotoImage(status_img)
            tk.Label(status_frame, image=self.status_icon, bg="#FFFFFF").pack(side="left", padx=(0, 5))
        except:
            pass
        
        tk.Label(
            status_frame,
            text="Đang hoạt động",
            font=("Inter", 9),
            fg="green",
            bg="#FFFFFF"
        ).pack(side="left")
        
        # Icon Key (RSA)
        try:
            key_path = os.path.join(
                os.path.dirname(__file__), "..", "assets", "icons", "key.png"
            )
            key_img = Image.open(key_path).resize((20, 20), Image.Resampling.LANCZOS)
            self.key_icon = ImageTk.PhotoImage(key_img)
            key_label = tk.Label(header_frame, image=self.key_icon, bg="#FFFFFF", cursor="hand2")
        except:
            key_label = tk.Label(header_frame, text="🔑", bg="#FFFFFF", font=("Inter", 14), cursor="hand2")
        
        key_label.pack(side="right", padx=15)
        key_label.bind("<Button-1>", self.toggle_rsa_panel)
    
    def _create_rsa_panel(self):
        """Tạo panel hiển thị khóa RSA"""
        self.rsa_panel = tk.Frame(self, bg="#F5F5F5") 
        self.rsa_panel.pack(fill="x", padx=20, pady=(10, 0))
        self.rsa_panel.pack_forget()  # Ẩn ban đầu
        
        # Nút đóng
        close_btn = tk.Label(
            self.rsa_panel, text="✕", font=("Arial", 16, "bold"),
            bg="#F5F5F5", fg="#888", cursor="hand2"
        )
        close_btn.place(relx=1.0, rely=0, anchor="ne", x=-10, y=8)
        close_btn.bind("<Button-1>", lambda e: self.rsa_panel.pack_forget())
        
        self._show_rsa_keys()

    def _clean_key(self, key_data):
        """Loại bỏ các dòng BEGIN/END PUBLIC KEY và khoảng trắng thừa."""
        if not key_data:
            return key_data
        
        lines = [line.strip() for line in key_data.split('\n')]
        
        # Lọc bỏ các dòng chứa BEGIN/END PUBLIC KEY
        cleaned_lines = [
            line for line in lines 
            if not line.startswith('-----BEGIN PUBLIC KEY-----') and 
               not line.startswith('-----END PUBLIC KEY-----') and
               line
        ]
        
        # Ghép các phần còn lại thành một chuỗi duy nhất
        return "".join(cleaned_lines)

    def _on_horizontal_scroll(self, event, key_text):
        """Xử lý cuộn chuột mượt cho thanh cuộn ngang"""
        # Nếu cuộn lên (delta > 0 hoặc num == 4), cuộn sang trái (giảm x)
        if event.num == 4 or event.delta > 0:
            key_text.xview_scroll(-1, "units")
        # Nếu cuộn xuống (delta < 0 hoặc num == 5), cuộn sang phải (tăng x)
        elif event.num == 5 or event.delta < 0:
            key_text.xview_scroll(1, "units")
        return "break" # Ngăn sự kiện lan truyền lên parent

    def _bind_mousewheel(self, widget, key_text):
        """Bind mousewheel cho Text widget để cuộn ngang."""
        widget.bind("<MouseWheel>", lambda e: self._on_horizontal_scroll(e, key_text))
        widget.bind("<Button-4>", lambda e: self._on_horizontal_scroll(e, key_text))
        widget.bind("<Button-5>", lambda e: self._on_horizontal_scroll(e, key_text))

    def _create_key_display(self, parent_frame, key_data):
        """Tạo khung hiển thị khóa với thanh cuộn ngang chỉ hiện khi cần thiết."""
        
        # Khung chứa Text và Scrollbar
        container = tk.Frame(parent_frame, bg=parent_frame['bg'])
        container.pack(fill="x", pady=(2, 0))

        # Thanh cuộn ngang (ban đầu không đóng gói)
        h_scrollbar = ttk.Scrollbar(
            container,
            orient="horizontal",
            style="Custom.Horizontal.TScrollbar" # <-- ÁP DỤNG STYLE MỚI
        )
        
        # Text Widget
        key_text = tk.Text(
            container, 
            font=("Consolas", 8), 
            bg=parent_frame['bg'], 
            height=2, 
            wrap="none", 
            borderwidth=0, 
            highlightthickness=0,
            xscrollcommand=h_scrollbar.set 
        )
        key_text.insert("1.0", key_data)
        key_text.config(state="disabled") 
        key_text.pack(side="top", fill="x", expand=True)
        
        # Cấu hình thanh cuộn
        h_scrollbar.config(command=key_text.xview)
        
        # Áp dụng cuộn chuột mượt
        self._bind_mousewheel(key_text, key_text) 
        self._bind_mousewheel(container, key_text)

        def check_scrollbar_visibility(event=None):
            """Kiểm tra và hiển thị/ẩn thanh cuộn ngang"""
            # Cần force update geometry để đo lường chính xác
            container.update_idletasks()
            
            # Lấy thông tin cuộn ngang (tỷ lệ của vùng hiển thị so với tổng nội dung)
            x_view = key_text.xview()
            
            # Nếu chuỗi khóa quá dài (tức là tổng nội dung lớn hơn vùng hiển thị, xview[1] < 1.0)
            if x_view[1] < 1.0:
                h_scrollbar.pack(side="bottom", fill="x")
            else:
                h_scrollbar.pack_forget()

        # Bind sự kiện thay đổi kích thước container để kiểm tra lại
        container.bind("<Configure>", check_scrollbar_visibility)
        
        # Chạy kiểm tra ban đầu
        self.after(50, check_scrollbar_visibility)


        return key_text

    def _show_rsa_keys(self):
        """Hiển thị khóa RSA - tự động lấy từ backend nếu chưa có"""
        # Xóa nội dung cũ (trừ nút đóng)
        for widget in self.rsa_panel.winfo_children():
            if widget.winfo_class() != 'Label' or widget['text'] != '✕': 
                widget.destroy()
        
        # Tiêu đề
        title_frame = tk.Frame(self.rsa_panel, bg="#F5F5F5")
        title_frame.pack(fill="x", pady=(8, 10), padx=10)
        
        try:
            key_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "key.png")
            key_img = Image.open(key_path).resize((18, 18), Image.Resampling.LANCZOS)
            icon = ImageTk.PhotoImage(key_img)
            icon_label = tk.Label(title_frame, image=icon, bg="#F5F5F5")
            icon_label.pack(side="left", padx=(0, 6))
            icon_label.image = icon
        except:
            tk.Label(title_frame, text="Key", bg="#F5F5F5", font=("Arial", 12)).pack(side="left", padx=(0, 6))
        
        tk.Label(title_frame, text="Trao đổi khóa RSA", font=("Inter", 11, "bold"), bg="#F5F5F5").pack(side="left")
        
        # === TỰ ĐỘNG LẤY KHÓA TỪ BACKEND ===
        if self.current_user_id is not None and self.partner_id is not None:
            try:
                from backend.Services.RSAService import RSAService  
                
                keys = RSAService.get_user_keys(self.current_user_id, self.partner_id)
                
                my_key = self._clean_key(keys.get("my_public_key")) or "Chưa tạo khóa"
                partner_key = self._clean_key(keys.get("partner_public_key")) or "Đối phương chưa có khóa"
                
            except Exception as e:
                my_key = "Lỗi tải khóa: Dịch vụ RSA chưa sẵn sàng"
                partner_key = "Lỗi tải khóa: Dịch vụ RSA chưa sẵn sàng"
                print(f"Error loading RSA keys in ChatHeader: {e}")
        else:
            my_key = "Thiếu user_id"
            partner_key = "Thiếu partner_id"
        
        # === HIỂN THỊ KHÓA VỚI SCROLL BAR NGANG ===
        
        # Khóa của người dùng
        frame1 = tk.Frame(self.rsa_panel, bg="#E8E8E8", padx=10, pady=8) 
        frame1.pack(fill="x", padx=10, pady=(0, 10)) 
        
        tk.Label(frame1, text="Khóa công khai của bạn:", font=("Inter", 9, "bold"),
                bg="#E8E8E8", anchor="w").pack(fill="x")
        
        self._create_key_display(frame1, my_key)
        
        # Khóa của đối phương
        frame2 = tk.Frame(self.rsa_panel, bg="#E8E8E8", padx=10, pady=8) 
        frame2.pack(fill="x", padx=10, pady=(0, 10)) 

        tk.Label(frame2, text=f"Khóa công khai của {self.contact_name}:",
                font=("Inter", 9, "bold"), bg="#E8E8E8", anchor="w").pack(fill="x")
        
        self._create_key_display(frame2, partner_key)

    
    def toggle_rsa_panel(self, event=None):
        """Toggle hiển thị/ẩn RSA panel"""
        if self.rsa_panel.winfo_ismapped():
            self.rsa_panel.pack_forget()
        else:
            # GỌI LẠI _show_rsa_keys TRƯỚC KHI HIỂN THỊ để cập nhật nội dung
            self._show_rsa_keys() 
            self.rsa_panel.pack(fill="x", padx=20, pady=(10, 0), after=self.winfo_children()[0])
