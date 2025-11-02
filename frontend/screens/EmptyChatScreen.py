import tkinter as tk
from PIL import Image, ImageTk
import os
from datetime import datetime
from components.ChatHeader import ChatHeader
from components.ChatInput import ChatInput
from backend.Config.ConversationModel import ConversationModel
from backend.Config.MessageModel import MessageModel
from backend.Services.RSAService import RSAService

class EmptyChatScreen(tk.Frame):
    def __init__(self, parent, contact_name, avatar_icon, current_user_id=None, partner_id=None, on_first_message=None):
        super().__init__(parent, bg="#FAFAFA")
        self.contact_name = contact_name
        self.avatar_icon = avatar_icon
        self.current_user_id = current_user_id
        self.partner_id = partner_id
        self.on_first_message = on_first_message

        # ===== CẤU HÌNH GRID =====
        self.grid_rowconfigure(1, weight=1) 
        self.grid_columnconfigure(0, weight=1)

        # ===== LẤY KHÓA RSA TỪ BACKEND =====
        rsa_keys = RSAService.get_user_keys(current_user_id, partner_id)

        # ===== HEADER (với RSA panel) =====
        self.header = ChatHeader(
            self, contact_name, avatar_icon,
            current_user_id=current_user_id,
            partner_id=partner_id,
            rsa_keys=rsa_keys
        )
        self.header.grid(row=0, column=0, sticky="ew")

        # ===== NỘI DUNG CHÍNH (Secure Message Placeholder) =====
        content = tk.Frame(self, bg="#FAFAFA")
        content.grid(row=1, column=0, sticky="nsew") 

        try:
            shield_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "security.png")
            shield_img = Image.open(shield_path).resize((80, 80), Image.Resampling.LANCZOS)
            self.shield_icon = ImageTk.PhotoImage(shield_img)
            tk.Label(content, image=self.shield_icon, bg="#FAFAFA").pack(pady=(100, 15))
        except:
            tk.Label(content, text="🛡️", font=("Arial", 60), bg="#FAFAFA").pack(pady=(100, 15))

        tk.Label(
            content,
            text="Trò chuyện bảo mật",
            font=("Inter", 16, "bold"),
            bg="#FAFAFA",
            fg="black"
        ).pack(pady=(0, 5))

        tk.Label(
            content,
            text="Tất cả tin nhắn đã được mã hóa",
            font=("Inter", 11),
            bg="#FAFAFA",
            fg="#555555"
        ).pack()

        tk.Label(
            content,
            text="RSA-2048 + AES-256",
            font=("Inter", 9, "italic"),
            bg="#FAFAFA",
            fg="#777777"
        ).pack(pady=(5, 0))

        # ===== KHUNG NHẬP TIN NHẮN =====
        self.chat_input = ChatInput(self, on_send=self.handle_send_message)
        self.chat_input.grid(row=2, column=0, sticky="ew")

    def handle_send_message(self, text):
        """Xử lý khi gửi tin nhắn đầu tiên - tạo conversation và lưu tin nhắn"""
        if not text.strip():
            return
        
        # Tạo conversation mới
        conv = ConversationModel.create_conversation(self.current_user_id, self.partner_id)
        conversation_id = conv["conversation_id"]
        
        # Lưu tin nhắn đầu tiên
        MessageModel.create_message(
            conversation_id,
            self.current_user_id,
            self.partner_id,
            message_encrypted=text
        )
        
        # Chuyển sang ChatScreen
        if self.on_first_message:
            self.on_first_message(self.contact_name, text)