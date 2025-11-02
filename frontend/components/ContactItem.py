import tkinter as tk

class ContactItem(tk.Frame):
    def __init__(self, parent, avatar_icon, name, message, has_unread_messages=False, on_select=None):
        super().__init__(parent, bg="#FFFFFF", height=60)
        self.pack_propagate(False)
        self.avatar_icon = avatar_icon
        self.name = name
        self.message = message
        self.on_select = on_select
        self.is_selected = False
        self.has_unread_messages = has_unread_messages 

        # --- Định nghĩa Font và Màu ---
        self.normal_font = ("Inter", 10)
        self.bold_font = ("Inter", 10, "bold")
        self.normal_fg = "#676767"
        self.unread_fg = "#333333" # Màu đậm hơn cho tin nhắn chưa đọc

        # --- Thiết lập font và màu ban đầu ---
        msg_font = self.bold_font if self.has_unread_messages else self.normal_font
        msg_fg = self.unread_fg if self.has_unread_messages else self.normal_fg

        # --- Bố cục avatar + nội dung ---
        tk.Label(self, image=self.avatar_icon, bg="#FFFFFF").pack(side="left", padx=8)
        
        text_frame = tk.Frame(self, bg="#FFFFFF")
        text_frame.pack(side="left", fill="both", expand=True)
        
        # Nhãn Tên
        tk.Label(text_frame, text=self.name, font=("Inter", 12), bg="#FFFFFF").pack(anchor="w", pady=(5,0))
        
        # Nhãn Tin nhắn (Áp dụng font in đậm)
        self.message_label = tk.Label(
            text_frame, 
            text=self.message, 
            font=msg_font, 
            fg=msg_fg, 
            bg="#FFFFFF"
        )
        self.message_label.pack(anchor="w", pady=(5,0))

        # --- Gán sự kiện click ---
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
        
        # Cấu hình màu nền cho Frame chính và các Frame con
        self.config(bg=new_bg)
        for child in self.winfo_children():
            child.config(bg=new_bg)
            for sub in child.winfo_children():
                sub.config(bg=new_bg)