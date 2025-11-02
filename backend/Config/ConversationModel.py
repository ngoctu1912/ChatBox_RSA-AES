from backend.Config.ConnectDB import connect_to_database
from datetime import datetime


class ConversationModel:
    @staticmethod
    def get_or_create_conversation(user1_id, user2_id, aes_key_encrypted="", iv=""):
        try:
            conn, cursor = connect_to_database()
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id

            query = """
                SELECT conversation_id FROM conversations 
                WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)
            """
            cursor.execute(query, (user1_id, user2_id, user2_id, user1_id))
            result = cursor.fetchone()

            if result:
                conversation_id = result['conversation_id']
            else:
                insert_query = """
                    INSERT INTO conversations (user1_id, user2_id, aes_key_encrypted, iv, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    user1_id, user2_id,
                    aes_key_encrypted or "TEMP_AES_KEY",
                    iv or "TEMP_IV",
                    datetime.now()
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
    def create_conversation(user1_id, user2_id, aes_key_encrypted="", iv=""):
        """
        Tạo conversation mới giữa 2 người dùng
        Returns: dict với conversation_id
        """
        try:
            conn, cursor = connect_to_database()
            
            # Đảm bảo user1_id < user2_id
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id
            
            insert_query = """
                INSERT INTO conversations (user1_id, user2_id, aes_key_encrypted, iv, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                user1_id, user2_id,
                aes_key_encrypted or "TEMP_AES_KEY",
                iv or "TEMP_IV",
                datetime.now()
            ))
            conn.commit()
            conversation_id = cursor.lastrowid
            cursor.close()
            conn.close()
            
            return {"conversation_id": conversation_id}
        except Exception as e:
            print(f"Error create_conversation: {e}")
            return None

    @staticmethod
    def get_conversation_between_users(user1_id, user2_id):
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT * FROM conversations 
                WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)
            """
            cursor.execute(query, (user1_id, user2_id, user2_id, user1_id))
            conversation = cursor.fetchone()
            cursor.close()
            conn.close()
            return conversation
        except Exception as e:
            print(f"Error get_conversation_between_users: {e}")
            return None

    @staticmethod
    def get_conversations_by_user(user_id):
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT 
                    c.*,
                    CASE WHEN c.user1_id = %s THEN u2.user_id ELSE u1.user_id END as partner_id,
                    CASE WHEN c.user1_id = %s THEN u2.full_name ELSE u1.full_name END as partner_name,
                    CASE WHEN c.user1_id = %s THEN u2.is_online ELSE u1.is_online END as partner_online
                FROM conversations c
                JOIN users u1 ON c.user1_id = u1.user_id
                JOIN users u2 ON c.user2_id = u2.user_id
                WHERE c.user1_id = %s OR c.user2_id = %s
                ORDER BY c.created_at DESC
            """
            cursor.execute(query, (user_id, user_id, user_id, user_id, user_id))
            conversations = cursor.fetchall()
            cursor.close()
            conn.close()
            return conversations
        except Exception as e:
            print(f"Error get_conversations_by_user: {e}")
            return []