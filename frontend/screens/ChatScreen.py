# frontend/screens/ChatScreen.py

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from datetime import datetime, timedelta
import socketio 

# Import components
from components.ChatHeader import ChatHeader
from components.ChatInput import ChatInput

# Import backend logic
from backend.Config.MessageModel import MessageModel
from backend.Config.ConversationModel import ConversationModel
from backend.Services.RSAService import RSAService
from backend.Core.ChatManager import ChatManager

class ChatScreen(tk.Frame):
    def __init__(self, parent, controller, sio_client, contact_name, avatar_icon, current_user_id, partner_id, conversation_id=None, chat_manager=None, partner_is_online=False, first_message_data=None):
        super().__init__(parent, bg="#F9F8F8")
        self.parent_frame = parent
        self.controller = controller
        self.sio_client = sio_client
        self.contact_name = contact_name
        self.avatar_icon = avatar_icon
        self.current_user_id = current_user_id
        self.partner_id = partner_id
        self.chat_manager = chat_manager
        self.partner_is_online = partner_is_online
        self.first_message_data = first_message_data

        conv = ConversationModel.get_conversation_between_users(current_user_id, partner_id)
        self.conversation_id = conversation_id or (conv["conversation_id"] if conv else None) 

        #  Chỉ row 2 (messages area) có weight=1
        self.grid_rowconfigure(2, weight=1)
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
        
        #  Thêm search bar (ẩn mặc định)
        self.create_search_bar()

        self.create_messages_area()

        self.chat_input = ChatInput(self, on_send=self.handle_send_message)
        self.chat_input.grid(row=3, column=0, sticky="ew")  #  Đổi từ row=2 thành row=3

        self.setup_custom_scrollbar_style()

        # ===  ĐĂNG KÝ ChatScreen VÀO CHAT_MANAGER ĐỂ NHẬN EVENT ===
        if self.chat_manager:
            self.chat_manager.active_chat_screen = self
            print(f" Registered ChatScreen for conv {self.conversation_id}")
        
        # === ĐĂNG KÝ SOCKET EVENTS (XÓA CŨ TRƯỚC) ===
        if self.sio_client and self.sio_client.connected:
            # Xóa event handlers cũ
            try:
                self.sio_client.off('new_message')
                self.sio_client.off('marked_as_read')
                self.sio_client.off('message_recalled')
            except:
                pass
            
            # Đăng ký mới
            self.sio_client.on('new_message', self.on_new_message)
            self.sio_client.on('marked_as_read', self.on_marked_as_read)
            self.sio_client.on('message_recalled', self.on_message_recalled)
            print(f" Socket events registered for ChatScreen conv {self.conversation_id}")

        # === HIỂN THI TIN NHẮN ĐẦU TIÊN (LOCAL ECHO) ===
        # Nếu có first_message_data (tin nhắn vừa gửi), hiển thị local echo trước
        if self.first_message_data and self.first_message_data.get('plain_text'):
             plain_text = self.first_message_data.get('plain_text')
             
             try:
                 time_obj = datetime.fromisoformat(self.first_message_data.get('sent_at'))
                 time_str = time_obj.strftime('%H:%M')
             except:
                 time_str = datetime.now().strftime('%H:%M')
                 
             # LOCAL ECHO: Không có message_id
             self.add_message("me", plain_text, time_str, is_read=False, message_id=None)
        
        # Tải tin nhắn từ database (CHỈ KHI KHÔNG CÓ local echo hoặc đã có conversation)
        # Vì tin nhắn pending không có trong messages table
        elif self.conversation_id:
            self.load_messages_from_db()
            
        #  JOIN ROOM CHO TẤT CẢ TRƯỜNG HỢP (cả khi có local echo)
        if self.conversation_id and self.sio_client and self.sio_client.connected:
            self.after(50, self.send_join_request)
            
            #  Chỉ mark as read sau khi user xem tin nhắn (2 giây hoặc khi scroll)
            self.after(2000, self.auto_mark_as_read_if_at_bottom)

    # ========================================
    # SOCKETIO EVENTS & MANAGEMENT (GIỮ NGUYÊN)
    # ========================================
    def send_join_request(self):
        """Gửi yêu cầu join room với user_id để Server xác thực."""
        self.sio_client.emit('join_conversation', {
            'conversation_id': self.conversation_id,
            'user_id': self.current_user_id 
        })
        print(f" Joining conv {self.conversation_id} with user {self.current_user_id}")
    # Socket events được route qua chat_manager.active_chat_screen
    
    def on_pending_message_received(self, data):
        """
        Xử lý khi nhận được tin nhắn đã được xử lý từ pending queue
        """
        print(f" [ChatScreen] Received pending_message_processed event: {data}")
        # Logic này đã được chuyển sang Chat.py, nhưng giữ lại để debug
        pass
    
    def on_new_message(self, data):
        """Xử lý khi nhận được tin nhắn mới (đã mã hóa) từ WebSocket"""
        if data.get('conversation_id') != self.conversation_id:
            return 
            
        sender_id = data.get('sender_id')
        message_id = data.get('message_id')
        
        # Xóa local echo nếu là tin nhắn của mình
        if sender_id == self.current_user_id:
            if message_id:
                for widget in self.scrollable_frame.winfo_children():
                    if not hasattr(widget, 'message_id') or widget.message_id is None:
                        widget.destroy()
                        break
        
        plain_text, is_valid = ChatManager.decrypt_received_message(data, self.current_user_id)
        self.display_received_message(sender_id, plain_text, is_valid, data.get('sent_at'), is_read=False, message_id=message_id)
        
        #  Debounce sidebar update để giảm lag
        if self.chat_manager and plain_text:
            try:
                latest_time_obj = datetime.fromisoformat(data.get('sent_at'))
                
                # Delay 100ms để tránh update quá nhiều
                self.after(100, lambda: self.chat_manager.update_sidebar_after_send(
                    self.contact_name, 
                    plain_text.strip()[:30] + "...", 
                    latest_time_obj
                ))
            except Exception as e:
                print(f"Lỗi cập nhật sidebar khi nhận tin: {e}")
        
        #  Mark as read chỉ khi user đang ở cuối chat (đang xem)
        self.after(500, self.auto_mark_as_read_if_at_bottom)


    def has_message_displayed(self, message_id):
        """Kiểm tra tin nhắn đã được hiển thị chưa"""
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'message_id') and widget.message_id == message_id:
                return True
        return False
    
    def on_message_sent_success(self, data):
        """Xử lý xác nhận gửi thành công (tin nhắn của mình)"""
        print(f"Server confirmed message {data.get('message_id')} sent successfully.")
    
    def on_marked_as_read(self, data):
        """Xử lý khi partner đánh dấu tin nhắn là đã đọc"""
        conversation_id = data.get('conversation_id')
        reader_id = data.get('reader_id')
        
        # Chỉ cập nhật nếu là conversation hiện tại và người đọc là partner
        if conversation_id == self.conversation_id and reader_id != self.current_user_id:
            self.update_all_messages_read_status()
    
    def update_all_messages_read_status(self):
        """Cập nhật trạng thái đã đọc cho tất cả tin nhắn của mình"""
        for msg_frame in self.scrollable_frame.winfo_children():
            # Tìm time_frame ở row=1, column=2 (chỉ có ở tin nhắn của mình)
            for child in msg_frame.grid_slaves(row=1, column=2):
                if isinstance(child, tk.Frame):
                    # Tìm read icon label và cập nhật
                    for label in child.winfo_children():
                        if isinstance(label, tk.Label):
                            text = label.cget('text')
                            if text == "✓":
                                label.config(text="✓✓", fg="#4FC3F7")
                                break
                    break
    
    def on_message_recalled(self, data):
        """Xử lý khi partner thu hồi tin nhắn"""
        message_id = data.get('message_id')
        conversation_id = data.get('conversation_id')
        print(f"↩ [ChatScreen] Received message_recalled: message_id={message_id}, conversation_id={conversation_id}")
        print(f"↩ [ChatScreen] Current conversation_id={self.conversation_id}")
        
        # Kiểm tra conversation
        if conversation_id != self.conversation_id:
            print(f" Wrong conversation, ignoring")
            return
        
        # Tìm và thay thế nội dung tin nhắn
        found = False
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'message_id'):
                print(f" Checking widget with message_id={widget.message_id}")
                if widget.message_id == message_id:
                    found = True
                    print(f" Found widget! Replacing content...")
                    
                    # Tìm bubble frame trong widget (duyệt tất cả children)
                    def find_and_replace_bubble(parent):
                        for child in parent.winfo_children():
                            if isinstance(child, tk.Frame):
                                bg_color = child.cget('bg')
                                if bg_color in ['#FFFFFF', '#0099FF']:
                                    print(f" Found bubble with bg={bg_color}")
                                    # Xóa nội dung cũ
                                    for label in child.winfo_children():
                                        label.destroy()
                                    
                                    # Thêm text "đã thu hồi"
                                    recalled_text = f"{self.contact_name} đã thu hồi tin nhắn"
                                    tk.Label(
                                        child, 
                                        text=recalled_text,
                                        font=("Inter", 11, "italic"),
                                        bg=bg_color,
                                        fg="#888888" if bg_color == '#FFFFFF' else "white",
                                        wraplength=380,
                                        justify="left"
                                    ).pack(fill="x")
                                    print(f"✅ Replaced message {message_id} with recall notice")
                                    return True
                                else:
                                    # Tìm tiếp trong children
                                    if find_and_replace_bubble(child):
                                        return True
                        return False
                    
                    if find_and_replace_bubble(widget):
                        return
                    else:
                        print(f" Could not find bubble frame in widget")
                    break
        
        if not found:
            print(f" Message {message_id} not found in UI")
            print(f" Available message_ids: {[w.message_id for w in self.scrollable_frame.winfo_children() if hasattr(w, 'message_id')]}")
    
    def update_all_sent_messages_to_read(self):
        """Cập nhật tất cả tin nhắn đã gửi (của mình) thành trạng thái đã đọc (✓✓)"""
        for widget in self.scrollable_frame.winfo_children():
            # Tìm các message frame của mình (có bubble màu xanh)
            try:
                # Tìm time_frame (row=1, column=2)
                for child in widget.grid_slaves(row=1, column=2):
                    if isinstance(child, tk.Frame):
                        # Tìm label icon đầu tiên (read status)
                        labels = [w for w in child.winfo_children() if isinstance(w, tk.Label)]
                        if labels:
                            icon_label = labels[0]
                            # Cập nhật icon và màu
                            icon_label.config(text="✓✓", fg="#4FC3F7")
                            print(f" Updated message to read status")
            except Exception as e:
                print(f" Error updating message status: {e}")
                continue
        
    def display_received_message(self, sender_id, plain_text, is_valid, sent_at, is_read=False, message_id=None):
        """Hàm helper để hiển thị tin nhắn sau khi giải mã"""
        is_mine = sender_id == self.current_user_id
        
        display_text = plain_text
        if not is_valid:
            display_text = f"[ERROR: Giải mã thất bại/Bị thay đổi]"
            
        try:
            time_obj = datetime.fromisoformat(sent_at)
            time_str = self.format_time_display(time_obj)
        except:
            time_str = datetime.now().strftime('%H:%M')
            
        #  Truyền is_read cho tin nhắn của mình
        read_status = is_read if is_mine else False
        sender_type = "me" if is_mine else "them"
        
        # Gọi trực tiếp add_message
        self.add_message(sender_type, display_text, time_str, is_read=read_status, message_id=message_id)
    
    def format_time_display(self, time_obj):
        """Format thời gian: Hôm nay HH:MM, Hôm qua HH:MM, hoặc DD/MM HH:MM"""
        now = datetime.now()
        today = now.date()
        msg_date = time_obj.date()
        
        time_part = time_obj.strftime('%H:%M')
        
        if msg_date == today:
            return f"Hôm nay {time_part}"
        elif msg_date == today - timedelta(days=1):
            return f"Hôm qua {time_part}"
        else:
            return time_obj.strftime('%d/%m %H:%M')

    # ========================================
    # TẢI TIN NHẮN THẬT TỪ DATABASE
    # ========================================
    def load_messages_from_db(self):
        """Lấy tin nhắn đã mã hóa từ DB và hiển thị đã giải mã"""
        for widget in self.scrollable_frame.winfo_children():
             widget.destroy()
             
        messages = MessageModel.get_messages_by_conversation(self.conversation_id)
        
        for msg in messages:
            #  Kiểm tra tin nhắn đã thu hồi
            if msg.get('message_encrypted') == '[RECALLED]':
                print(f"↩ Loading recalled message: {msg.get('message_id')}")
                # Hiển thị thông báo thu hồi
                is_mine = msg["sender_id"] == self.current_user_id
                time_obj = msg["sent_at"]
                time_str = self.format_time_display(time_obj)
                message_id = msg.get('message_id')
                
                recalled_text = "Bạn đã thu hồi tin nhắn" if is_mine else f"{self.contact_name} đã thu hồi tin nhắn"
                
                # Tạo tin nhắn recalled với style italic
                self.add_recalled_message(is_mine, recalled_text, time_str, message_id)
                continue
            
            message_data={
                'conversation_id': self.conversation_id,
                'message_encrypted': msg['message_encrypted'],
                'nonce_tag_data': msg.get('nonce_tag_data'), 
                'message_hash': msg.get('message_hash')
            }
            
            decrypted_text, is_valid = ChatManager.decrypt_received_message(
                message_data=message_data,
                current_user_id=self.current_user_id
            )
            
            #  Lấy is_read từ database
            # Chỉ hiển thị đã đọc cho tin nhắn của mình (sender_id == current_user_id)
            is_mine = msg["sender_id"] == self.current_user_id
            is_read = bool(msg.get('is_read', False)) if is_mine else False
            message_id = msg.get('message_id')
            self.display_received_message(msg["sender_id"], decrypted_text, is_valid, msg["sent_at"].isoformat(), is_read=is_read, message_id=message_id)
        
        self.after(200, lambda: self.canvas.yview_moveto(1.0))
    
    def add_recalled_message(self, is_mine, text, time, message_id):
        """Hiển thị tin nhắn đã thu hồi"""
        msg_frame = tk.Frame(self.scrollable_frame, bg="#F9F8F8")
        msg_frame.pack(fill="x", pady=4, padx=10)
        
        if message_id:
            msg_frame.message_id = message_id

        msg_frame.grid_columnconfigure(0, weight=1)
        msg_frame.grid_columnconfigure(1, weight=0)
        msg_frame.grid_columnconfigure(2, weight=1)

        P_X = 10
        MARGIN_SIZE = 80
        
        if is_mine:
            tk.Frame(msg_frame, bg="#F9F8F8", width=MARGIN_SIZE).grid(row=0, column=0, sticky="ew")
            bubble = tk.Frame(msg_frame, bg="#0099FF", padx=12, pady=8)
            bubble.grid(row=0, column=2, sticky="e", padx=(0, P_X))
            
            tk.Label(bubble, text=text, font=("Inter", 11, "italic"),
                    bg="#0099FF", fg="white", wraplength=380, justify="left").pack(fill="x")
            
            tk.Label(msg_frame, text=time, font=("Inter", 8),
                    fg="#888888", bg="#F9F8F8").grid(row=1, column=2, sticky="e", padx=(0, 15))
        else:
            bubble = tk.Frame(msg_frame, bg="#FFFFFF", padx=12, pady=8)
            bubble.grid(row=0, column=0, sticky="w", padx=(P_X, 0))
            
            tk.Label(bubble, text=text, font=("Inter", 11, "italic"),
                    bg="#FFFFFF", fg="#888888", wraplength=380, justify="left").pack(fill="x")
            
            tk.Frame(msg_frame, bg="#F9F8F8", width=MARGIN_SIZE).grid(row=0, column=2, sticky="ew")
            tk.Label(msg_frame, text=time, font=("Inter", 8),
                    fg="#888888", bg="#F9F8F8").grid(row=1, column=0, sticky="w", padx=(15, 0))

    def handle_send_message(self, plain_text):
        """
        Xử lý sự kiện gửi tin nhắn: hiển thị cục bộ (Local Echo) và gửi qua Socket.IO.
        FIX: Bổ sung reset unread count.
        """
        plain_text = plain_text.strip()
        
        if not plain_text:
            return
        
        if not self.sio_client or not self.sio_client.connected:
            messagebox.showerror("Lỗi Mạng", "Kết nối WebSocket chưa sẵn sàng hoặc đã bị ngắt.")
            return

        if not self.conversation_id:
             conv_id = ConversationModel.get_or_create_conversation(self.current_user_id, self.partner_id)
             self.conversation_id = conv_id
             
             if not self.conversation_id:
                  messagebox.showerror("Lỗi Gửi", "Không thể tạo Conversation ID.")
                  return
        
        # 1. LOCAL ECHO
        latest_time_obj = datetime.now()
        time_str = latest_time_obj.strftime("%H:%M")
        self.add_message("me", plain_text, time_str, is_read=False, message_id=None)

        # 2. Xóa nội dung nhập
        self.chat_input.clear()

        # 3. Cập nhật sidebar (FIX: Bổ sung reset unread count)
        if self.chat_manager:
            try:
                 self.chat_manager.update_sidebar_after_send(
                     self.contact_name, 
                     plain_text.strip()[:30] + "...", 
                     latest_time_obj
                 )
                 # Đảm bảo unread count là 0 cho tin nhắn mình gửi
                 self.chat_manager.update_unread_count_in_sidebar(self.contact_name, 0)
            except AttributeError as e:
                 print(f"Lỗi: Không thể cập nhật Sidebar - {e}")
        
        # 4. Join room VÀ gửi tin nhắn
        # Đảm bảo join room TRƯỚC khi gửi để nhận được new_message event
        if not hasattr(self, '_joined_room') or not self._joined_room:
            self.sio_client.emit('join_conversation', {
                'conversation_id': self.conversation_id, 
                'user_id': self.current_user_id
            })
            self._joined_room = True
            print(f" Joined room before sending message")

        self.after(50, lambda: self.sio_client.emit('send_message', {
            'partner_id': self.partner_id,
            'conversation_id': self.conversation_id,
            'plain_text': plain_text
        }))

    # ========================================
    # HIỂN THỊ TIN NHẮN
    # ========================================
    def create_messages_area(self):
        self.canvas = tk.Canvas(self, bg="#F9F8F8", highlightthickness=0)
        self.canvas.grid(row=2, column=0, sticky="nsew")  #  Đổi từ row=1 thành row=2

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
        
        #  Nút Jump to Bottom
        self.jump_btn = tk.Button(
            self,
            text="↓",
            font=("Inter", 16, "bold"),
            bg="#0099FF",
            fg="white",
            relief="flat",
            cursor="hand2",
            width=3,
            height=1,
            command=self.jump_to_latest
        )
        self.jump_btn.place(relx=0.95, rely=0.95, anchor="se")
        self.jump_btn.place_forget()  # Ẩn mặc định
        
        # Theo dõi scroll để hiện/ẩn nút
        self.canvas.bind("<Configure>", self.check_scroll_position)
        self.scrollable_frame.bind("<Configure>", lambda e: self.check_scroll_position(e))
    
    def check_scroll_position(self, event=None):
        """Kiểm tra vị trí scroll để hiện/ẩn nút jump"""
        try:
            # Lấy vị trí scroll hiện tại (0.0 = top, 1.0 = bottom)
            scroll_pos = self.canvas.yview()[1]
            
            # Hiện nút nếu không ở bottom
            if scroll_pos < 0.98:
                self.jump_btn.place(relx=0.95, rely=0.95, anchor="se")
            else:
                self.jump_btn.place_forget()
        except:
            pass
    
    def jump_to_latest(self):
        """Cuộn xuống tin nhắn mới nhất"""
        self.canvas.yview_moveto(1.0)
    
    def create_search_bar(self):
        """Tạo thanh tìm kiếm tin nhắn"""
        self.search_frame = tk.Frame(self, bg="#FFFFFF", height=50)
        self.search_frame.grid(row=1, column=0, sticky="ew")
        self.search_frame.grid_remove()  # Ẩn mặc định
        
        self.search_entry = tk.Entry(self.search_frame, font=("Inter", 11), bg="#F0F0F0", relief="flat")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.search_entry.insert(0, "Tìm kiếm tin nhắn...")
        self.search_entry.bind("<FocusIn>", self.on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self.on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self.on_search_key_release)
        
        # Nút đóng search
        close_btn = tk.Button(self.search_frame, text="✕", font=("Inter", 12), 
                              bg="#FFFFFF", fg="#666", relief="flat", cursor="hand2",
                              command=self.close_search)
        close_btn.pack(side="right", padx=10)
        
        # Navigation buttons
        self.search_result_label = tk.Label(self.search_frame, text="", font=("Inter", 9), 
                                           bg="#FFFFFF", fg="#666")
        self.search_result_label.pack(side="right", padx=5)
        
        self.search_results = []
        self.current_search_index = -1
        
    def toggle_search(self):
        """Bật/tắt search bar"""
        if self.search_frame.winfo_viewable():
            self.close_search()
        else:
            self.search_frame.grid()
            self.search_entry.focus()
            
    def close_search(self):
        """Đóng search bar và clear highlights"""
        self.search_frame.grid_remove()
        self.clear_search_highlights()
        self.search_results = []
        self.current_search_index = -1
        
    def on_search_focus_in(self, event):
        if self.search_entry.get() == "Tìm kiếm tin nhắn...":
            self.search_entry.delete(0, tk.END)
            
    def on_search_focus_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Tìm kiếm tin nhắn...")
            
    def on_search_key_release(self, event):
        """Tìm kiếm khi gõ"""
        query = self.search_entry.get().strip()
        if query and query != "Tìm kiếm tin nhắn...":
            self.search_messages(query)
        else:
            self.clear_search_highlights()
            
    def search_messages(self, query):
        """Tìm và highlight tin nhắn chứa keyword"""
        self.clear_search_highlights()
        self.search_results = []
        
        query_lower = query.lower()
        
        for msg_frame in self.scrollable_frame.winfo_children():
            try:
                # Tìm bubble frame
                for child in msg_frame.winfo_children():
                    if isinstance(child, tk.Frame) and child.cget('bg') in ['#0099FF', '#FFFFFF']:
                        # Tìm text label
                        for label in child.winfo_children():
                            if isinstance(label, tk.Label):
                                text = label.cget('text')
                                if query_lower in text.lower():
                                    # Highlight
                                    original_bg = child.cget('bg')
                                    child.config(bg="#FFEB3B")  # Màu vàng highlight
                                    label.config(bg="#FFEB3B")
                                    self.search_results.append((msg_frame, child, label, original_bg))
            except:
                continue
        
        if self.search_results:
            self.current_search_index = 0
            self.search_result_label.config(text=f"{len(self.search_results)} kết quả")
            # Scroll đến kết quả đầu tiên
            self.search_results[0][0].update_idletasks()
            self.canvas.yview_moveto(self.search_results[0][0].winfo_y() / self.scrollable_frame.winfo_height())
        else:
            self.search_result_label.config(text="Không tìm thấy")
            
    def clear_search_highlights(self):
        """Xóa highlight"""
        for msg_frame, bubble, label, original_bg in self.search_results:
            try:
                bubble.config(bg=original_bg)
                label.config(bg=original_bg)
            except:
                pass
        
    def auto_mark_as_read_if_at_bottom(self):
        """Tự động mark as read nếu user đang ở cuối chat (đang xem tin nhắn)"""
        try:
            scroll_pos = self.canvas.yview()[1]
            # Chỉ mark nếu scroll ở bottom (>95%)
            if scroll_pos > 0.95:
                self.mark_all_as_read()
        except:
            pass
    
    def mark_all_as_read(self):
        """Gửi yêu cầu Socket.IO để đánh dấu tất cả tin nhắn là đã đọc."""
        if self.conversation_id:
            self.sio_client.emit('mark_as_read', {
                'conversation_id': self.conversation_id,
                'user_id': self.current_user_id 
            })
            print(f"Requesting to mark conv {self.conversation_id} as read for user {self.current_user_id}")
            
            # Cập nhật trạng thái unread_count trên sidebar
            if self.chat_manager:
                self.chat_manager.update_unread_count_in_sidebar(
                    contact_name=self.contact_name, 
                    new_count=0
                )
        
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
        #  Tăng tốc độ cuộn và xử lý đúng cả delta > 0 và delta < 0
        if event.delta > 0 or event.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif event.delta < 0 or event.num == 5:
            self.canvas.yview_scroll(3, "units")
        
        #  Kiểm tra vị trí scroll sau khi cuộn
        self.after(50, self.check_scroll_position)
        return "break"

    def update_scrollbar_visibility(self):
        """Cập nhật hiển thị scrollbar"""
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
            
    def add_message(self, sender, text, time, is_read=False, message_id=None):
        """Hiển thị tin nhắn dạng bong bóng với trạng thái đã đọc"""
        msg_frame = tk.Frame(self.scrollable_frame, bg="#F9F8F8")
        msg_frame.pack(fill="x", pady=4, padx=10)
        
        # Lưu message_id vào widget
        if message_id:
            msg_frame.message_id = message_id
        else:
            msg_frame.message_id = None

        msg_frame.grid_columnconfigure(0, weight=1) 
        msg_frame.grid_columnconfigure(1, weight=0) 
        msg_frame.grid_columnconfigure(2, weight=1) 

        P_X = 10
        MARGIN_SIZE = 80 
        
        if sender == "me":
            tk.Frame(msg_frame, bg="#F9F8F8", width=MARGIN_SIZE).grid(row=0, column=0, sticky="ew")

            bubble = tk.Frame(msg_frame, bg="#0099FF", padx=12, pady=8)
            bubble.grid(row=0, column=2, sticky="e", padx=(0, P_X)) 
            
            text_label = tk.Label(bubble, text=text, font=("Inter", 12),
                     bg="#0099FF", fg="white", wraplength=380, justify="left")
            text_label.pack(fill="x")
            
            #  Thêm context menu cho tin nhắn của mình
            # if message_id:
            #     bubble.bind("<Button-3>", lambda e: self.show_message_menu(e, message_id, msg_frame, text, "me"))
            #     text_label.bind("<Button-3>", lambda e: self.show_message_menu(e, message_id, msg_frame, text, "me"))
            
            #  Thêm frame cho time và read status
            time_frame = tk.Frame(msg_frame, bg="#F9F8F8")
            time_frame.grid(row=1, column=2, sticky="e", padx=(0, 15))
            
            # Icon đã đọc/chưa đọc
            read_icon = "✓✓" if is_read else "✓"
            read_color = "#4FC3F7" if is_read else "#888888"
            
            tk.Label(time_frame, text=read_icon, font=("Inter", 9, "bold"),
                     fg=read_color, bg="#F9F8F8").pack(side="left", padx=(0, 3))
            
            tk.Label(time_frame, text=time, font=("Inter", 8),
                     fg="#888888", bg="#F9F8F8").pack(side="left")

        else:
            bubble = tk.Frame(msg_frame, bg="#FFFFFF", padx=12, pady=8)
            bubble.grid(row=0, column=0, sticky="w", padx=(P_X, 0)) 
            
            tk.Label(bubble, text=text, font=("Inter", 12),
                     bg="#FFFFFF", fg="black", wraplength=380, justify="left").pack(fill="x")
                     
            tk.Frame(msg_frame, bg="#F9F8F8", width=MARGIN_SIZE).grid(row=0, column=2, sticky="ew")

            tk.Label(msg_frame, text=time, font=("Inter", 8),
                     fg="#888888", bg="#F9F8F8").grid(row=1, column=0, sticky="w", padx=(15, 0))

        # Update canvas and scroll to bottom
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.after(50, lambda: self.canvas.yview_moveto(1.0))
    
        
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

    def destroy(self):
        """Dọn dẹp và rời khỏi phòng chat"""
        if self.sio_client and self.sio_client.connected and self.conversation_id:
            self.sio_client.emit('leave_conversation', {'conversation_id': self.conversation_id})
            print(f"🚪 Left conversation {self.conversation_id}")
            
        #  KHÔNG XÓA event handlers - ChatScreen mới sẽ đăng ký lại với off() trước
        # Nếu xóa ở đây, tin nhắn vừa gửi sẽ không được nhận
            
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
            self.canvas.unbind("<Configure>")
        except:
            pass
            
        super().destroy()