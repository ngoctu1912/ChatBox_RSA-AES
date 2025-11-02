from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from backend.Config.ConnectDB import connect_to_database


class RSAService:
    """
    Service xử lý các thao tác liên quan đến RSA:
    - Tạo cặp khóa RSA
    - Lưu khóa vào database
    - Lấy khóa công khai/riêng tư
    """

    @staticmethod
    def generate_rsa_keypair(key_size=2048):
        """
        Sinh cặp khóa RSA mới
        
        Args:
            key_size (int): Kích thước khóa (mặc định 2048 bit)
            
        Returns:
            tuple: (private_key_pem, public_key_pem) dưới dạng string
        """
        try:
            # Sinh private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size
            )
            
            # Lấy public key từ private key
            public_key = private_key.public_key()

            # Chuyển đổi private key sang PEM format
            pem_private = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')

            # Chuyển đổi public key sang PEM format
            pem_public = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

            return pem_private, pem_public
            
        except Exception as e:
            print(f"Error generating RSA keypair: {e}")
            return None, None

    @staticmethod
    def create_rsa_key_for_user(user_id, key_size=2048):
        """
        Sinh cặp khóa RSA và lưu vào database cho user
        
        Args:
            user_id (int): ID của user
            key_size (int): Kích thước khóa (mặc định 2048 bit)
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            # Sinh cặp khóa
            pem_private, pem_public = RSAService.generate_rsa_keypair(key_size)
            
            if not pem_private or not pem_public:
                print("Failed to generate keypair")
                return False

            # Lưu vào database
            conn, cursor = connect_to_database()
            query = """
                INSERT INTO rsa_keys (user_id, public_key, private_key_encrypted, key_size)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, pem_public, pem_private, key_size))
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"RSA keypair created successfully for user {user_id}")
            return True
            
        except Exception as e:
            print(f"Error create_rsa_key_for_user: {e}")
            return False

    @staticmethod
    def get_public_key(user_id):
        """
        Lấy khóa công khai RSA mới nhất của user
        
        Args:
            user_id (int): ID của user
            
        Returns:
            str: Public key ở dạng PEM, hoặc None nếu không tìm thấy
        """
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT public_key FROM rsa_keys 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result['public_key'] if result else None
            
        except Exception as e:
            print(f"Error get_public_key: {e}")
            return None

    @staticmethod
    def get_private_key(user_id):
        """
        Lấy khóa riêng tư RSA mới nhất của user
        
        Args:
            user_id (int): ID của user
            
        Returns:
            str: Private key ở dạng PEM, hoặc None nếu không tìm thấy
        """
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT private_key_encrypted FROM rsa_keys 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result['private_key_encrypted'] if result else None
            
        except Exception as e:
            print(f"Error get_private_key: {e}")
            return None

    @staticmethod
    def get_keypair(user_id):
        """
        Lấy cả cặp khóa (public + private) của user
        
        Args:
            user_id (int): ID của user
            
        Returns:
            dict: {"public_key": str, "private_key": str} hoặc None
        """
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT public_key, private_key_encrypted, key_size, created_at
                FROM rsa_keys 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return {
                    "public_key": result['public_key'],
                    "private_key": result['private_key_encrypted'],
                    "key_size": result['key_size'],
                    "created_at": result['created_at']
                }
            return None
            
        except Exception as e:
            print(f"Error get_keypair: {e}")
            return None

    @staticmethod
    def get_user_keys(current_user_id, partner_id):
        """
        Lấy cặp khóa RSA của cả 2 user để hiển thị hoặc sử dụng
        
        Args:
            current_user_id (int): ID của user hiện tại
            partner_id (int): ID của đối phương
            
        Returns:
            dict: {
                "my_public_key": str,
                "my_private_key": str,
                "partner_public_key": str
            } hoặc dict với các giá trị None nếu không tìm thấy
        """
        try:
            # Lấy khóa của user hiện tại
            my_keypair = RSAService.get_keypair(current_user_id)
            
            # Lấy khóa công khai của đối phương
            partner_public_key = RSAService.get_public_key(partner_id)
            
            return {
                "my_public_key": my_keypair["public_key"] if my_keypair else None,
                "my_private_key": my_keypair["private_key"] if my_keypair else None,
                "partner_public_key": partner_public_key,
                "my_key_size": my_keypair["key_size"] if my_keypair else None,
                "my_key_created_at": my_keypair["created_at"] if my_keypair else None
            }
            
        except Exception as e:
            print(f"Error get_user_keys: {e}")
            return {
                "my_public_key": None,
                "my_private_key": None,
                "partner_public_key": None,
                "my_key_size": None,
                "my_key_created_at": None
            }

    @staticmethod
    def delete_old_keys(user_id, keep_latest=1):
        """
        Xóa các khóa cũ, chỉ giữ lại N khóa mới nhất
        
        Args:
            user_id (int): ID của user
            keep_latest (int): Số lượng khóa mới nhất cần giữ lại
            
        Returns:
            bool: True nếu thành công
        """
        try:
            conn, cursor = connect_to_database()
            query = """
                DELETE FROM rsa_keys 
                WHERE user_id = %s 
                AND rsa_key_id NOT IN (
                    SELECT rsa_key_id FROM (
                        SELECT rsa_key_id FROM rsa_keys 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    ) as temp
                )
            """
            cursor.execute(query, (user_id, user_id, keep_latest))
            conn.commit()
            deleted_count = cursor.rowcount
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                print(f"Deleted {deleted_count} old keys for user {user_id}")
            
            return True
            
        except Exception as e:
            print(f"Error delete_old_keys: {e}")
            return False