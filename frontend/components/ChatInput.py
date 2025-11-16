import tkinter as tk
from PIL import Image, ImageTk
import os

class ChatInput(tk.Frame):
    """Component Input chung cho ChatScreen và EmptyChatScreen"""
    
    def __init__(self, parent, on_send=None):
        super().__init__(parent, bg="#FFFFFF", height=70)
        self.on_send = on_send
        
        self.pack_propagate(False)
        self._create_widgets()
    
    def _create_widgets(self):
        # Dùng grid để căn đều
        self.columnconfigure(0, weight=1)  # Entry
        self.columnconfigure(1, weight=0)  # Send button
        self.rowconfigure(0, weight=1)
        
        # Container để căn giữa text entry
        entry_container = tk.Frame(self, bg="#F5F5F5")
        entry_container.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=15)
        
        # Ô nhập tin nhắn
        self.message_entry = tk.Entry(
            entry_container,
            font=("Inter", 12),
            relief="flat",
            bg="#F5F5F5",
            fg="#888888",
            borderwidth=0,
            highlightthickness=0
        )
        self.message_entry.pack(fill="both", expand=True, padx=8)
        self.message_entry.insert(0, "Nhập tin nhắn ....")
        
        # Placeholder
        self.message_entry.bind("<FocusIn>", self._clear_placeholder)
        self.message_entry.bind("<FocusOut>", self._restore_placeholder)
        self.message_entry.bind("<Return>", lambda e: self._handle_send())
        
        # Icon gửi
        try:
            send_path = os.path.join(
                os.path.dirname(__file__), "..", "assets", "icons", "send.png"
            )
            send_img = Image.open(send_path).resize((20, 20), Image.Resampling.LANCZOS)
            self.send_icon = ImageTk.PhotoImage(send_img)
        except Exception as e:
            print("Không tìm thấy ảnh send.png:", e)
            self.send_icon = None
        
        # Nút gửi
        send_btn = tk.Button(
            self,
            text=" Gửi",
            image=self.send_icon if self.send_icon else None,
            compound="left",
            font=("Inter", 12, "bold"),
            bg="#0099FF",
            fg="white",
            activebackground="#0088EE",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._handle_send
        )
        send_btn.grid(row=0, column=1, sticky="ns", padx=(0, 20), pady=15, ipadx=12, ipady=4)
        
        # Hover effect
        send_btn.bind("<Enter>", lambda e: send_btn.config(bg="#0088EE"))
        send_btn.bind("<Leave>", lambda e: send_btn.config(bg="#0099FF"))
    
    def _clear_placeholder(self, event):
        """Xóa placeholder khi focus"""
        if self.message_entry.get() == "Nhập tin nhắn ....":
            self.message_entry.delete(0, tk.END)
            self.message_entry.config(fg="black")
    
    def _restore_placeholder(self, event):
        """Khôi phục placeholder khi không có text"""
        if not self.message_entry.get().strip():
            self.message_entry.insert(0, "Nhập tin nhắn ....")
            self.message_entry.config(fg="#888888")
    
    def _handle_send(self):
        text = self.message_entry.get().strip()
        if not text:
            return

        # Gọi callback gửi tin nhắn
        if self.on_send:
            self.on_send(text)

        # Kiểm tra widget còn tồn tại trước khi xóa
        try:
            if self.message_entry.winfo_exists():
                self.message_entry.delete(0, tk.END)
        except tk.TclError:
            pass
    
    def get_text(self):
        """Lấy text từ entry"""
        text = self.message_entry.get().strip()
        return text if text != "Nhập tin nhắn ...." else ""
    
    def clear(self):
        """Xóa nội dung entry"""
        self.message_entry.delete(0, tk.END)
        self.message_entry.focus_set()