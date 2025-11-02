import tkinter as tk
from screens.Sidebar import Sidebar
from screens.ChatHome import ChatHome
from screens.ChatScreen import ChatScreen
from screens.EmptyChatScreen import EmptyChatScreen
from backend.Config.UserModel import UserModel
from backend.Config.ConversationModel import ConversationModel
from backend.Config.MessageModel import MessageModel

class Chat(tk.Frame):
    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.configure(bg="white")
        self.controller = controller
        self.current_user = user_data
        self.user_id = user_data['user_id']

        # ==== Load danh sách contacts ====
        self.contacts = self.load_contacts_from_db()
        self.contacts_data = {c["name"]: c for c in self.contacts}

        # ==== Sidebar ====
        user_info = {
            "name": user_data['full_name'],
            "status": "Đang hoạt động"
        }

        # FIX: Truyền controller vào Sidebar
        self.sidebar = Sidebar(
            self,
            controller=controller,  # <-- THÊM DÒNG NÀY
            user_info=user_info,
            contacts=self.contacts,
            on_contact_click=self.open_chat
        )
        self.sidebar.pack(side="left", fill="y")

        # ==== Content Frame ====
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(side="left", fill="both", expand=True)

        # ==== Hiển thị ChatHome ban đầu ====
        self.current_view = None
        self.show_chat_home()

    def load_contacts_from_db(self):
        try:
            all_users = UserModel.get_all_users_except(self.user_id)
            contacts = []
            for user in all_users:
                conv = ConversationModel.get_conversation_between_users(self.user_id, user['user_id'])
                latest_msg = MessageModel.get_latest_message_between_users(self.user_id, user['user_id']) if conv else None

                contacts.append({
                    "name": user['full_name'],
                    "partner_id": user['user_id'],
                    "conversation_id": conv['conversation_id'] if conv else None,
                    "message": latest_msg['message_encrypted'][:30] + "..." if latest_msg else "Chưa có tin nhắn",
                    "has_messages": latest_msg is not None,
                    "is_online": user.get('is_online', False)
                })
            return contacts
        except Exception as e:
            print(f"DB Error: {e}")
            return self.get_mock_contacts()

    def get_mock_contacts(self):
        return [
            {"name": "Lan", "message": "Chào bạn", "has_messages": True, "partner_id": 2, "conversation_id": 1, "is_online": True},
            {"name": "Minh", "message": "Chưa có tin nhắn", "has_messages": False, "partner_id": 3, "conversation_id": None, "is_online": False},
        ]

    def show_chat_home(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = ChatHome(self.content_frame)
        self.current_view.pack(fill="both", expand=True)
        self.current_contact = None

    def open_chat(self, contact_name, avatar_icon):
        """Mở chat với contact"""
        self.current_contact = contact_name
        contact = self.contacts_data.get(contact_name, {})
        has_messages = contact.get("has_messages", False)

        if self.current_view:
            self.current_view.destroy()

        current_user_id = self.current_user['user_id']
        partner_id = contact.get("partner_id")

        if has_messages:
            self.current_view = ChatScreen(
                self.content_frame,
                contact_name,
                avatar_icon,
                current_user_id=current_user_id,
                partner_id=partner_id
            )
        else:
            self.current_view = EmptyChatScreen(
                self.content_frame,
                contact_name,
                avatar_icon,
                current_user_id=current_user_id,
                partner_id=partner_id,
                on_first_message=self.handle_first_message
            )
        
        self.current_view.pack(fill="both", expand=True)

    def handle_first_message(self, contact_name, message_text):
        """Xử lý khi gửi tin nhắn đầu tiên - chuyển sang ChatScreen"""
        contact = self.contacts_data[contact_name]
        contact["has_messages"] = True

        conv = ConversationModel.get_conversation_between_users(
            self.user_id, 
            contact["partner_id"]
        )
        if conv:
            contact["conversation_id"] = conv["conversation_id"]

        if self.current_view:
            self.current_view.destroy()

        avatar_icon = self.sidebar.get_avatar_for_contact(contact_name)
        current_user_id = self.current_user['user_id']
        partner_id = contact.get("partner_id")

        self.current_view = ChatScreen(
            self.content_frame,
            contact_name,
            avatar_icon,
            current_user_id=current_user_id,
            partner_id=partner_id
        )
        self.current_view.pack(fill="both", expand=True)