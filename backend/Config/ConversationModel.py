# backend/Config/ConversationModel.py

from backend.Config.ConnectDB import connect_to_database
from datetime import datetime


class ConversationModel:
    @staticmethod
    def get_or_create_conversation(user1_id, user2_id):
        """
        Lấy conversation ID giữa 2 users, nếu chưa có thì tạo mới (phù hợp với CSDL mới).
        """
        try:
            conn, cursor = connect_to_database()
            
            # Đảm bảo user1_id < user2_id để duy trì UNIQUE KEY
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id

            # 1. TÌM KIẾM
            query = """
                SELECT conversation_id, user1_id, user2_id FROM conversations 
                WHERE user1_id = %s AND user2_id = %s
            """
            cursor.execute(query, (user1_id, user2_id))
            result = cursor.fetchone()

            if result:
                conversation_id = result['conversation_id']
            else:
                # 2. TẠO MỚI (KHÔNG CÒN AES KEY VÀ IV)
                insert_query = """
                    INSERT INTO conversations (user1_id, user2_id, created_at)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (
                    user1_id, user2_id, datetime.now()
                ))
                conn.commit()
                conversation_id = cursor.lastrowid

            cursor.close()
            conn.close()
            return conversation_id
        except Exception as e:
            print(f"Error get_or_create_conversation: {e}")
            return None

    @staticmethod
    def create_conversation(user1_id, user2_id):
        """Tạo conversation mới giữa 2 người dùng."""
        try:
            # Hạn chế dùng hàm này, nên dùng get_or_create_conversation
            conversation_id = ConversationModel.get_or_create_conversation(user1_id, user2_id)
            if conversation_id:
                 return {"conversation_id": conversation_id}
            return None
        except Exception as e:
            print(f"Error create_conversation: {e}")
            return None

    @staticmethod
    def get_conversation_between_users(user1_id, user2_id):
        """Lấy thông tin conversation dựa trên 2 user ID."""
        try:
            conn, cursor = connect_to_database()
            
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id
                
            query = """
                SELECT * FROM conversations 
                WHERE user1_id = %s AND user2_id = %s
            """
            cursor.execute(query, (user1_id, user2_id))
            conversation = cursor.fetchone()
            cursor.close()
            conn.close()
            return conversation
        except Exception as e:
            print(f"Error get_conversation_between_users: {e}")
            return None

    @staticmethod
    def get_conversation_by_id(conversation_id):
        """Lấy thông tin conversation theo ID."""
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT * FROM conversations 
                WHERE conversation_id = %s
            """
            cursor.execute(query, (conversation_id,))
            conversation = cursor.fetchone()
            cursor.close()
            conn.close()
            return conversation
        except Exception as e:
            print(f"Error get_conversation_by_id: {e}")
            return None

    @staticmethod
    def get_conversations_by_user(user_id):
        """Lấy danh sách conversations của user (logic không đổi)."""
        # ... (giữ nguyên logic SELECT)
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT 
                    c.*,
                    CASE WHEN c.user1_id = %s THEN u2.full_name ELSE u1.full_name END as partner_name,
                    CASE WHEN c.user1_id = %s THEN u2.is_online ELSE u1.is_online END as partner_online,
                    
                    -- BỔ SUNG: Lấy tin nhắn cuối cùng (LAST_MESSAGE)
                    m.message_encrypted AS last_message_content,
                    m.sent_at AS last_message_time
                    
                FROM conversations c
                JOIN users u1 ON c.user1_id = u1.user_id
                JOIN users u2 ON c.user2_id = u2.user_id
                
                -- LEFT JOIN: Lấy tin nhắn cuối cùng cho từng conversation
                LEFT JOIN messages m ON m.message_id = (
                    SELECT message_id FROM messages 
                    WHERE conversation_id = c.conversation_id 
                    ORDER BY sent_at DESC LIMIT 1
                )
                
                WHERE c.user1_id = %s OR c.user2_id = %s
                -- SẮP XẾP theo thời gian tin nhắn cuối
                ORDER BY m.sent_at DESC, c.created_at DESC
            """
            cursor.execute(query, (user_id, user_id, user_id, user_id))
            conversations = cursor.fetchall()
            cursor.close()
            conn.close()
            return conversations
        except Exception as e:
            print(f"Error get_conversations_by_user: {e}")
            return []