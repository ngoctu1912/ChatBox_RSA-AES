import os
import base64
from datetime import datetime, timedelta
from backend.Utils.RedisClient import redis_client
from backend.Config.ConnectDB import connect_to_database


class SessionService:
    """
    Quản lý AES session keys cho mỗi conversation
    """
    
    # Session key hết hạn sau 24h
    SESSION_EXPIRY = 24 * 60 * 60  # seconds
    
    @staticmethod
    def generate_aes_key():
        """
        Sinh AES key 256-bit ngẫu nhiên
        Returns: str (base64 encoded)
        """
        try:
            aes_key = os.urandom(32)  # 256 bits
            return base64.b64encode(aes_key).decode('utf-8')
        except Exception as e:
            print(f"Error generating AES key: {e}")
            return None
    
    @staticmethod
    def create_session_key(conversation_id: int, initiator_user_id: int):
        """
        Tạo AES key mới cho conversation
        
        Args:
            conversation_id: ID của conversation
            initiator_user_id: User ID người khởi tạo
            
        Returns:
            str: AES key (base64 encoded)
        """
        try:
            # Generate AES key
            aes_key = SessionService.generate_aes_key()
            if not aes_key:
                return None
            
            # Lưu vào Redis với expiry
            session_data = {
                'aes_key': aes_key,
                'conversation_id': conversation_id,
                'initiator_user_id': initiator_user_id,
                'created_at': datetime.now().isoformat(),
                'key_exchanged': True  # Đánh dấu chưa exchange xong
            }
            
            redis_key = f"session:{conversation_id}"
            redis_client.set(redis_key, session_data, expire=SessionService.SESSION_EXPIRY)
            
            # Backup vào database
            conn, cursor = connect_to_database()
            query = """
                INSERT INTO session_keys 
                (conversation_id, aes_key_encrypted, created_by, expires_at)
                VALUES (%s, %s, %s, %s)
            """
            expires_at = datetime.now() + timedelta(seconds=SessionService.SESSION_EXPIRY)
            cursor.execute(query, (conversation_id, aes_key, initiator_user_id, expires_at))
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f" Session key created for conversation {conversation_id}")
            return aes_key
            
        except Exception as e:
            print(f"Error create_session_key: {e}")
            return None
    
    @staticmethod
    def get_session_key(conversation_id: int):
        """
        Lấy AES key của conversation
        
        Args:
            conversation_id: ID của conversation
            
        Returns:
            dict: Session data hoặc None
        """
        try:
            # Thử lấy từ Redis trước (nhanh hơn)
            redis_key = f"session:{conversation_id}"
            session_data = redis_client.get(redis_key)
            
            if session_data:
                return session_data
            
            # Nếu không có trong Redis, lấy từ DB
            conn, cursor = connect_to_database()
            query = """
                SELECT aes_key_encrypted, created_by, created_at, expires_at
                FROM session_keys
                WHERE conversation_id = %s 
                  AND expires_at > NOW()
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor.execute(query, (conversation_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                # Restore vào Redis
                session_data = {
                    'aes_key': result['aes_key_encrypted'],
                    'conversation_id': conversation_id,
                    'initiator_user_id': result['created_by'],
                    'created_at': result['created_at'].isoformat(),
                    'key_exchanged': True
                }
                redis_client.set(redis_key, session_data, expire=SessionService.SESSION_EXPIRY)
                return session_data
            
            return None
            
        except Exception as e:
            print(f"Error get_session_key: {e}")
            return None
    
    @staticmethod
    def mark_key_exchanged(conversation_id: int):
        """
        Đánh dấu key đã được exchange thành công
        """
        try:
            redis_key = f"session:{conversation_id}"
            session_data = redis_client.get(redis_key)
            if session_data:
                session_data['key_exchanged'] = True
                redis_client.set(redis_key, session_data, expire=SessionService.SESSION_EXPIRY)
                return True
            return False
        except Exception as e:
            print(f"Error mark_key_exchanged: {e}")
            return False
    
    @staticmethod
    def delete_session_key(conversation_id: int):
        """
        Xóa session key (khi user muốn reset key)
        """
        try:
            redis_key = f"session:{conversation_id}"
            redis_client.delete(redis_key)
            
            # Đánh dấu expired trong DB
            conn, cursor = connect_to_database()
            query = """
                UPDATE session_keys 
                SET expires_at = NOW()
                WHERE conversation_id = %s
            """
            cursor.execute(query, (conversation_id,))
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error delete_session_key: {e}")
            return False
    
    @staticmethod
    def is_key_exchanged(conversation_id: int):
        """
        Kiểm tra key đã được exchange chưa
        """
        try:
            session_data = SessionService.get_session_key(conversation_id)
            return session_data and session_data.get('key_exchanged', False)
        except Exception as e:
            print(f"Error is_key_exchanged: {e}")
            return False