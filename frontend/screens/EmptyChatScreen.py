import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from datetime import datetime
import socketio 

# Import components
from components.ChatHeader import ChatHeader
from components.ChatInput import ChatInput

# Import backend logic
from backend.Config.ConversationModel import ConversationModel
from backend.Services.RSAService import RSAService
from backend.Core.ChatManager import ChatManager


class EmptyChatScreen(tk.Frame):
    """Màn hình hiển thị khi chưa có tin nhắn nào được gửi giữa 2 người."""
    def __init__(self, parent, controller, sio_client, contact_name, avatar_icon, 
                 current_user_id=None, partner_id=None, on_first_message=None, 
                 conversation_id=None, chat_manager=None, partner_is_online=False):
        super().__init__(parent, bg="#FAFAFA")
        self.controller = controller
        self.sio_client = sio_client
        self.contact_name = contact_name
        self.avatar_icon = avatar_icon
        self.current_user_id = current_user_id
        self.partner_id = partner_id
        self.on_first_message = on_first_message
        self.conversation_id = conversation_id
        self.chat_manager = chat_manager
        self.partner_is_online = partner_is_online

        self.grid_rowconfigure(1, weight=1) 
        self.grid_columnconfigure(0, weight=1)

        my_keypair = RSAService.get_keypair(current_user_id)
        partner_public_key = RSAService.get_public_key(partner_id)
        
        rsa_keys = {
            "my_public_key": my_keypair["public_key"] if my_keypair else None,
            "partner_public_key": partner_public_key
        }

        self.header = ChatHeader(
            self, contact_name, avatar_icon,
            current_user_id=current_user_id,
            partner_id=partner_id,
            rsa_keys=rsa_keys,
            partner_is_online=self.partner_is_online
        )
        self.header.grid(row=0, column=0, sticky="ew")

        empty_frame = tk.Frame(self, bg="#FAFAFA")
        empty_frame.grid(row=1, column=0, sticky="nsew")
        empty_frame.grid_rowconfigure(0, weight=1)
        empty_frame.grid_columnconfigure(0, weight=1)

        content = tk.Frame(empty_frame, bg="#FAFAFA")
        content.grid(row=0, column=0, sticky="")

        #  ICON SECURITY (Trò chuyện bảo mật)
        try:
            security_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "security.png")
            security_img = Image.open(security_path).resize((100, 100), Image.Resampling.LANCZOS)
            self.security_icon = ImageTk.PhotoImage(security_img)
            tk.Label(content, image=self.security_icon, bg="#FAFAFA").pack(pady=(0, 20))
        except Exception as e:
            print(f"Không tìm thấy security.png: {e}")
            tk.Label(content, text="🛡️", font=("Inter", 60), bg="#FAFAFA").pack(pady=(0, 20))

        tk.Label(
            content,
            text="Trò chuyện bảo mật",
            font=("Inter", 18, "bold"),
            bg="#FAFAFA",
            fg="#333333"
        ).pack(pady=(0, 10))
        
        tk.Label(
            content,
            text="Tất cả tin nhắn đã được mã hóa",
            font=("Inter", 11),
            bg="#FAFAFA",
            fg="#888888"
        ).pack(pady=(0, 5))
        
        tk.Label(
            content,
            text="RSA-2048 + AES-256",
            font=("Inter", 10, "italic"),
            bg="#FAFAFA",
            fg="#999999"
        ).pack(pady=(0, 0))

        self.chat_input = ChatInput(self, on_send=self.handle_send_message)
        self.chat_input.grid(row=2, column=0, sticky="ew")
        
        if self.sio_client and self.sio_client.connected:
            self.register_socket_events()
    
    def register_socket_events(self):
        """Đăng ký lắng nghe event message_queued"""
        self.sio_client.on('message_queued', self.on_message_queued)
    
   
    def on_message_queued(self, data):
        """
        Xử lý khi tin nhắn bị pending (chờ người nhận đăng nhập).
        Chỉ log thông tin, không cần hiển thị popup vì đã hiển thị local echo.
        """
        plain_text = data.get('plain_text', '')
        contact_name = self.contact_name

        print(f" Message queued: Tin nhắn đã được lưu và sẽ gửi khi {contact_name} đăng nhập. Nội dung: {plain_text[:50]}...")

    
    def handle_send_message(self, plain_text):
        """Gửi tin nhắn → Local Echo → Mã hóa/Pending → Chuyển sang ChatScreen"""
        plain_text = plain_text.strip()
        if not plain_text:
            return
        
        # 1. XÓA INPUT TRƯỚC (tránh TclError)
        self.chat_input.clear()
        
        # 2. CẬP NHẬT SIDEBAR (TRƯỚC KHI GỌI BACKEND)
        latest_time_obj = datetime.now()
        
        if self.chat_manager:
            try:
                self.chat_manager.update_sidebar_after_send(
                    self.contact_name,
                    plain_text[:30] + "...",
                    latest_time_obj
                )
                self.chat_manager.update_unread_count_in_sidebar(self.contact_name, 0)
            except Exception as e:
                print(f"Lỗi cập nhật sidebar từ EmptyChatScreen: {e}")
        
        # 3. GỌI HÀM CHUYỂN KHUNG (Chuyển sang ChatScreen ngay lập tức)
        if self.on_first_message:
            self.on_first_message(self.contact_name, {
                'conversation_id': self.conversation_id, 
                'status': 'local_echo',
                'plain_text': plain_text,  
                'sent_at': latest_time_obj.isoformat()
            })
        
        # 4. GỌI CHAT MANAGER ĐỂ THỰC HIỆN TOÀN BỘ LUỒNG (ASYNC)
        success, result_data = ChatManager.send_encrypted_message(
            sender_id=self.current_user_id,
            partner_id=self.partner_id,
            plain_text_message=plain_text
        )

        if success:
            status = result_data.get('status', 'sent')
            if status == 'pending':
                 print(f" Message is pending for {self.contact_name}")
            else:
                 print(f" Message sent (ID: {result_data.get('message_id')}).")
        else:
            print(f" Error sending message in background: {result_data}")
            
    def destroy(self):
        """Dọn dẹp"""
        if self.sio_client:
            try:
                self.sio_client.off('message_queued')
            except:
                pass
        super().destroy()