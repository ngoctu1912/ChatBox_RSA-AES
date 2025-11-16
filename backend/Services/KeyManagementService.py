import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from backend.Services.RSAService import RSAService
from backend.Services.SessionService import SessionService


class KeyManagementService:
    """
    Xử lý mã hóa/giải mã AES key bằng RSA và điều phối Key Exchange.
    """
    
    @staticmethod
    def encrypt_aes_key_for_user(aes_key: str, user_id: int):
        """
        Mã hóa AES key bằng RSA public key của user
        
        Args:
            aes_key: AES key (base64 string)
            user_id: ID của user nhận
            
        Returns:
            str: Encrypted AES key (base64 encoded) hoặc None
        """
        try:
            # Lấy public key của user
            public_key_pem = RSAService.get_public_key(user_id)
            if not public_key_pem:
                print(f"Public key not found for user {user_id}")
                return None
            
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Mã hóa AES key
            aes_key_bytes = aes_key.encode('utf-8')
            encrypted = public_key.encrypt(
                aes_key_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Encode to base64
            encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
            return encrypted_b64
            
        except Exception as e:
            print(f"Error encrypt_aes_key_for_user: {e}")
            return None
    
    @staticmethod
    def decrypt_aes_key(encrypted_aes_key: str, user_id: int):
        """
        Giải mã AES key bằng RSA private key của user
        
        Args:
            encrypted_aes_key: Encrypted AES key (base64 string)
            user_id: ID của user sở hữu private key
            
        Returns:
            str: Decrypted AES key (base64) hoặc None
        """
        try:
            # Lấy private key của user
            private_key_pem = RSAService.get_private_key(user_id)
            if not private_key_pem:
                print(f"Private key not found for user {user_id}")
                return None
            
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_aes_key)
            
            # Giải mã
            decrypted = private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            print(f"Error decrypt_aes_key: {e}")
            return None
    
    @staticmethod
    def accept_key_exchange(encrypted_aes_key: str, user_id: int, conversation_id: int):
        """
        Partner nhận và giải mã AES key
        
        Args:
            encrypted_aes_key: Encrypted AES key nhận được
            user_id: ID của partner
            conversation_id: ID conversation
            
        Returns:
            str: Decrypted AES key hoặc None
        """
        try:
            # Giải mã AES key
            aes_key = KeyManagementService.decrypt_aes_key(encrypted_aes_key, user_id)
            
            if aes_key:
                # BƯỚC CỐT LÕI: LƯU KEY AES PLAINTEXT VÀO SESSION SERVICE
                SessionService.save_key_after_exchange(conversation_id, aes_key)
                
                # Đánh dấu key exchange thành công (Nếu hàm này tồn tại)
                # SessionService.mark_key_exchanged(conversation_id) 
                return aes_key
            
            return None
            
        except Exception as e:
            print(f"Error accept_key_exchange: {e}")
            return None
    
    @staticmethod
    def rotate_session_key(conversation_id: int, initiator_user_id: int, partner_user_id: int):
        """
        Tạo lại AES key mới (key rotation)
        """
        try:
            # Xóa key cũ
            SessionService.delete_session_key(conversation_id)
            
            # Tạo key mới
            return KeyManagementService.initiate_key_exchange(
                conversation_id, 
                initiator_user_id, 
                partner_user_id
            )
            
        except Exception as e:
            print(f"Error rotate_session_key: {e}")
            return None
        
    @staticmethod
    def initiate_key_exchange(conversation_id: int, initiator_user_id: int, partner_user_id: int):
        """
        Khởi tạo key exchange:
        1. Tạo AES Key mới.
        2. Lưu AES Key PLAIN vào Session Service (Redis).
        3. Mã hóa AES Key bằng RSA Public Key của Partner.
        
        Returns:
            dict: Dữ liệu cần thiết để gửi cho Partner qua WebSocket, hoặc None nếu lỗi.
        """
        try:
            # 1. Tạo và Lưu AES Key (PLAIN) vào Session Service (Redis)
            aes_key_plain_b64 = SessionService.create_session_key(conversation_id, initiator_user_id)
            if not aes_key_plain_b64:
                return None
            
            # 2. Mã hóa AES Key bằng RSA Public Key của Partner
            encrypted_aes_key_b64 = KeyManagementService.encrypt_aes_key_for_user(
                aes_key=aes_key_plain_b64, 
                user_id=partner_user_id
            )
            
            if not encrypted_aes_key_b64:
                # Xóa key đã tạo trong Redis nếu mã hóa thất bại
                SessionService.delete_session_key(conversation_id)
                return None
            
            # 3. Trả về dữ liệu cần gửi qua WebSocket
            return {
                'conversation_id': conversation_id,
                'initiator_id': initiator_user_id,
                'partner_id': partner_user_id,
                'encrypted_aes_key': encrypted_aes_key_b64,
                'message': 'INITIATE_KEY_EXCHANGE' 
            }
            
        except Exception as e:
            print(f"Error initiate_key_exchange: {e}")
            return None