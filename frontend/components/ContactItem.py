import tkinter as tk
from datetime import datetime


class ContactItem(tk.Frame):
    def __init__(self, parent, avatar_icon, name, message, latest_time="", unread_count=0, on_select=None, is_online=False):
        super().__init__(parent, bg="#FFFFFF", height=60)
        self.pack_propagate(False)
        self.avatar_icon = avatar_icon
        self.name = name
        self.message = message
        self.latest_time = latest_time
        self.on_select = on_select
        self.is_selected = False
        self.unread_count = unread_count 
        self.is_online = is_online

        # Font và màu
        self.normal_font = ("Inter", 10)
        self.bold_font = ("Inter", 10, "bold")

        self._create_widgets()
        self.set_selected(False)

    def _create_widgets(self):
        # Khung chứa avatar + nội dung
        self.avatar_label = tk.Label(self, image=self.avatar_icon, bg=self["bg"])
        self.avatar_label.pack(side="left", padx=8)
        
        self.text_frame = tk.Frame(self, bg=self["bg"])
        self.text_frame.pack(side="left", fill="both", expand=True)
        
        # --- HÀNG 1: TÊN + TRẠNG THÁI ONLINE ---
        self.header_frame = tk.Frame(self.text_frame, bg=self["bg"])
        self.header_frame.pack(fill="x", anchor="w", pady=(5, 0))
        
        # Tên
        self.name_label = tk.Label(self.header_frame, text=self.name, font=("Inter", 12), bg=self["bg"])
        self.name_label.pack(side="left", anchor="w", padx=(0, 5)) 

        # Trạng thái online/offline
        if self.is_online:
            status_text = "Đang hoạt động"
            status_color = "green"
        else:
            status_text = "Offline"
            status_color = "#999999"

        # Icon Trạng thái (chấm tròn)
        self.status_icon_label = tk.Label(self.header_frame, text="•", font=("Inter", 12, "bold"), fg=status_color, bg=self["bg"])
        self.status_icon_label.pack(side="left", anchor="w")
        
        # Text Trạng thái
        self.status_text_label = tk.Label(self.header_frame, text=status_text, font=("Inter", 9), fg=status_color, bg=self["bg"])
        self.status_text_label.pack(side="left", anchor="w")
        
        # Thời gian
        self.time_label = tk.Label(self.header_frame, text=self.latest_time, font=("Inter", 8), fg="#999999", bg=self["bg"])
        self.time_label.pack(side="right", padx=(5, 0))
        
        # --- HÀNG 2: TIN NHẮN + SỐ ĐẾM CHƯA ĐỌC ---
        self.footer_frame = tk.Frame(self.text_frame, bg=self["bg"])
        self.footer_frame.pack(fill="x", anchor="w", pady=(0, 5))
        
        #  Giới hạn chiều rộng message_label để không che unread badge
        self.message_label = tk.Label(
            self.footer_frame, 
            text=self.message, 
            font=self.bold_font if self.unread_count > 0 else self.normal_font, 
            fg="#333333" if self.unread_count > 0 else "#676767", 
            bg=self["bg"],
            anchor="w",
            width=20  #  Giới hạn 20 ký tự để không đè lên unread badge
        )
        self.message_label.pack(side="left", anchor="w", fill="x", expand=True)
        
        self.unread_count_label = tk.Label(
            self.footer_frame,
            text=str(self.unread_count) if self.unread_count > 0 else "",
            font=("Inter", 8, "bold"),
            bg="#FF6B6B" if self.unread_count > 0 else self["bg"],
            fg="white" if self.unread_count > 0 else self["bg"],
            width=3 if self.unread_count > 0 else 0,  #  Tăng width lên 3 cho số > 9
            relief='flat',
            borderwidth=0,
            padx=4,  #  Thêm padding ngang
            pady=2   #  Thêm padding dọc
        )
        self.unread_count_label.pack(side="right", padx=(5, 0), pady=(0, 0))

        # Gán sự kiện click
        self.bind_all_widgets(self, "<Button-1>", self.select)
              
    def bind_all_widgets(self, widget, event, callback):
        widget.bind(event, callback)
        for child in widget.winfo_children():
            self.bind_all_widgets(child, event, callback)

    def select(self, event=None):
        if self.on_select:
            self.on_select(self)  

    def set_selected(self, selected: bool):
        """Cập nhật màu khi được chọn hoặc bỏ chọn"""
        self.is_selected = selected
        new_bg = "#D6F0FA" if selected else "#FFFFFF"
        
        # Cập nhật màu nền cho tất cả widgets
        self.config(bg=new_bg)
        self.avatar_label.config(bg=new_bg)
        self.text_frame.config(bg=new_bg)
        self.header_frame.config(bg=new_bg)
        self.footer_frame.config(bg=new_bg)
        self.name_label.config(bg=new_bg)
        self.status_icon_label.config(bg=new_bg)
        self.status_text_label.config(bg=new_bg)
        self.time_label.config(bg=new_bg)
        self.message_label.config(bg=new_bg)
        
        # Chỉ cập nhật unread_count_label nếu không có unread
        if self.unread_count == 0:
            self.unread_count_label.config(bg=new_bg, fg=new_bg)
    
    def update_online_status(self, is_online: bool):
        """Cập nhật trạng thái online/offline real-time"""
        print(f" [ContactItem] {self.name}: Updating status to {'online' if is_online else 'offline'}")
        
        self.is_online = is_online
        
        # Cập nhật màu sắc và text
        if is_online:
            status_text = "Đang hoạt động"
            status_color = "green"
        else:
            status_text = "Offline"
            status_color = "#999999"
        
        # Cập nhật UI
        try:
            self.status_icon_label.config(fg=status_color)
            self.status_text_label.config(text=status_text, fg=status_color)
            print(f" [ContactItem] {self.name}: UI updated successfully")
        except Exception as e:
            print(f" [ContactItem] {self.name}: Error updating UI - {e}")
                
    def update_unread_count(self, count):
        """Cập nhật số lượng tin chưa đọc và màu sắc"""
        self.unread_count = count
        
        if count > 0:
            new_font = self.bold_font
            new_fg = "#333333"
            
            # Cập nhật số đếm
            self.unread_count_label.config(
                text=str(count),
                bg="#FF6B6B",
                fg="white",
                width=2
            )
        else:
            new_font = self.normal_font
            new_fg = "#676767"
            
            # Ẩn số đếm
            self.unread_count_label.config(
                text="",
                bg="#FFFFFF",
                fg="#FFFFFF",
                width=0
            )

        # Cập nhật font và màu cho tin nhắn
        self.message_label.config(font=new_font, fg=new_fg)
    
    def update_message(self, message_text, latest_time=""):
        """Cập nhật preview tin nhắn và thời gian"""
        self.message = message_text
        if latest_time:
            self.latest_time = latest_time
        
        # Cập nhật UI
        self.message_label.config(text=self.message)
        if latest_time:
            self.time_label.config(text=self.latest_time)

    # ==================  THÊM MỚI: CẬP NHẬT TRẠNG THÁI ONLINE/OFFLINE ==================
    def update_online_status(self, is_online):
        """
        Cập nhật hiển thị trạng thái online/offline
        
        Args:
            is_online (bool): True nếu online, False nếu offline
        """
        self.is_online = is_online
        
        # Cập nhật text và màu sắc
        if is_online:
            status_text = "Đang hoạt động"
            status_color = "green"
        else:
            status_text = "Offline"
            status_color = "#999999"
        
        # Cập nhật icon trạng thái (chấm tròn)
        if hasattr(self, 'status_icon_label'):
            self.status_icon_label.config(fg=status_color)
        
        # Cập nhật text trạng thái
        if hasattr(self, 'status_text_label'):
            self.status_text_label.config(text=status_text, fg=status_color)
        
        print(f"  Updated online status for {self.name}: {'Online' if is_online else 'Offline'}")