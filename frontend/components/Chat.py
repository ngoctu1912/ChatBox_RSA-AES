import tkinter as tk
from screens.Sidebar import Sidebar
from screens.ChatHome import ChatHome
from screens.ChatScreen import ChatScreen
from screens.EmptyChatScreen import EmptyChatScreen
from backend.Config.UserModel import UserModel
from backend.Config.ConversationModel import ConversationModel
from backend.Config.MessageModel import MessageModel
from backend.Core.ChatManager import ChatManager
from datetime import datetime
import socketio


class Chat(tk.Frame):
    def __init__(self, parent, controller, user_data, sio_client):
        super().__init__(parent)
        self.configure(bg="white")
        self.controller = controller
        self.current_user = user_data
        self.user_id = user_data['user_id']
        self.sio_client = sio_client 

        # ==== Load danh sách contacts ====
        self.contacts = self.load_contacts_from_db()
        self.contacts_data = {c["name"]: c for c in self.contacts}

        # ==== Sidebar ====
        user_info = {
            "name": user_data['full_name'],
            "status": "Đang hoạt động",
            "username": user_data.get('username', ''),
            "email": user_data.get('email', '')
        }

        self.sidebar = Sidebar(
            self,
            controller=controller,
            user_info=user_info,
            contacts=self.contacts,
            on_contact_click=self.open_chat,
            sio_client=self.sio_client,  #  Truyền socket client
            user_id=self.user_id  #  Truyền user_id
        )
        self.sidebar.pack(side="left", fill="y")

        # ==== Content Frame ====
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(side="left", fill="both", expand=True)

        # ==== Hiển thị ChatHome ban đầu ====
        self.current_view = ChatHome(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        
        # ====  ĐĂNG KÝ WEBSOCKET EVENTS TOÀN CỤC ====
        if self.sio_client and self.sio_client.connected:
            self.register_global_events()


    def load_contacts_from_db(self):
        """Tải danh sách contacts (Sắp xếp theo thời gian mới nhất)"""
        try:
            all_users = UserModel.get_all_users_except(self.user_id) 
            contacts = []
            
            for user in all_users:
                partner_id = user['user_id']
                conv = ConversationModel.get_conversation_between_users(self.user_id, partner_id)
                conversation_id = conv['conversation_id'] if conv else None
                
                latest_msg = None
                unread_count = 0
                
                if conversation_id:
                     latest_msg = MessageModel.get_latest_message_by_conversation(conversation_id)
                     unread_count = MessageModel.get_unread_count(conversation_id, self.user_id)

                message_preview = "Chưa có tin nhắn"
                latest_time = datetime.min

                if latest_msg:
                    message_data_for_decrypt = {
                        'conversation_id': conversation_id,
                        'message_encrypted': latest_msg['message_encrypted'],
                        'nonce_tag_data': latest_msg.get('nonce_tag_data'),
                        'message_hash': latest_msg.get('message_hash')
                    }
                    
                    decrypted_text, is_valid = ChatManager.decrypt_received_message(message_data_for_decrypt, self.user_id)
                    
                    if is_valid:
                         message_preview = decrypted_text[:30] + "..."
                    else:
                         message_preview = "..." + latest_msg['message_encrypted'][:15]
                         
                    latest_time = latest_msg['sent_at']


                contacts.append({
                    "name": user['full_name'],
                    "partner_id": partner_id,
                    "conversation_id": conversation_id,
                    "message": message_preview,
                    "has_messages": latest_msg is not None,
                    "is_online": user.get('is_online', False),
                    "unread_count": unread_count,
                    "latest_message_time": latest_time
                })
            
            contacts.sort(key=lambda x: x['latest_message_time'], reverse=True) 
            return contacts
        except Exception as e:
            print(f"DB Error in load_contacts_from_db: {e}")
            return []
    
    # ==========================================
    #  ĐĂNG KÝ WEBSOCKET EVENTS TOÀN CỤC
    # ==========================================
    def register_global_events(self):
        """Đăng ký các sự kiện WebSocket toàn cục (không phụ thuộc vào màn hình đang mở)"""
        
        # 1. Lắng nghe trạng thái online/offline
        self.sio_client.on('user_online', self.on_user_status_changed)
        self.sio_client.on('user_offline', self.on_user_status_changed)
        
        # 2. XÓA EVENT CŨ VÀ ĐĂNG KÝ MỚI - Lắng nghe tin nhắn mới từ BẤT KỲ conversation nào
        try:
            self.sio_client.off('new_message')
        except:
            pass
        self.sio_client.on('new_message', self.on_global_new_message)
        
        # 3. LẮng nghe pending messages được xử lý
        self.sio_client.on('pending_message_processed', self.on_pending_processed)
        
        # 4. Lắng nghe thông báo pending messages
        self.sio_client.on('pending_messages_notification', self.on_pending_notification)
        
        # 5. Lắng nghe phản hồi trạng thái online ban đầu
        self.sio_client.on('online_status_response', self.on_initial_online_status)
        
        print(" Global WebSocket events registered")
        
        #  JOIN TẤT CẢ CONVERSATION ROOMS
        self.after(100, self.join_all_conversations)
        
        #  TẢI LẠI TRẠNG THÁI ONLINE TỪ DATABASE
        self.after(200, self.refresh_online_status_from_db)
    
    def join_all_conversations(self):
        """Join tất cả conversation rooms để nhận tin nhắn real-time"""
        try:
            for contact in self.contacts:
                conv_id = contact.get('conversation_id')
                if conv_id:
                    self.sio_client.emit('join_conversation', {
                        'conversation_id': conv_id,
                        'user_id': self.user_id
                    })
            print(f"🔗 [Chat] Joined {len(self.contacts)} conversation rooms")
        except Exception as e:
            print(f"❌ [Chat] Error joining conversations: {e}")
    
    def refresh_online_status_from_db(self):
        """Tải lại trạng thái online từ database"""
        try:
            print(f" [Chat] Refreshing online status from database...")
            
            # Reload contacts để lấy is_online mới nhất từ DB
            updated_contacts = self.load_contacts_from_db()
            
            # Cập nhật trạng thái cho contacts hiện tại
            for updated_contact in updated_contacts:
                partner_id = updated_contact.get('partner_id')
                is_online = updated_contact.get('is_online', False)
                
                # Tìm contact tương ứng trong danh sách hiện tại
                for contact in self.contacts:
                    if contact.get('partner_id') == partner_id:
                        old_status = contact.get('is_online', False)
                        contact['is_online'] = is_online
                        
                        if old_status != is_online:
                            print(f"✏️  [Chat] Updated {contact['name']}: {old_status} → {is_online}")
                            # Cập nhật UI
                            self.sidebar.update_contact_status(contact['name'], is_online)
                        break
            
            print(f" [Chat] Online status refreshed from database")
            
        except Exception as e:
            print(f" [Chat] Error refreshing online status: {e}")
    
    def request_initial_online_status(self):
        """Yêu cầu trạng thái online của tất cả users khi vào trang Chat (DEPRECATED - dùng DB thay thế)"""
        # Không còn cần thiết vì đã load trực tiếp từ DB
        pass
    
    def on_initial_online_status(self, data):
        """Xử lý phản hồi trạng thái online ban đầu"""
        online_status = data.get('online_status', {})
        
        print(f"📬 Received initial online status: {online_status}")
        
        # Cập nhật trạng thái cho từng contact
        for contact in self.contacts:
            partner_id = contact.get('partner_id')
            if partner_id in online_status:
                is_online = online_status[partner_id]
                contact['is_online'] = is_online
                
                #  Cập nhật UI CHỈ cho contact đó, không reload toàn bộ
                self.sidebar.update_contact_status(contact['name'], is_online)
        
        #  KHÔNG GỌI display_contacts() - tránh destroy ChatScreen
        print(" [Chat] Online status updated without reload")
    
    def on_user_status_changed(self, data):
        """Xử lý khi có user thay đổi trạng thái online/offline"""
        print(f" [Chat] Received user status event: {data}")
        
        user_id = data.get('user_id')
        is_online = data.get('is_online')
        
        # Xác định trạng thái từ data hoặc event name
        if is_online is None:
            # Fallback: nếu không có is_online, không xử lý
            print(f"  [Chat] Missing is_online field in event data")
            return
        
        print(f" [Chat] Looking for user_id={user_id}, is_online={is_online}")
        
        found = False
        for contact in self.contacts:
            if contact.get('partner_id') == user_id:
                found = True
                old_status = contact.get('is_online', False)
                contact['is_online'] = is_online
                
                print(f"  [Chat] Updating {contact['name']}: {old_status} → {is_online}")
                
                # Cập nhật Sidebar
                self.sidebar.update_contact_status(contact['name'], is_online)
                
                #  CẬP NHẬT CHATHEADER NẾU ĐANG MỞ CHAT VỚI USER ĐÓ
                if (hasattr(self, 'current_view') and 
                    hasattr(self.current_view, 'partner_id') and 
                    self.current_view.partner_id == user_id and
                    hasattr(self.current_view, 'header')):
                    print(f" [Chat] Updating ChatHeader for {contact['name']}")
                    self.current_view.header.update_online_status(is_online)
                
                print(f"{'🟢' if is_online else '⚪'} [Chat] User {contact['name']} is now {'online' if is_online else 'offline'}")
                break
        
        if not found:
            print(f" [Chat] User ID {user_id} not found in contacts")
    
    def on_pending_notification(self, data):
        """
        XỬ LÝ THÔNG BÁO PENDING MESSAGES KHI VỪA ĐĂNG NHẬP
        """
        count = data.get('count', 0)
        message = data.get('message', '')
        
        if count > 0:
            print(f" You have {count} pending message(s)")
    
    def on_pending_processed(self, data):
        """
        XỬ LÝ KHI PENDING MESSAGES ĐƯỢC GỬI THÀNH CÔNG (Của user hiện tại)
        """
        updates = data.get('updates', [])
        
        for update in updates:
            conversation_id = update['conversation_id']
            # message_id = update['message_id']
            
            # TÌM CONTACT TƯƠNG ỨNG VÀ CẬP NHẬT SIDEBAR
            for contact in self.contacts:
                if contact.get('conversation_id') == conversation_id:
                    # Tải lại tin nhắn mới nhất từ DB để cập nhật preview chính xác
                    try:
                        latest_msg = MessageModel.get_latest_message_by_conversation(conversation_id)
                        
                        if latest_msg:
                            message_data_for_decrypt = {
                                'conversation_id': conversation_id,
                                'message_encrypted': latest_msg['message_encrypted'],
                                'nonce_tag_data': latest_msg.get('nonce_tag_data'),
                                'message_hash': latest_msg.get('message_hash')
                            }
                            
                            decrypted_text, is_valid = ChatManager.decrypt_received_message(
                                message_data_for_decrypt, 
                                self.user_id
                            )
                            
                            preview = decrypted_text[:30] + "..." if is_valid else "..."
                            
                            # Cập nhật sidebar với tin nhắn mới (sẽ tự sắp xếp)
                            self.update_sidebar_after_send(
                                contact['name'],
                                preview,
                                latest_msg['sent_at']
                            )
                            
                            print(f" Updated sidebar for {contact['name']} after pending processed")
                    
                    except Exception as e:
                        print(f"Error updating sidebar after pending: {e}")
                    
                    break
    
    def on_global_new_message(self, data):
        """
        Xử lý khi có tin nhắn mới đến (bất kỳ conversation nào).
        """
        print(f"🔔🔔🔔 [Chat] on_global_new_message TRIGGERED! conv={data.get('conversation_id')}, sender={data.get('sender_id')}, my_id={self.user_id}")
        
        conversation_id = data.get('conversation_id')
        sender_id = data.get('sender_id')
        
        if sender_id == self.user_id:
            print(f"⏭️ [Chat] Skip - message from myself")
            return
        
        contact = None
        for c in self.contacts:
            if c.get('conversation_id') == conversation_id:
                contact = c
                break
        
        if not contact:
            # Reload lại contacts để lấy conversation mới (nếu tin nhắn đầu tiên)
            self.contacts = self.load_contacts_from_db()
            self.contacts_data = {c["name"]: c for c in self.contacts}
            self.sidebar.display_contacts(self.contacts)
            
            for c in self.contacts:
                if c.get('conversation_id') == conversation_id:
                    contact = c
                    break
            
            if not contact:
                return
        
        # Giải mã tin nhắn
        try:
            plain_text, is_valid = ChatManager.decrypt_received_message(data, self.user_id)
            
            if not is_valid or plain_text.startswith('[ERROR'):
                print(f"❌ [Chat] Decryption failed for message")
                return
                
            latest_time_obj = datetime.fromisoformat(data.get('sent_at'))
            
            # 1. Cập nhật dữ liệu contact
            contact['message'] = plain_text.strip()[:30] + "..."
            contact['latest_message_time'] = latest_time_obj
            
            # 2. Kiểm tra xem có đang chat với người này không
            is_current_chat = (
                hasattr(self, 'current_view') and 
                hasattr(self.current_view, 'conversation_id') and
                self.current_view.conversation_id == conversation_id
            )
            
            if is_current_chat:
                # Đang chat với người này
                contact['unread_count'] = 0
                print(f"✅ [Chat] Message from {contact['name']} (current chat) - updating chat window")
                
                # CẬP NHẬT CHAT WINDOW
                if hasattr(self.current_view, 'on_new_message'):
                    self.current_view.on_new_message(data)
            else:
                # Không đang chat - tăng unread
                current_unread = contact.get('unread_count', 0)
                new_unread = current_unread + 1
                contact['unread_count'] = new_unread
                print(f"✅ [Chat] New message from {contact['name']} (unread: {new_unread})")
            
            # 3. Sort lại
            self.contacts.sort(key=lambda x: x.get('latest_message_time', datetime.min), reverse=True)
            
            # 4. CẬP NHẬT UI SIDEBAR - LUÔN LUÔN CẬP NHẬT
            self.sidebar.update_single_contact(
                contact['name'],
                plain_text.strip()[:30] + "...",
                latest_time_obj
            )
            
            print(f"✅ [Chat] Sidebar updated for {contact['name']}")
                
        except Exception as e:
            print(f"❌ [Chat] Error processing global new message: {e}")
            import traceback
            traceback.print_exc()

    
    def update_sidebar_after_send(self, contact_name, message_preview, latest_time):
        """
        Cập nhật dữ liệu Sidebar (self.contacts) sau khi tin nhắn mới được gửi 
        (Cả mình và người khác gửi, CHỈ CẬP NHẬT NỘI DUNG VÀ SORT).
        """
        contact = self.contacts_data.get(contact_name)
        if contact:
            # 1. Cập nhật dữ liệu (in-memory)
            contact["message"] = message_preview
            contact["latest_message_time"] = latest_time
            contact["has_messages"] = True
            
            # 2. Sắp xếp lại danh bạ
            self.contacts.sort(key=lambda x: x['latest_message_time'], reverse=True)
            
            # 3.  CHỈ CẬP NHẬT contact item thay vì reload toàn bộ
            # Tránh destroy ChatScreen đang active
            self.sidebar.update_single_contact(contact_name, message_preview, latest_time)

    def update_unread_count_in_sidebar(self, contact_name, new_count):
        """
        Cập nhật số lượng tin nhắn chưa đọc cho một contact cụ thể trên sidebar.
        """
        contact = self.contacts_data.get(contact_name)
        if contact:
            contact["unread_count"] = new_count
            self.sidebar.update_contact_unread_count(
                contact_name=contact_name, 
                new_count=new_count
            )
            
    def open_chat(self, contact_name, avatar_icon):
        """Mở màn hình chat (ChatScreen hoặc EmptyChatScreen)"""
        contact = self.contacts_data.get(contact_name, {})
        
        current_user_id = self.current_user['user_id']
        partner_id = contact.get("partner_id")
        conversation_id = contact.get("conversation_id")
        partner_is_online = contact.get("is_online", False)  #  LẤY TRẠNG THÁI ONLINE
        
        if self.current_view:
            self.current_view.destroy()

        sio_client = self.sio_client
        has_messages = contact.get("has_messages", False)
        
        if has_messages:
            self.current_view = ChatScreen(
                self.content_frame,
                controller=self.controller,
                sio_client=sio_client,
                contact_name=contact_name,
                avatar_icon=avatar_icon,
                current_user_id=current_user_id,
                partner_id=partner_id,
                conversation_id=conversation_id,
                chat_manager=self,
                partner_is_online=partner_is_online  #  TRUYỀN TRẠNG THÁI
            )
        else:
            self.current_view = EmptyChatScreen(
                self.content_frame,
                controller=self.controller,
                sio_client=sio_client,
                contact_name=contact_name,
                avatar_icon=avatar_icon,
                current_user_id=current_user_id,
                partner_id=partner_id,
                on_first_message=self.handle_first_message,
                conversation_id=conversation_id,
                chat_manager=self,
                partner_is_online=partner_is_online  #  TRUYỀN TRẠNG THÁI
            )
        
        self.current_view.pack(fill="both", expand=True)

    
    
    def handle_first_message(self, contact_name, message_data):
        """Xử lý khi gửi tin nhắn đầu tiên - chuyển sang ChatScreen (An toàn TclError)"""
        contact = self.contacts_data[contact_name]
        contact["has_messages"] = True
        contact["conversation_id"] = message_data.get('conversation_id') 

        if self.current_view:
            self.current_view.destroy()
            
        def switch_to_chat_screen():
            avatar_icon = self.sidebar.get_avatar_for_contact(contact_name)
            current_user_id = self.current_user['user_id']
            partner_id = contact.get("partner_id")
            conversation_id = contact.get("conversation_id")
            partner_is_online = contact.get("is_online", False)  #  LẤY TRẠNG THÁI
            sio_client = self.sio_client

            self.current_view = ChatScreen(
                self.content_frame,
                controller=self.controller,
                sio_client=sio_client,
                contact_name=contact_name,
                avatar_icon=avatar_icon,
                current_user_id=current_user_id,
                partner_id=partner_id,
                conversation_id=conversation_id,
                chat_manager=self,
                partner_is_online=partner_is_online,  #  TRUYỀN TRẠNG THÁI
                first_message_data=message_data # <-- BỔ SUNG TRUYỀN DỮ LIỆU GỐC
            )
            self.current_view.pack(fill="both", expand=True)

        self.after(1, switch_to_chat_screen)
    
    def destroy(self):
        """Dọn dẹp khi đóng Chat frame"""
        if self.sio_client:
            try:
                self.sio_client.off('user_online')
                self.sio_client.off('user_offline')
                self.sio_client.off('new_message')
                self.sio_client.off('pending_message_processed')
                self.sio_client.off('pending_messages_notification')
                print(" Global WebSocket events unregistered")
            except:
                pass
        
        super().destroy()
        
