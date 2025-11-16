from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from backend.Config.ConnectDB import connect_to_database
import base64


class RSAService:
    """
    Service xử lý các thao tác liên quan đến RSA:
    - Tạo cặp khóa RSA
    - Lưu khóa vào database
    - Lấy khóa công khai/riêng tư
    - MÃ HÓA và GIẢI MÃ Key AES (đã bổ sung)
    """

    @staticmethod
    def generate_rsa_keypair(key_size=2048):
        """
        Sinh cặp khóa RSA mới.
        
        Args:
            key_size (int): Kích thước khóa (mặc định 2048 bit)
            
        Returns:
            tuple: (private_key_pem, public_key_pem) dưới dạng string
        """
        try:
            # Sinh private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
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
        Sinh cặp khóa RSA và lưu vào database cho user.
        
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
        """Lấy Khóa Công khai RSA của user"""
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
        """Lấy Khóa Riêng tư RSA của user"""
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
        """Lấy cả cặp khóa (Công khai và Riêng tư)"""
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

    # ========================================
    # MÃ HÓA / GIẢI MÃ KEY AES BẰNG RSA (FIX)
    # ========================================
    @staticmethod
    def encrypt_aes_key(partner_id, aes_key_plain_b64):
        """
        Mã hóa AES Session Key (Base64) bằng Public Key RSA của đối tác.
        
        Args:
            partner_id (int): ID của đối tác
            aes_key_plain_b64 (str): AES Key plaintext ở dạng Base64
            
        Returns:
            str: AES Key đã mã hóa bằng RSA, hoặc None nếu lỗi
        """
        try:
            public_key_pem = RSAService.get_public_key(partner_id)
            if not public_key_pem:
                print(f"Error encrypt_aes_key: Partner {partner_id} public key not found.")
                return None
            
            # Tải Public Key từ PEM string
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Giải mã Base64 Key AES để lấy bytes
            aes_key_bytes = base64.b64decode(aes_key_plain_b64)

            # Mã hóa Key AES bằng Public Key RSA (dùng OAEP Padding)
            encrypted_aes_key = public_key.encrypt(
                aes_key_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Trả về Key đã mã hóa dưới dạng Base64
            return base64.b64encode(encrypted_aes_key).decode('utf-8')
            
        except Exception as e:
            print(f"Error encrypt_aes_key: {e}")
            return None

    @staticmethod
    def decrypt_aes_key(user_id, encrypted_aes_key_b64):
        """
        Giải mã AES Session Key (Base64) bằng Private Key RSA của user hiện tại.
        
        Args:
            user_id (int): ID của user hiện tại
            encrypted_aes_key_b64 (str): AES Key đã mã hóa bằng RSA ở dạng Base64
            
        Returns:
            str: AES Key plaintext Base64, hoặc None nếu thất bại
        """
        try:
            private_key_pem = RSAService.get_private_key(user_id)
            if not private_key_pem:
                print(f"Error decrypt_aes_key: Private key not found for user {user_id}.")
                return None
            
            # Tải Private Key (Private Key được lưu dưới dạng PEM string)
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            
            # Giải mã Base64 Key AES đã mã hóa
            encrypted_aes_key_bytes = base64.b64decode(encrypted_aes_key_b64)

            # Giải mã Key AES bằng Private Key RSA
            decrypted_aes_key_bytes = private_key.decrypt(
                encrypted_aes_key_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Trả về Key đã giải mã dưới dạng Base64
            return base64.b64encode(decrypted_aes_key_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"Error decrypt_aes_key: {e}")
            return None


    @staticmethod
    def get_user_keys(current_user_id, partner_id):
        """Lấy tất cả các khóa cần thiết cho việc hiển thị/trao đổi"""
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
        
   
    
    @staticmethod
    def ensure_keypair_exists_or_create(user_id: int):
        """
        Kiểm tra xem user đã có khóa RSA hợp lệ chưa. Nếu chưa có, tạo mới và lưu.
        Returns: bool (True nếu có khóa hoặc tạo thành công, False nếu lỗi)
        """
        try:
            # Kiểm tra sự tồn tại của Public Key
            existing_key = RSAService.get_public_key(user_id) 
            
            # NẾU ĐÃ CÓ KHÓA → RETURN TRUE
            if existing_key:
                print(f" RSA keypair already exists for user {user_id}")
                return True
            
            #  CHƯA CÓ KHÓA → TẠO MỚI
            print(f" RSA keypair not found for user {user_id}. Creating new keypair...")
            success = RSAService.create_rsa_key_for_user(user_id)
            
            if success:
                print(f" RSA keypair created successfully for user {user_id}.")
                return True
            else:
                print(f" Failed to create RSA keypair for user {user_id}.")
                return False
                
        except Exception as e:
            print(f" Critical error in ensure_keypair_exists_or_create: {e}")
            import traceback
            traceback.print_exc()
            return False