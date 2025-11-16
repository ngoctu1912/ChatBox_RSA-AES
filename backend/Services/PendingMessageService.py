# backend/Services/PendingMessageService.py
# FINAL VERSION - Khớp với ConnectDB.py trả về (conn, cursor)

from backend.Config.ConnectDB import connect_to_database
from datetime import datetime

class PendingMessageService:
    """Quản lý tin nhắn chờ xử lý khi người nhận chưa đăng nhập"""
    
    @staticmethod
    def save_pending_message(sender_id, receiver_id, conversation_id, plain_text):
        """
        Lưu tin nhắn vào hàng đợi
        Returns: pending_id (int) hoặc None nếu lỗi
        """
        try:
            # ConnectDB trả về (conn, cursor)
            conn, cursor = connect_to_database()
            
            query = """
                INSERT INTO pending_messages 
                (sender_id, receiver_id, conversation_id, plain_text, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """
            
            cursor.execute(query, (sender_id, receiver_id, conversation_id, plain_text))
            conn.commit()
            
            pending_id = cursor.lastrowid
            
            cursor.close()
            conn.close()
            
            print(f" Message {pending_id} queued for user {receiver_id} (not logged in yet)")
            return pending_id
            
        except Exception as e:
            print(f" Error saving pending message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_pending_messages(receiver_id):
        """
        Lấy tất cả tin nhắn chờ của một user
        Returns: list of dict
        """
        try:
            # ConnectDB trả về (conn, cursor) với dictionary=True
            conn, cursor = connect_to_database()
            
            query = """
                SELECT id, sender_id, conversation_id, plain_text, created_at
                FROM pending_messages
                WHERE receiver_id = %s
                ORDER BY created_at ASC
            """
            
            cursor.execute(query, (receiver_id,))
            messages = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return messages
            
        except Exception as e:
            print(f" Error fetching pending messages: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_pending_count(receiver_id):
        """
        Đếm số lượng pending messages của user
        Returns: int
        """
        try:
            conn, cursor = connect_to_database()
            
            query = "SELECT COUNT(*) as count FROM pending_messages WHERE receiver_id = %s"
            cursor.execute(query, (receiver_id,))
            
            result = cursor.fetchone()
            count = result['count'] if result else 0
            
            cursor.close()
            conn.close()
            
            return count
            
        except Exception as e:
            print(f" Error counting pending messages: {e}")
            return 0
    
    @staticmethod
    def delete_pending_messages(receiver_id):
        """
        Xóa tất cả pending messages sau khi đã xử lý
        Returns: số lượng messages đã xóa
        """
        try:
            conn, cursor = connect_to_database()
            
            query = "DELETE FROM pending_messages WHERE receiver_id = %s"
            cursor.execute(query, (receiver_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                print(f"  Deleted {deleted_count} pending messages for user {receiver_id}")
            
            return deleted_count
            
        except Exception as e:
            print(f" Error deleting pending messages: {e}")
            return 0
    
    @staticmethod
    def delete_single_pending(pending_id):
        """
        Xóa một pending message cụ thể
        Returns: bool (success)
        """
        try:
            conn, cursor = connect_to_database()
            
            query = "DELETE FROM pending_messages WHERE id = %s"
            cursor.execute(query, (pending_id,))
            
            conn.commit()
            success = cursor.rowcount > 0
            
            cursor.close()
            conn.close()
            
            return success
            
        except Exception as e:
            print(f" Error deleting pending message {pending_id}: {e}")
            return False