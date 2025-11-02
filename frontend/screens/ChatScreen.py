# import tkinter as tk
# from tkinter import ttk
# from PIL import Image, ImageTk
# import os
# from datetime import datetime
# from components.ChatHeader import ChatHeader
# from components.ChatInput import ChatInput
# from backend.Config.MessageModel import MessageModel
# from backend.Config.ConversationModel import ConversationModel
# from backend.Services.RSAService import RSAService


# class ChatScreen(tk.Frame):
#     def __init__(self, parent, contact_name, avatar_icon, current_user_id, partner_id):
#         super().__init__(parent, bg="#F9F8F8")
#         self.contact_name = contact_name
#         self.avatar_icon = avatar_icon
#         self.current_user_id = current_user_id
#         self.partner_id = partner_id

#         # ===== LẤY CONVERSATION_ID GIỮA 2 NGƯỜI =====
#         conv = ConversationModel.get_conversation_between_users(current_user_id, partner_id)
#         self.conversation_id = conv["conversation_id"] if conv else None

#         # ===== CẤU HÌNH LƯỚI =====
#         self.grid_rowconfigure(1, weight=1)
#         self.grid_columnconfigure(0, weight=1)

#         # ===== LẤY KHÓA RSA TỪ BACKEND =====
#         rsa_keys = RSAService.get_user_keys(current_user_id, partner_id)

#         # ===== HEADER (component với RSA panel) =====
#         self.header = ChatHeader(
#             self, contact_name, avatar_icon, 
#             current_user_id=current_user_id, 
#             partner_id=partner_id,
#             rsa_keys=rsa_keys
#         )
#         self.header.grid(row=0, column=0, sticky="ew")

#         # ===== KHUNG CHAT =====
#         self.create_messages_area()

#         # ===== KHUNG NHẬP =====
#         self.chat_input = ChatInput(self, on_send=self.handle_send_message)
#         self.chat_input.grid(row=2, column=0, sticky="ew")

#         # ===== TÙY CHỈNH SCROLLBAR =====
#         self.setup_custom_scrollbar_style()

#         # ===== TẢI TIN NHẮN TỪ DATABASE =====
#         if self.conversation_id:
#             self.load_messages_from_db()

#     # ========================================
#     # KHUNG CHAT
#     # ========================================
#     def create_messages_area(self):
#         self.canvas = tk.Canvas(self, bg="#F9F8F8", highlightthickness=0)
#         self.canvas.grid(row=1, column=0, sticky="nsew")

#         self.scrollbar = ttk.Scrollbar(
#             self, orient="vertical", command=self.canvas.yview,
#             style="Custom.Vertical.TScrollbar"
#         )
#         self.scrollbar_is_visible = False

#         self.scrollable_frame = tk.Frame(self.canvas, bg="#F9F8F8")
#         # Thay vì bind Configure, ta sẽ dùng canvas.itemconfig để kiểm soát chiều rộng
#         self.scrollable_frame.bind(
#             "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
#         )

#         # BUỘC SCROLLABLE_FRAME GIÃN THEO CHIỀU RỘNG CỦA CANVAS
#         # Cần phải dùng after(0) để lấy được kích thước canvas chính xác sau khi grid
#         self.after(0, lambda: self._initialize_canvas_window())
#         self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
#         # Bắt sự kiện thay đổi kích thước canvas để cập nhật chiều rộng cửa sổ
#         self.canvas.bind("<Configure>", self.on_canvas_resize)

#         self.after(100, self.update_scrollbar_visibility)
#         self.scrollable_frame.bind("<Configure>", lambda e: self.after(10, self.update_scrollbar_visibility))

#         self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
#         self.canvas.bind_all("<Button-4>", self.on_mouse_wheel)
#         self.canvas.bind_all("<Button-5>", self.on_mouse_wheel)
        
#     def _initialize_canvas_window(self):
#         """Khởi tạo cửa sổ canvas sau khi canvas đã có kích thước"""
#         # Đảm bảo scrollable_frame chiếm toàn bộ chiều rộng của canvas
#         self.canvas_window = self.canvas.create_window(
#             (0, 0), 
#             window=self.scrollable_frame, 
#             anchor="nw", 
#             width=self.canvas.winfo_width()
#         )

#     def on_canvas_resize(self, event):
#         """Đảm bảo scrollable_frame luôn có chiều rộng bằng canvas"""
#         # Cập nhật chiều rộng của cửa sổ trong canvas
#         if hasattr(self, 'canvas_window') and self.canvas_window:
#             self.canvas.itemconfig(self.canvas_window, width=event.width)
#         self.canvas.configure(scrollregion=self.canvas.bbox("all"))
#         self.update_scrollbar_visibility()


#     def on_mouse_wheel(self, event):
#         if event.delta > 0 or event.num == 4:
#             self.canvas.yview_scroll(-1, "units")
#         elif event.num == 5 or event.delta < 0:
#             self.canvas.yview_scroll(1, "units")
#         return "break"

#     def update_scrollbar_visibility(self):
#         """Cập nhật hiển thị scrollbar - FIX lỗi TclError"""
#         try:
#             self.canvas.update_idletasks()
#             self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
#             # Kiểm tra canvas có được pack chưa
#             if not self.canvas.winfo_ismapped():
#                 return
            
#             canvas_height = self.canvas.winfo_height()
#             content_height = self.scrollable_frame.winfo_reqheight()
            
#             if content_height > canvas_height and canvas_height > 1:
#                 if not self.scrollbar_is_visible:
#                     self.scrollbar.grid(row=1, column=1, sticky="ns")
#                     self.scrollbar_is_visible = True
#             else:
#                 if self.scrollbar_is_visible:
#                     self.scrollbar.grid_remove()
#                     self.scrollbar_is_visible = False
#         except Exception as e:
#             # print(f"Scrollbar visibility error: {e}") # Bỏ dòng này để tránh lỗi
#             pass

#     # ========================================
#     # TẢI TIN NHẮN THẬT TỪ DATABASE
#     # ========================================
#     def load_messages_from_db(self):
#         """Lấy tin nhắn từ DB và hiển thị"""
#         messages = MessageModel.get_messages_by_conversation(self.conversation_id)
#         for msg in messages:
#             sender = "me" if msg["sender_id"] == self.current_user_id else "them"
#             # Giả định tin nhắn đã được giải mã cho việc hiển thị (như trong code cũ)
#             text = msg["message_encrypted"] 
#             time_str = msg["sent_at"].strftime("%H:%M")
#             self.add_message(sender, text, time_str)

#     # ========================================
#     # GỬI TIN NHẮN
#     # ========================================
#     def handle_send_message(self, text):
#         """Gửi tin nhắn → lưu DB → hiển thị"""
#         if not text.strip():
#             return
        
#         # Nếu chưa có conversation, tạo mới
#         if not self.conversation_id:
#             conv = ConversationModel.create_conversation(self.current_user_id, self.partner_id)
#             self.conversation_id = conv["conversation_id"]

#         # Giả định text ở đây là tin nhắn đã mã hóa
#         MessageModel.create_message(
#             self.conversation_id,
#             self.current_user_id,
#             self.partner_id,
#             message_encrypted=text
#         )

#         self.add_message("me", text, datetime.now().strftime("%H:%M"))

#     # ========================================
#     # HIỂN THỊ TIN NHẮN (ĐÃ FIX CĂN CHỈNH)
#     # ========================================
#     def add_message(self, sender, text, time):
#         """Hiển thị tin nhắn dạng bong bóng với căn chỉnh động"""
#         # --- Khung chứa tin nhắn và thời gian ---
#         msg_frame = tk.Frame(self.scrollable_frame, bg="#F9F8F8")
#         # Sử dụng fill="x" để đảm bảo msg_frame chiếm hết chiều rộng của scrollable_frame
#         msg_frame.pack(fill="x", pady=8, padx=10) 

#         # --- CẤU HÌNH GRID CHO msg_frame (3 cột: Lề Trái, Nội dung, Lề Phải) ---
#         # Cột 0 & 2: Dùng để giới hạn lề 80px (sử dụng Frame rỗng) và chiếm không gian trống khi phóng to (weight=1).
#         # Cột 1: Không dùng trong kịch bản này, nhưng giữ để chia cột rõ ràng.
        
#         msg_frame.grid_columnconfigure(0, weight=1) 
#         msg_frame.grid_columnconfigure(1, weight=0) 
#         msg_frame.grid_columnconfigure(2, weight=1) 

#         # Lề 10px chung cho bong bóng
#         P_X = 10
#         # Khoảng cách lề cố định 80px
#         MARGIN_SIZE = 80 
        
#         if sender == "me":
#             # --- TIN NHẮN CỦA MÌNH (Căn phải) ---
            
#             # CỘT 0: Frame rỗng giới hạn lề trái 80px
#             # Nó sẽ giãn tối đa nhờ weight=1, nhưng width=80 đảm bảo lề tối thiểu 80px
#             tk.Frame(msg_frame, bg="#F9F8F8", width=MARGIN_SIZE).grid(row=0, column=0, sticky="ew")

#             # CỘT 2: Bong bóng tin nhắn
#             bubble = tk.Frame(msg_frame, bg="#0099FF", padx=12, pady=8)
#             # grid vào cột 2, sticky="e" để căn phải
#             bubble.grid(row=0, column=2, sticky="e", padx=(0, P_X)) 
            
#             tk.Label(bubble, text=text, font=("Inter", 12),
#                      bg="#0099FF", fg="white", wraplength=380, justify="left").pack(fill="x")
                     
#             # THỜI GIAN (Nằm ở hàng dưới, căn phải)
#             tk.Label(msg_frame, text=time, font=("Inter", 8),
#                      fg="#888888", bg="#F9F8F8").grid(row=1, column=2, sticky="e", padx=(0, 15))

#         else:
#             # --- TIN NHẮN CỦA NGƯỜI KHÁC (Căn trái) ---
            
#             # CỘT 0: Bong bóng tin nhắn
#             bubble = tk.Frame(msg_frame, bg="#FFFFFF", padx=12, pady=8)
#             # grid vào cột 0, sticky="w" để căn trái
#             bubble.grid(row=0, column=0, sticky="w", padx=(P_X, 0)) 
            
#             tk.Label(bubble, text=text, font=("Inter", 12),
#                      bg="#FFFFFF", fg="black", wraplength=380, justify="left").pack(fill="x")
                     
#             # CỘT 2: Frame rỗng giới hạn lề phải 80px
#             tk.Frame(msg_frame, bg="#F9F8F8", width=MARGIN_SIZE).grid(row=0, column=2, sticky="ew")

#             # THỜI GIAN (Nằm ở hàng dưới, căn trái)
#             tk.Label(msg_frame, text=time, font=("Inter", 8),
#                      fg="#888888", bg="#F9F8F8").grid(row=1, column=0, sticky="w", padx=(15, 0))

#         self.after(10, lambda: self.canvas.yview_moveto(1.0))

#     # ========================================
#     # CẤU HÌNH STYLE CHO SCROLLBAR
#     # ========================================
#     def setup_custom_scrollbar_style(self):
#         style = ttk.Style()
#         style.theme_use('default')
#         style.configure(
#             "Custom.Vertical.TScrollbar",
#             background="#E0E0E0",
#             troughcolor="#F9F8F8",
#             borderwidth=0,
#             arrowsize=0,
#             width=8
#         )
#         style.map("Custom.Vertical.TScrollbar",
#                   background=[("active", "#B0B0B0"), ("!active", "#E0E0E0")])

#     # ========================================
#     # DỌN RÁC
#     # ========================================
#     def destroy(self):
#         try:
#             self.canvas.unbind_all("<MouseWheel>")
#             self.canvas.unbind_all("<Button-4>")
#             self.canvas.unbind_all("<Button-5>")
#             self.canvas.unbind("<Configure>")
#         except:
#             pass
#         super().destroy()

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
from datetime import datetime
from components.ChatHeader import ChatHeader
from components.ChatInput import ChatInput
from backend.Config.MessageModel import MessageModel
from backend.Config.ConversationModel import ConversationModel
from backend.Services.RSAService import RSAService


class ChatScreen(tk.Frame):
    def __init__(self, parent, contact_name, avatar_icon, current_user_id, partner_id):
        super().__init__(parent, bg="#F9F8F8")
        self.contact_name = contact_name
        self.avatar_icon = avatar_icon
        self.current_user_id = current_user_id
        self.partner_id = partner_id

        # ===== LẤY CONVERSATION_ID GIỮA 2 NGƯỜI =====
        conv = ConversationModel.get_conversation_between_users(current_user_id, partner_id)
        self.conversation_id = conv["conversation_id"] if conv else None

        # ===== CẤU HÌNH LƯỚI =====
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ===== LẤY KHÓA RSA TỪ BACKEND =====
        # Lấy khóa của mình
        my_keypair = RSAService.get_keypair(current_user_id)
        # Lấy khóa công khai của đối phương
        partner_public_key = RSAService.get_public_key(partner_id)
        
        rsa_keys = {
            "my_public_key": my_keypair["public_key"] if my_keypair else None,
            "my_private_key": my_keypair["private_key"] if my_keypair else None,
            "partner_public_key": partner_public_key
        }

        # ===== HEADER (component với RSA panel) =====
        self.header = ChatHeader(
            self, contact_name, avatar_icon, 
            current_user_id=current_user_id, 
            partner_id=partner_id,
            rsa_keys=rsa_keys
        )
        self.header.grid(row=0, column=0, sticky="ew")

        # ===== KHUNG CHAT =====
        self.create_messages_area()

        # ===== KHUNG NHẬP =====
        self.chat_input = ChatInput(self, on_send=self.handle_send_message)
        self.chat_input.grid(row=2, column=0, sticky="ew")

        # ===== TÙY CHỈNH SCROLLBAR =====
        self.setup_custom_scrollbar_style()

        # ===== TẢI TIN NHẮN TỪ DATABASE =====
        if self.conversation_id:
            self.load_messages_from_db()

    # ========================================
    # KHUNG CHAT
    # ========================================
    def create_messages_area(self):
        self.canvas = tk.Canvas(self, bg="#F9F8F8", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview,
            style="Custom.Vertical.TScrollbar"
        )
        self.scrollbar_is_visible = False

        self.scrollable_frame = tk.Frame(self.canvas, bg="#F9F8F8")
        self.scrollable_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.after(0, lambda: self._initialize_canvas_window())
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.after(100, self.update_scrollbar_visibility)
        self.scrollable_frame.bind("<Configure>", lambda e: self.after(10, self.update_scrollbar_visibility))

        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self.on_mouse_wheel)
        
    def _initialize_canvas_window(self):
        """Khởi tạo cửa sổ canvas sau khi canvas đã có kích thước"""
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor="nw", 
            width=self.canvas.winfo_width()
        )

    def on_canvas_resize(self, event):
        """Đảm bảo scrollable_frame luôn có chiều rộng bằng canvas"""
        if hasattr(self, 'canvas_window') and self.canvas_window:
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.update_scrollbar_visibility()


    def on_mouse_wheel(self, event):
        if event.delta > 0 or event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        return "break"

    def update_scrollbar_visibility(self):
        """Cập nhật hiển thị scrollbar - FIX lỗi TclError"""
        try:
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            if not self.canvas.winfo_ismapped():
                return
            
            canvas_height = self.canvas.winfo_height()
            content_height = self.scrollable_frame.winfo_reqheight()
            
            if content_height > canvas_height and canvas_height > 1:
                if not self.scrollbar_is_visible:
                    self.scrollbar.grid(row=1, column=1, sticky="ns")
                    self.scrollbar_is_visible = True
            else:
                if self.scrollbar_is_visible:
                    self.scrollbar.grid_remove()
                    self.scrollbar_is_visible = False
        except Exception as e:
            pass

    # ========================================
    # TẢI TIN NHẮN THẬT TỪ DATABASE
    # ========================================
    def load_messages_from_db(self):
        """Lấy tin nhắn từ DB và hiển thị"""
        messages = MessageModel.get_messages_by_conversation(self.conversation_id)
        for msg in messages:
            sender = "me" if msg["sender_id"] == self.current_user_id else "them"
            text = msg["message_encrypted"] 
            time_str = msg["sent_at"].strftime("%H:%M")
            self.add_message(sender, text, time_str)

    # ========================================
    # GỬI TIN NHẮN
    # ========================================
    def handle_send_message(self, text):
        """Gửi tin nhắn → lưu DB → hiển thị"""
        if not text.strip():
            return
        
        # Nếu chưa có conversation, tạo mới
        if not self.conversation_id:
            conv = ConversationModel.create_conversation(self.current_user_id, self.partner_id)
            self.conversation_id = conv["conversation_id"]

        # Giả định text ở đây là tin nhắn đã mã hóa
        MessageModel.create_message(
            self.conversation_id,
            self.current_user_id,
            self.partner_id,
            message_encrypted=text
        )

        self.add_message("me", text, datetime.now().strftime("%H:%M"))

    # ========================================
    # HIỂN THỊ TIN NHẮN (ĐÃ FIX CĂN CHỈNH)
    # ========================================
    def add_message(self, sender, text, time):
        """Hiển thị tin nhắn dạng bong bóng với căn chỉnh động"""
        msg_frame = tk.Frame(self.scrollable_frame, bg="#F9F8F8")
        msg_frame.pack(fill="x", pady=8, padx=10) 

        msg_frame.grid_columnconfigure(0, weight=1) 
        msg_frame.grid_columnconfigure(1, weight=0) 
        msg_frame.grid_columnconfigure(2, weight=1) 

        P_X = 10
        MARGIN_SIZE = 80 
        
        if sender == "me":
            # --- TIN NHẮN CỦA MÌNH (Căn phải) ---
            tk.Frame(msg_frame, bg="#F9F8F8", width=MARGIN_SIZE).grid(row=0, column=0, sticky="ew")

            bubble = tk.Frame(msg_frame, bg="#0099FF", padx=12, pady=8)
            bubble.grid(row=0, column=2, sticky="e", padx=(0, P_X)) 
            
            tk.Label(bubble, text=text, font=("Inter", 12),
                     bg="#0099FF", fg="white", wraplength=380, justify="left").pack(fill="x")
                     
            tk.Label(msg_frame, text=time, font=("Inter", 8),
                     fg="#888888", bg="#F9F8F8").grid(row=1, column=2, sticky="e", padx=(0, 15))

        else:
            # --- TIN NHẮN CỦA NGƯỜI KHÁC (Căn trái) ---
            bubble = tk.Frame(msg_frame, bg="#FFFFFF", padx=12, pady=8)
            bubble.grid(row=0, column=0, sticky="w", padx=(P_X, 0)) 
            
            tk.Label(bubble, text=text, font=("Inter", 12),
                     bg="#FFFFFF", fg="black", wraplength=380, justify="left").pack(fill="x")
                     
            tk.Frame(msg_frame, bg="#F9F8F8", width=MARGIN_SIZE).grid(row=0, column=2, sticky="ew")

            tk.Label(msg_frame, text=time, font=("Inter", 8),
                     fg="#888888", bg="#F9F8F8").grid(row=1, column=0, sticky="w", padx=(15, 0))

        self.after(10, lambda: self.canvas.yview_moveto(1.0))

    # ========================================
    # CẤU HÌNH STYLE CHO SCROLLBAR
    # ========================================
    def setup_custom_scrollbar_style(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Vertical.TScrollbar",
            background="#E0E0E0",
            troughcolor="#F9F8F8",
            borderwidth=0,
            arrowsize=0,
            width=8
        )
        style.map("Custom.Vertical.TScrollbar",
                  background=[("active", "#B0B0B0"), ("!active", "#E0E0E0")])

    # ========================================
    # DỌN RÁC
    # ========================================
    def destroy(self):
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
            self.canvas.unbind("<Configure>")
        except:
            pass
        super().destroy()