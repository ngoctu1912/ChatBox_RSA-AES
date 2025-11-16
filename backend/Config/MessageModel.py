from backend.Config.ConnectDB import connect_to_database
from backend.Config.ConversationModel import ConversationModel
from datetime import datetime


class MessageModel:
    @staticmethod
    def create_message(conversation_id, sender_id, receiver_id, message_encrypted, nonce, tag, hmac_value, aes_key_encrypted=None):
        """
        Tạo tin nhắn mới trong CSDL (Logic SQL đã FIX).
        """
        conn = None
        message_id = None
        
        try:
            conn, cursor = connect_to_database()
            
            aes_key_encrypted_sql = aes_key_encrypted if aes_key_encrypted else None 
            nonce_tag_data_value = f"{nonce}:{tag}"

            # 1. INSERT Tin nhắn
            query_insert = """
                INSERT INTO messages 
                (conversation_id, sender_id, receiver_id, message_encrypted, nonce_tag_data, message_hash, aes_key_encrypted, sent_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query_insert, (
                conversation_id, sender_id, receiver_id, message_encrypted, 
                nonce_tag_data_value, hmac_value, aes_key_encrypted_sql, datetime.now()
            ))
            
            # 2. LẤY ID VỪA ĐƯỢC CHÈN
            cursor.execute("SELECT LAST_INSERT_ID() AS message_id")
            result = cursor.fetchone()
            
            if result and 'message_id' in result:
                message_id = result['message_id']
            else:
                raise Exception("Không thể lấy ID tin nhắn vừa được chèn.")
            
            # 3. Tạo message_status (Chỉ cho người nhận)
            query_status = """
                INSERT INTO message_status (message_id, user_id, is_read)
                VALUES (%s, %s, FALSE)
            """
            cursor.execute(query_status, (message_id, receiver_id))
            
            conn.commit()
            
            return True, message_id

        except Exception as e:
            print(f"Lỗi khi tạo tin nhắn: {e}")
            if conn: conn.rollback()
            return False, f"Lỗi: {str(e)}"
        finally:
            if conn: conn.close()
            
    @staticmethod
    def get_messages_by_conversation(conversation_id, limit=100, current_user_id=None):
        """
        Lấy toàn bộ tin nhắn theo conversation_id (theo thứ tự thời gian tăng dần), 
        bao gồm nonce_tag_data, message_hash và is_read.
        is_read = TRUE khi receiver đã đọc tin nhắn
        """
        try:
            conn, cursor = connect_to_database()
            
            # Lấy is_read từ message_status của receiver (không phụ thuộc current_user)
            query = """
                SELECT m.message_id, m.sender_id, m.receiver_id, m.message_encrypted, 
                       m.nonce_tag_data, m.message_hash, m.sent_at, u.full_name AS sender_name,
                       COALESCE(ms.is_read, FALSE) as is_read
                FROM messages m
                JOIN users u ON m.sender_id = u.user_id
                LEFT JOIN message_status ms ON m.message_id = ms.message_id 
                    AND ms.user_id = m.receiver_id
                WHERE m.conversation_id = %s
                ORDER BY m.sent_at ASC, m.message_id ASC
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
        
    @staticmethod
    def get_unread_count(conversation_id, user_id):
        """Đếm số lượng tin nhắn chưa đọc cho user_id"""
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT COUNT(m.message_id) 
                FROM messages m
                JOIN message_status ms ON m.message_id = ms.message_id
                WHERE m.conversation_id = %s
                AND ms.user_id = %s
                AND ms.is_read = FALSE
                AND m.sender_id != %s  -- Không tính tin nhắn của chính mình
            """
            cursor.execute(query, (conversation_id, user_id, user_id))
            count = cursor.fetchone()
            cursor.close()
            conn.close()
            return count['COUNT(m.message_id)'] if count else 0
        except Exception as e:
            print(f"[ERROR] get_unread_count: {e}")
            return 0
    
    @staticmethod
    def mark_conversation_as_read(conversation_id, user_id):
        """Đánh dấu tất cả tin nhắn nhận trong conversation là đã đọc."""
        try:
            conn, cursor = connect_to_database()
            query = """
                UPDATE message_status ms
                JOIN messages m ON ms.message_id = m.message_id
                SET ms.is_read = TRUE, ms.read_at = NOW()
                WHERE ms.user_id = %s
                AND m.conversation_id = %s
                AND m.sender_id != %s  -- Chỉ đánh dấu tin nhắn của người khác là đã đọc
            """
            cursor.execute(query, (user_id, conversation_id, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"[ERROR] mark_conversation_as_read: {e}")
            return False
    
    @staticmethod
    def delete_message(message_id):
        """Xóa tin nhắn khỏi database"""
        try:
            conn, cursor = connect_to_database()
            
            # Xóa message_status trước
            cursor.execute("DELETE FROM message_status WHERE message_id = %s", (message_id,))
            
            # Xóa message
            cursor.execute("DELETE FROM messages WHERE message_id = %s", (message_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"[ERROR] delete_message: {e}")
            return False
    
    @staticmethod
    def mark_message_as_recalled(message_id):
        """Đánh dấu tin nhắn là đã thu hồi (thay vì xóa)"""
        try:
            conn, cursor = connect_to_database()
            
            # Cập nhật nội dung thành "[RECALLED]"
            cursor.execute(
                "UPDATE messages SET message_encrypted = '[RECALLED]' WHERE message_id = %s",
                (message_id,)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"[ERROR] mark_message_as_recalled: {e}")
            return False
