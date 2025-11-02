from backend.Config.ConnectDB import connect_to_database
from backend.Config.ConversationModel import ConversationModel
from datetime import datetime


class MessageModel:
    @staticmethod
    def get_messages_by_conversation(conversation_id, limit=100):
        """
        Lấy toàn bộ tin nhắn theo conversation_id (theo thứ tự thời gian tăng dần)
        """
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT m.message_id, m.sender_id, m.receiver_id, m.message_encrypted, 
                       m.message_hash, m.sent_at, u.full_name AS sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.user_id
                WHERE m.conversation_id = %s
                ORDER BY m.sent_at ASC
                LIMIT %s
            """
            cursor.execute(query, (conversation_id, limit))
            messages = cursor.fetchall()
            cursor.close()
            conn.close()
            return messages
        except Exception as e:
            print(f"[ERROR] get_messages_by_conversation: {e}")
            return []

    @staticmethod
    def create_message(conversation_id, sender_id, receiver_id, message_encrypted, message_hash=""):
        """
        Tạo một tin nhắn mới trong cuộc hội thoại
        """
        try:
            conn, cursor = connect_to_database()
            query = """
                INSERT INTO messages 
                (conversation_id, sender_id, receiver_id, message_encrypted, message_hash, sent_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                conversation_id,
                sender_id,
                receiver_id,
                message_encrypted,
                message_hash or "TEMP_HASH",
                datetime.now()
            ))
            conn.commit()
            message_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return True, message_id
        except Exception as e:
            print(f"[ERROR] create_message: {e}")
            return False, None

    @staticmethod
    def get_latest_message_by_conversation(conversation_id):
        """
        Lấy tin nhắn mới nhất trong một cuộc hội thoại
        """
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT * FROM messages 
                WHERE conversation_id = %s 
                ORDER BY sent_at DESC LIMIT 1
            """
            cursor.execute(query, (conversation_id,))
            message = cursor.fetchone()
            cursor.close()
            conn.close()
            return message
        except Exception as e:
            print(f"[ERROR] get_latest_message_by_conversation: {e}")
            return None

    @staticmethod
    def get_latest_message_between_users(user1_id, user2_id):
        """
        Lấy tin nhắn mới nhất giữa 2 người (dựa vào ConversationModel)
        """
        try:
            conversation = ConversationModel.get_conversation_between_users(user1_id, user2_id)
            if not conversation:
                return None
            return MessageModel.get_latest_message_by_conversation(conversation['conversation_id'])
        except Exception as e:
            print(f"[ERROR] get_latest_message_between_users: {e}")
            return None
